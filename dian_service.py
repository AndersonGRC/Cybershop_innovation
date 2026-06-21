"""Puente con el microservicio FacturacionDIAN (facturación electrónica).

Cadena completa para que "todo hable con todo":
  1. El operador activa el módulo `facturacion_electronica` (module_service →
     cliente_config del tenant) — eso es lo que `facturacion_habilitada()` lee
     en la app del cliente.
  2. Este servicio provisiona el tenant en FacturacionDIAN
     (POST /api/v1/admin/tenants con X-Master-Key) y escribe las credenciales
     en el EnvironmentFile de la instancia: DIAN_SERVICE_URL, DIAN_API_KEY,
     DIAN_MASTER_KEY (SSO HMAC del panel DIAN) y DIAN_UI_URL.
  3. La instancia del cliente se reinicia para tomar el env →
     routes/factura_electronica.py de la app ya puede emitir.

Sin dependencias nuevas: usa urllib de la stdlib.
"""

import json
import urllib.error
import urllib.request

from config import Config
import integrations_service as ints

ENV_KEYS = ('DIAN_SERVICE_URL', 'DIAN_API_KEY', 'DIAN_MASTER_KEY', 'DIAN_UI_URL')
_UUID_CERO = '00000000-0000-0000-0000-000000000000'
AMBIENTES = ('habilitacion', 'produccion')


class DianError(Exception):
    """Error operativo hablando con el servicio DIAN (mensaje apto para flash)."""


def is_configured() -> bool:
    return bool(Config.DIAN_MASTER_KEY)


def _api() -> str:
    return (Config.DIAN_SERVICE_URL or '').rstrip('/')


def _root() -> str:
    """URL raíz del servicio (sin /api/v1) — donde vive /health."""
    api = _api()
    return api[: -len('/api/v1')] if api.endswith('/api/v1') else api


def _request(method: str, url: str, headers: dict | None = None,
             payload: dict | None = None, timeout: int = 8):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8') or '{}'
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode('utf-8') or '{}')
        except (ValueError, OSError):
            body = {}
        return exc.code, body
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise DianError(f"No se pudo contactar el servicio DIAN en {url}: {exc}") from exc


def calcular_dv(nit: str) -> int:
    """Dígito de verificación de un NIT (algoritmo oficial DIAN)."""
    pesos = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)
    digitos = ''.join(ch for ch in str(nit) if ch.isdigit())
    if not digitos:
        raise DianError('NIT inválido: no contiene dígitos.')
    total = sum(int(d) * pesos[i] for i, d in enumerate(reversed(digitos)))
    resto = total % 11
    return resto if resto < 2 else 11 - resto


def service_alive(timeout: int = 3) -> bool:
    try:
        status, _ = _request('GET', f"{_root()}/health", timeout=timeout)
        return status == 200
    except DianError:
        return False


def buscar_tenant_por_nit(nit: str) -> dict | None:
    """Busca el tenant en el servicio DIAN por NIT (vía listado admin)."""
    status, body = _request(
        'GET', f"{_api()}/admin/tenants",
        headers={'X-Master-Key': Config.DIAN_MASTER_KEY},
    )
    if status != 200 or not isinstance(body, list):
        return None
    nit = ''.join(ch for ch in str(nit) if ch.isdigit())
    return next((t for t in body if str(t.get('nit')) == nit), None)


def get_status(slug: str) -> dict:
    """Estado local (sin red) para pintar el panel: master key + env del cliente."""
    env = ints.read_env(slug)
    return {
        'master_configured': is_configured(),
        'service_url': _api(),
        'env': {k: bool(env.get(k)) for k in ENV_KEYS},
        'env_ok': bool(env.get('DIAN_SERVICE_URL') and env.get('DIAN_API_KEY')),
    }


def validate(slug: str) -> list:
    """Valida la cadena con red: devuelve [(ok: bool, mensaje: str), ...]."""
    checks = []
    checks.append((is_configured(),
                   'DIAN_MASTER_KEY configurada en el maestro (.cybershop.conf)'))
    alive = service_alive()
    checks.append((alive, f"Servicio DIAN alcanzable ({_root()}/health)"))
    env = ints.read_env(slug)
    for key in ('DIAN_SERVICE_URL', 'DIAN_API_KEY', 'DIAN_MASTER_KEY'):
        checks.append((bool(env.get(key)), f"{key} presente en el env de la instancia"))
    if alive and env.get('DIAN_API_KEY'):
        # Una factura inexistente con API key válida da 404; key inválida da 403.
        status, _ = _request(
            'GET', f"{env.get('DIAN_SERVICE_URL', _api()).rstrip('/')}/facturas/{_UUID_CERO}/estado",
            headers={'X-API-Key': env['DIAN_API_KEY']}, timeout=5,
        )
        checks.append((status == 404,
                       'API key del cliente aceptada por el servicio DIAN'
                       if status == 404 else
                       f"API key del cliente rechazada por el servicio (HTTP {status})"))
    return checks


def provision(slug: str, nombre: str, nit: str, razon_social: str,
              dv=None, ambiente: str = 'habilitacion', prefijo: str = '') -> dict:
    """Crea el tenant en FacturacionDIAN y escribe las credenciales en su env.

    La API key se retorna UNA sola vez por el servicio; aquí queda persistida
    de inmediato en el EnvironmentFile de la instancia del cliente.
    """
    if not is_configured():
        raise DianError('DIAN_MASTER_KEY no está configurada en el maestro '
                        '(.cybershop.conf). Sin ella no se puede provisionar.')
    nit = ''.join(ch for ch in str(nit) if ch.isdigit())
    if not nit:
        raise DianError('NIT requerido (solo dígitos).')
    if not (nombre or '').strip() or not (razon_social or '').strip():
        raise DianError('Nombre y razón social son obligatorios.')
    if ambiente not in AMBIENTES:
        raise DianError(f"Ambiente inválido: {ambiente}. Use {' o '.join(AMBIENTES)}.")
    if dv in (None, ''):
        dv = calcular_dv(nit)

    payload = {
        'nombre': nombre.strip(),
        'nit': nit,
        'digito_verificacion': int(dv),
        'razon_social': razon_social.strip(),
        'ambiente': ambiente,
        'prefijo': (prefijo or '').strip(),
    }
    status, body = _request(
        'POST', f"{_api()}/admin/tenants",
        headers={'X-Master-Key': Config.DIAN_MASTER_KEY},
        payload=payload, timeout=10,
    )
    if status == 409:
        raise DianError(
            f"El NIT {nit} ya está registrado en el servicio DIAN. Si pertenece a "
            "este cliente y perdió su API key, hay que rotarla desde el panel DIAN "
            "y pegarla manualmente en Integraciones → Facturación Electrónica.")
    if status == 401 or status == 403:
        raise DianError('El servicio DIAN rechazó la DIAN_MASTER_KEY del maestro.')
    if status != 201 or not body.get('api_key'):
        raise DianError(f"El servicio DIAN respondió HTTP {status}: "
                        f"{body.get('error', body)}")

    valores = {
        'DIAN_SERVICE_URL': _api(),
        'DIAN_API_KEY': body['api_key'],
        'DIAN_MASTER_KEY': Config.DIAN_MASTER_KEY,
    }
    if Config.DIAN_UI_URL:
        valores['DIAN_UI_URL'] = Config.DIAN_UI_URL
    ints.set_env_values(slug, valores)
    return {'tenant_dian_id': body.get('id'), 'nit': nit, 'dv': int(dv)}
