"""Correo de bienvenida para los clientes que se crean desde el maestro.

El maestro no envía correos: se lo pide al sitio de CyberShop (el tenant primario,
que ya envía los de la prueba gratis y la compra en línea con su Gmail), por la red
interna y con el secreto compartido INTERNAL_API_KEY. El correo lleva la tienda, el
panel, el usuario y la contraseña temporal; la contraseña nunca se guarda ni se
escribe en el log.
"""

import json
import os
import urllib.error
import urllib.request

from config import Config
from db import control_plane_cursor

RUTA = '/internal/api/v1/correo-bienvenida'
ESPERA_SEGUNDOS = 25


def url_operador():
    """Dirección interna del sitio de CyberShop: OPERADOR_INTERNAL_URL o el puerto
    del tenant primario en la red local. '' si no se sabe."""
    fija = (os.getenv('OPERADOR_INTERNAL_URL') or '').strip().rstrip('/')
    if fija:
        return fija
    try:
        with control_plane_cursor(dict_cursor=True) as cur:
            cur.execute("""SELECT r.port FROM tenants t JOIN tenant_runtime r ON r.tenant_id = t.id
                           WHERE t.slug = %s LIMIT 1""", (Config.PRIMARY_TENANT_SLUG,))
            fila = cur.fetchone()
    except Exception:  # noqa: BLE001
        return ''
    return f"http://127.0.0.1:{fila['port']}" if fila and fila.get('port') else ''


def enviar(resultado, admin_nombre=''):
    """Pide enviar la bienvenida del cliente recién creado. (enviado, motivo si no)."""
    clave = (getattr(Config, 'INTERNAL_API_KEY', '') or '').strip()
    base = url_operador()
    if not clave or not base:
        return False, 'falta la configuración interna (INTERNAL_API_KEY o el puerto del sitio principal)'
    dominio = resultado.get('domain') or (f"{resultado.get('slug')}.{Config.BASE_DOMAIN}"
                                          if resultado.get('slug') else '')
    datos = {
        'admin_email': resultado.get('admin_email') or '',
        'admin_nombre': admin_nombre or '',
        'admin_password': resultado.get('admin_password') or '',
        'dominio': dominio,
        'plan': resultado.get('plan') or '',
        'client_code': resultado.get('client_code') or '',
    }
    peticion = urllib.request.Request(
        base + RUTA, data=json.dumps(datos).encode('utf-8'), method='POST',
        headers={'Content-Type': 'application/json', 'X-Internal-Key': clave})
    try:
        with urllib.request.urlopen(peticion, timeout=ESPERA_SEGUNDOS) as respuesta:
            cuerpo = json.loads(respuesta.read().decode('utf-8') or '{}')
        return (True, '') if cuerpo.get('ok') else (False, 'el correo no salió')
    except urllib.error.HTTPError as exc:
        return False, f'el sitio principal respondió {exc.code}'
    except Exception as exc:  # noqa: BLE001 — red, tiempo de espera, JSON
        return False, f'no se pudo contactar el sitio principal ({type(exc).__name__})'
