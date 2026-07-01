"""Auto-servicio para que el operador autorice su propia IP en el allow-list.

Vive FUERA del filtro de IP: nginx expone `/autorizar-ip` con HTTP Basic Auth
(contraseña propia) para que el operador pueda recuperar acceso al panel aunque
su IP dinámica haya cambiado. Por seguridad SOLO autoriza la IP de ORIGEN de la
petición (nunca una arbitraria) y mantiene como máximo MAX_IPS entradas para no
acumular IPs viejas indefinidamente.
"""

import ipaddress
import subprocess
from pathlib import Path

from flask import Blueprint, request

bp = Blueprint('ip_self', __name__)

ALLOW_FILE = Path('/etc/nginx/cybershop-allow/dynamic.conf')
MAX_IPS = 5
SUDO = '/usr/bin/sudo'
NGINX = '/usr/sbin/nginx'
SYSTEMCTL = '/usr/bin/systemctl'


def _client_ip() -> str:
    """IP real del cliente (nginx la pasa en X-Real-IP = $remote_addr)."""
    ip = (request.headers.get('X-Real-IP')
          or request.headers.get('X-Forwarded-For', '').split(',')[0]
          or request.remote_addr or '')
    return ip.strip()


def _valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _read_ips() -> list:
    if not ALLOW_FILE.exists():
        return []
    ips = []
    for line in ALLOW_FILE.read_text().splitlines():
        s = line.strip()
        if s.startswith('allow ') and s.endswith(';'):
            ips.append(s[len('allow '):-1].strip())
    return ips


def _write_ips(ips: list) -> None:
    out = ["# Generado por /autorizar-ip — IPs dinámicas del operador.",
           f"# Se actualiza solo; máximo {MAX_IPS} IPs (las más recientes).", ""]
    out += [f"allow {ip};" for ip in ips]
    ALLOW_FILE.write_text("\n".join(out) + "\n")


_PAGE = """<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Autorizar IP · CyberShop</title><style>
body{font-family:system-ui,-apple-system,sans-serif;background:#0e1b33;color:#fff;
display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}
.card{background:#122c94;padding:2rem;border-radius:16px;max-width:440px;width:90%;
box-shadow:0 12px 48px rgba(0,0,0,.45)}h1{font-size:1.35rem;margin:0 0 1rem}
code{background:#0e1b33;padding:3px 10px;border-radius:6px;font-size:1.05rem}
button{background:#fb8500;color:#0e1b33;border:0;padding:.8rem 1.2rem;border-radius:10px;
font-weight:800;font-size:1rem;cursor:pointer;width:100%;margin-top:1.2rem}
a{color:#fb8500;font-weight:700}.ok{color:#28d17c}.err{color:#ff6b6b}
.muted{color:#a9b4d0;font-size:.85rem;margin-top:1.1rem;line-height:1.4}
</style></head><body><div class=card>__BODY__</div></body></html>"""


def _render(body: str) -> str:
    return _PAGE.replace('__BODY__', body)


@bp.route('/autorizar-ip', methods=['GET'])
def autorizar_form():
    ip = _client_ip()
    ya = ip in _read_ips()
    body = ("<h1>Autorizar mi acceso al panel</h1>"
            "<p>Tu IP pública detectada:</p>"
            f"<p><code>{ip or 'desconocida'}</code></p>")
    if ya:
        body += "<p class=ok>✓ Esta IP ya está autorizada.</p>"
    body += ("<form method=post><button type=submit>Autorizar esta IP</button></form>"
             "<p class=muted>Se agrega al filtro del panel y podrás entrar en "
             "admin.cybershopcol.com. Solo se autoriza la IP desde la que estás "
             "conectada ahora.</p>")
    return _render(body)


@bp.route('/autorizar-ip', methods=['POST'])
def autorizar_do():
    ip = _client_ip()
    if not _valid_ip(ip):
        return _render(f"<h1 class=err>Error</h1><p>No se pudo determinar una IP "
                       f"válida (<code>{ip or '—'}</code>).</p>"), 400
    ips = _read_ips()
    if ip in ips:
        ips.remove(ip)
    ips.insert(0, ip)          # la más reciente primero
    ips = ips[:MAX_IPS]        # cap: no acumular IPs viejas
    try:
        _write_ips(ips)
        t = subprocess.run([SUDO, NGINX, '-t'], capture_output=True, text=True, timeout=30)
        if t.returncode != 0:
            return _render("<h1 class=err>Error</h1><p>La configuración de nginx no "
                           "validó; no se aplicó el cambio.</p>"), 500
        subprocess.run([SUDO, SYSTEMCTL, 'reload', 'nginx'],
                       capture_output=True, text=True, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return _render(f"<h1 class=err>Error</h1><p>{exc}</p>"), 500
    body = ("<h1 class=ok>✓ IP autorizada</h1>"
            f"<p><code>{ip}</code> ya tiene acceso al panel.</p>"
            "<p><a href='https://admin.cybershopcol.com/'>Ir al panel →</a></p>"
            f"<p class=muted>IPs autorizadas ({len(ips)}/{MAX_IPS}): {', '.join(ips)}</p>")
    return _render(body)
