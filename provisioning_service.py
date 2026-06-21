"""Aprovisionamiento de la instancia de cada cliente.

Modelo: una instancia por cliente, mismo servidor, puerto distinto, dominio
propio (reverse proxy Caddy: dominio -> 127.0.0.1:puerto). Código compartido
en APP_DIR; cada instancia se diferencia por su EnvironmentFile
(<INSTANCE_ENV_DIR>/<slug>.env), que SOBREESCRIBE el .cybershop.conf compartido
(el app usa load_dotenv override=False -> el entorno gana).

En Windows (dev) solo se hace lo testeable: asignar puerto, escribir el env y
registrar tenant_runtime. Los pasos de systemd/Caddy se ejecutan SOLO en Linux.
"""

import os
import secrets
import subprocess
import threading

from config import Config
from db import control_plane_cursor
import integrations_service as ints
import proxy_service


IS_LINUX = (os.name == 'posix')
# Ruta absoluta: el servicio del maestro corre con PATH restringido al venv
# (sin /usr/bin), por lo que 'sudo'/'systemctl' a secas no se resuelven.
SUDO = ['/usr/bin/sudo'] if IS_LINUX else []   # www-data corre systemctl con sudo (NOPASSWD acotado)
SYSTEMCTL = '/usr/bin/systemctl'


# ── Tabla runtime (defensivo) ──────────────────────────────────
def _ensure_runtime_table():
    with control_plane_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_runtime (
                tenant_id INT PRIMARY KEY REFERENCES tenants(id),
                port INT UNIQUE, subdomain TEXT UNIQUE, custom_domain TEXT UNIQUE,
                instance_status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


# ── Puertos ────────────────────────────────────────────────────
def _port_in_use(port: int) -> bool:
    try:
        out = subprocess.run(['ss', '-tlnH', f'sport = :{port}'],
                             capture_output=True, text=True, timeout=10).stdout
        return bool(out.strip())
    except Exception:
        return False


def allocate_port(tenant_id: int) -> int:
    _ensure_runtime_table()
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT port FROM tenant_runtime WHERE tenant_id = %s", (tenant_id,))
        row = cur.fetchone()
        if row and row['port']:
            return row['port']
        cur.execute("SELECT port FROM tenant_runtime WHERE port IS NOT NULL")
        used = {r['port'] for r in cur.fetchall()}
    for p in range(Config.PORT_MIN, Config.PORT_MAX + 1):
        if p in used:
            continue
        if IS_LINUX and _port_in_use(p):
            continue
        return p
    raise RuntimeError("No hay puertos libres en el rango configurado.")


def register_runtime(tenant_id, port, subdomain, custom_domain=None, status='pending'):
    _ensure_runtime_table()
    with control_plane_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenant_runtime (tenant_id, port, subdomain, custom_domain, instance_status, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (tenant_id) DO UPDATE SET
                port = EXCLUDED.port, subdomain = EXCLUDED.subdomain,
                custom_domain = EXCLUDED.custom_domain,
                instance_status = EXCLUDED.instance_status, updated_at = NOW()
            """,
            (tenant_id, port, subdomain, custom_domain, status),
        )


def set_status(tenant_id, status):
    _ensure_runtime_table()
    with control_plane_cursor() as cur:
        cur.execute(
            "UPDATE tenant_runtime SET instance_status = %s, updated_at = NOW() WHERE tenant_id = %s",
            (status, tenant_id),
        )


def get_runtime(tenant_id):
    _ensure_runtime_table()
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT * FROM tenant_runtime WHERE tenant_id = %s", (tenant_id,))
        return cur.fetchone()


# ── Overrides de interfaz por instancia (theme a medida del sitio público) ────
# Carpeta FUERA del repo compartido (/var/www/CyberShop); `git pull` nunca la
# toca. Si existe `<root>/<slug>/templates|static`, la app del cliente pisa con
# ellos las plantillas/estáticos compartidos SOLO para ese cliente.
OVERRIDES_ROOT = os.getenv('INSTANCE_OVERRIDES_ROOT', '/var/www/cybershop-overrides')


def ensure_overrides_dir(slug):
    """Crea (idempotente) la carpeta de overrides del cliente con `templates/` y
    `static/`. Devuelve la ruta. Solo crea en Linux (prod); en dev solo calcula."""
    d = os.path.join(OVERRIDES_ROOT, slug)
    if IS_LINUX:
        for sub in ('templates', 'static'):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


# ── EnvironmentFile por instancia ──────────────────────────────
def write_instance_env(slug, db_name, port, tenant_id):
    """Escribe los overrides de runtime, preservando integraciones y secreto."""
    env = ints.read_env(slug)
    env['PORT'] = str(port)
    env['DB_NAME'] = db_name
    env['DEFAULT_TENANT_ID'] = str(tenant_id)
    env['DEFAULT_TENANT_SLUG'] = slug
    env['CYBERSHOP_API_ENABLED'] = '1'
    env['INSTANCE_OVERRIDES_DIR'] = ensure_overrides_dir(slug)
    env.setdefault('FLASK_SECRET_KEY', secrets.token_hex(32))
    ints._write_env(slug, env)


def domain_for(subdomain: str) -> str:
    return f"{subdomain}.{Config.BASE_DOMAIN}"


# ── systemd + Caddy (solo Linux) ───────────────────────────────
def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def enable_service(slug):
    if not IS_LINUX:
        return 'skipped (no-linux)'
    _run(SUDO + [SYSTEMCTL, 'enable', f'cybershop@{slug}'])
    _run(SUDO + [SYSTEMCTL, 'start', f'cybershop@{slug}'])
    return 'enabled'


def service_unit(slug):
    """Unidad systemd de la instancia. El tenant primario (sitio principal) corre
    en el servicio `cybershop`; el resto en la plantilla `cybershop@<slug>`."""
    if slug == Config.PRIMARY_TENANT_SLUG:
        return 'cybershop'
    return f'cybershop@{slug}'


def restart_service(slug):
    if not IS_LINUX:
        return 'skipped (no-linux)'
    _run(SUDO + [SYSTEMCTL, 'restart', service_unit(slug)])
    return 'restarted'


def stop_service(slug):
    if not IS_LINUX:
        return 'skipped (no-linux)'
    _run(SUDO + [SYSTEMCTL, 'stop', f'cybershop@{slug}'])
    # disable: un cliente suspendido NO debe auto-arrancar tras un reboot
    _run(SUDO + [SYSTEMCTL, 'disable', f'cybershop@{slug}'])
    return 'stopped'


# Proxy (nginx por defecto, o Caddy) delegado a proxy_service.
def write_site(domain, port, is_subdomain=True):
    return proxy_service.write_site(domain, port, is_subdomain=is_subdomain)


def remove_site(domain):
    return proxy_service.remove_site(domain)


def _issue_ssl_bg(domains):
    """Emite certificados en segundo plano (no bloquea la creación)."""
    for dom in domains:
        try:
            proxy_service.issue_ssl(dom)
        except Exception:
            pass


def issue_ssl_async(domains):
    """Lanza la emisión de SSL en un hilo daemon. Devuelve de inmediato.

    certbot puede tardar decenas de segundos (DNS / Let's Encrypt) y, si corre
    dentro del request de crear cliente, supera el proxy_read_timeout del nginx
    del maestro (60s) → el operador ve un 504 aunque el cliente sí se creó.
    El sitio queda accesible por HTTP al instante y pasa a HTTPS cuando el cert
    quede listo (reintentable con "Reaprovisionar").
    """
    doms = [d for d in (domains or []) if d]
    if not doms:
        return
    threading.Thread(target=_issue_ssl_bg, args=(doms,), daemon=True).start()


# ── Orquestador ────────────────────────────────────────────────
def provision(tenant_id, slug, db_name, subdomain=None, custom_domain=None):
    """Asigna puerto, escribe env, registra runtime y (en Linux) levanta la
    instancia + el proxy (nginx/Caddy). Valida el dominio (seguridad).
    Devuelve {port, domain, custom_domain, instance_status}."""
    subdomain = proxy_service.validate_subdomain(subdomain or slug)
    custom_domain = proxy_service.validate_domain(custom_domain) if custom_domain else None
    port = allocate_port(tenant_id)
    write_instance_env(slug, db_name, port, tenant_id)

    status = 'pending'
    ssl_msgs = []
    if IS_LINUX:
        enable_service(slug)
        write_site(domain_for(subdomain), port, is_subdomain=True)
        if custom_domain:
            write_site(custom_domain, port, is_subdomain=False)
        status = 'running'
        # SSL en SEGUNDO PLANO: no bloquea el request de creación (evita el 504
        # del nginx del maestro). El sitio sirve por HTTP de inmediato y pasa a
        # HTTPS cuando certbot termina. Ver issue_ssl_async().
        doms = list({domain_for(subdomain), custom_domain} - {None})
        issue_ssl_async(doms)
        ssl_msgs.append('ssl: emitiéndose en segundo plano (%s)' % ', '.join(doms))

    register_runtime(tenant_id, port, subdomain, custom_domain, status=status)
    return {
        'port': port,
        'domain': domain_for(subdomain),
        'custom_domain': custom_domain,
        'instance_status': status,
        'ssl': ' | '.join(ssl_msgs) if ssl_msgs else None,
    }
