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


# ── Despliegue de código compartido con GATE de "cambios públicos" ────────────
# El panel corre como www-data (sin permiso de git). Un script root
# (/usr/local/bin/cybershop-deploy-code.sh, NOPASSWD acotado) expone 2 subcomandos:
#   changes -> lista los archivos que cambiarían respecto a origin/master (no muta)
#   apply   -> git merge --ff-only origin/master (nunca hace merge ni pisa locales)
# El código es COMPARTIDO por todas las instancias; cada cliente carga el nuevo
# código al reiniciar su instancia. Las mejoras del app (después del login) y de
# seguridad/backend fluyen; los cambios del SITIO PÚBLICO (antes del login) se
# BLOQUEAN salvo include_public=True, para no soltarlos a los clientes sin querer.
DEPLOY_SCRIPT = '/usr/local/bin/cybershop-deploy-code.sh'

# Presentación del sitio PÚBLICO (antes del login). Único punto a mantener.
# NO se incluye el backend/servicios ni el CSS compartido (variables.css,
# layout.css, layout.js): eso fluye siempre (p. ej. parches de seguridad).
PUBLIC_PATHS = (
    'app/templates/plantillaindex.html', 'app/templates/plantillaindexError.html',
    'app/templates/tienda_suspendida.html',
    'app/templates/index.html', 'app/templates/productos.html',
    'app/templates/producto_detalle.html', 'app/templates/servicios.html',
    'app/templates/carrito.html', 'app/templates/metodos_pago.html',
    'app/templates/respuesta_pago.html', 'app/templates/redireccion_payu.html',
    'app/templates/software.html', 'app/templates/descargar.html',
    'app/templates/comprar_plan.html', 'app/templates/activar_tienda.html',
    'app/templates/renovar_plan.html', 'app/templates/login.html',
    'app/templates/registrarcliente.html', 'app/templates/lista_deseos.html',
    'app/templates/404.html',
    'app/templates/share/publico_',          # prefijo: publico_carpeta/clave/vencido
    'app/static/css/index.css', 'app/static/css/Productos.css',
    'app/static/css/ProductoDetalle.css', 'app/static/css/carrito.css',
    'app/static/css/error404.css', 'app/static/css/respuesta _pago.css',
    'app/static/js/Shoppingcar.js',
)


def _is_public_path(path):
    p = (path or '').strip()
    for pat in PUBLIC_PATHS:
        if pat.endswith('_'):                # patrón de prefijo (share/publico_*)
            if p.startswith(pat):
                return True
        elif p == pat:
            return True
    return False


def _run_deploy(subcmd):
    r = subprocess.run(SUDO + ['-n', DEPLOY_SCRIPT, subcmd],
                       capture_output=True, text=True, timeout=120)
    out = ((r.stdout or '') + (r.stderr or '')).strip()
    return r.returncode, out


def deploy_code(include_public=False):
    """Trae el código compartido desde GitHub con GATE de cambios públicos.
    Devuelve (status, msg) con status ∈ {'updated','uptodate','blocked','error'}.
    En dev (no-linux) es no-op ('uptodate')."""
    if not IS_LINUX:
        return 'uptodate', 'deploy de código omitido (dev)'
    try:
        rc, out = _run_deploy('changes')
    except Exception as exc:  # noqa: BLE001
        return 'error', f'no se pudo consultar cambios: {exc}'
    if rc != 0:
        return 'error', f'error consultando cambios: {out}'
    changed = [ln for ln in out.splitlines() if ln.strip()]
    if not changed:
        return 'uptodate', 'ya al día (sin cambios)'
    public_changed = [f for f in changed if _is_public_path(f)]
    if public_changed and not include_public:
        muestra = ', '.join(public_changed[:6]) + ('…' if len(public_changed) > 6 else '')
        return 'blocked', (f'{len(changed)} cambio(s) incluyen el SITIO PÚBLICO '
                           f'({muestra}). Si son intencionales, usa "Deploy completo".')
    try:
        rc2, out2 = _run_deploy('apply')
    except Exception as exc:  # noqa: BLE001
        return 'error', f'no se pudo aplicar el deploy: {exc}'
    if rc2 != 0:
        return 'error', f'error aplicando ({out2})'
    nota = f' (incluyó {len(public_changed)} público)' if public_changed else ''
    return 'updated', f'actualizado a {out2}: {len(changed)} archivo(s){nota}'


def service_unit(slug):
    """Unidad systemd de la instancia. El tenant primario (sitio principal) corre
    en el servicio `cybershop`; el resto en la plantilla `cybershop@<slug>`."""
    if slug == Config.PRIMARY_TENANT_SLUG:
        return 'cybershop'
    return f'cybershop@{slug}'


def enable_service(slug):
    if not IS_LINUX:
        return 'skipped (no-linux)'
    # Usar service_unit(): para el primario es `cybershop` (NO la plantilla
    # `cybershop@cyber-t001`, cuyo env no tiene PORT → crash-loop perpetuo).
    unit = service_unit(slug)
    _run(SUDO + [SYSTEMCTL, 'enable', unit])
    _run(SUDO + [SYSTEMCTL, 'start', unit])
    return 'enabled'


def restart_service(slug):
    if not IS_LINUX:
        return 'skipped (no-linux)'
    _run(SUDO + [SYSTEMCTL, 'restart', service_unit(slug)])
    return 'restarted'


def stop_service(slug):
    if not IS_LINUX:
        return 'skipped (no-linux)'
    unit = service_unit(slug)
    _run(SUDO + [SYSTEMCTL, 'stop', unit])
    # disable: un cliente suspendido NO debe auto-arrancar tras un reboot
    _run(SUDO + [SYSTEMCTL, 'disable', unit])
    return 'stopped'


def repair_primary_unit():
    """Limpia el unit templated fantasma del tenant primario.

    El primario corre como `cybershop.service`. Si por un reaprovisionamiento
    viejo quedó habilitado/arrancado `cybershop@<PRIMARY>` (cuyo env no tiene
    PORT), systemd lo reinicia en bucle indefinidamente. Esto lo detiene y
    deshabilita SIN tocar el servicio real `cybershop`. Idempotente."""
    if not IS_LINUX:
        return 'skipped (no-linux)'
    ghost = f'cybershop@{Config.PRIMARY_TENANT_SLUG}'
    _run(SUDO + [SYSTEMCTL, 'stop', ghost])
    _run(SUDO + [SYSTEMCTL, 'disable', ghost])
    # reset-failed es cosmético (limpia el contador de fallos); si la regla
    # sudoers no lo permite, stop+disable ya frenan el bucle.
    _run(SUDO + [SYSTEMCTL, 'reset-failed', ghost])
    return f'unit fantasma {ghost} detenido y deshabilitado'


def service_is_active(slug) -> bool:
    """True si la unidad systemd de la instancia está 'active'. No requiere sudo
    (is-active es consulta no privilegiada)."""
    if not IS_LINUX:
        return False
    r = _run([SYSTEMCTL, 'is-active', service_unit(slug)])
    return (r.stdout or '').strip() == 'active'


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
    # El tenant primario se gestiona como `cybershop.service` (puerto fijo, env y
    # nginx propios). Reaprovisionarlo por la plantilla `cybershop@<slug>` le
    # escribiría un env sin sentido y lo dejaría en crash-loop. No-op seguro.
    if slug == Config.PRIMARY_TENANT_SLUG:
        rt = get_runtime(tenant_id) or {}
        return {
            'port': rt.get('port'),
            'domain': Config.BASE_DOMAIN,
            'custom_domain': rt.get('custom_domain'),
            'instance_status': 'running' if IS_LINUX else 'pending',
            'ssl': 'gestionado aparte (sitio principal cybershop.service)',
        }

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
