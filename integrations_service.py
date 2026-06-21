"""Integraciones / credenciales de API por cliente (administradas desde el maestro).

El app de cada cliente lee estas credenciales desde variables de entorno
(`PAYU_*`, `GOOGLE_*`, `MAIL_*`, etc.). En el modelo de una instancia por
cliente, cada cliente tiene su EnvironmentFile (`<INSTANCE_ENV_DIR>/<slug>.env`).
El maestro las administra editando ese archivo (secretos enmascarados) y luego
reinicia la instancia. NO toca `CyberShop/app/`.
"""

import json
import urllib.request
from pathlib import Path

from config import Config


def fetch_ai_models(base_url: str, timeout: float = 4.0) -> list:
    """Lista los modelos disponibles en el servidor Ollama del tenant (/api/tags).

    Tolerante: si no hay URL, la PC está apagada o falla la red, devuelve [] y el
    campo Modelo se queda como texto libre (no rompe la página).
    """
    base_url = (base_url or '').strip().rstrip('/')
    if not base_url:
        return []
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=timeout) as r:
            data = json.loads(r.read().decode('utf-8'))
        names = [m.get('name') for m in data.get('models', []) if m.get('name')]
        return sorted(names)
    except Exception:
        return []


# (key, label, secret?, type, options) — type: 'text' | 'select'
GROUPS = [
    ('Pasarela de pagos (PayU / PSE)', [
        ('PAYU_MERCHANT_ID', 'Merchant ID', False, 'text', None),
        ('PAYU_ACCOUNT_ID', 'Account ID', False, 'text', None),
        ('PAYU_API_LOGIN', 'API Login', True, 'text', None),
        ('PAYU_API_KEY', 'API Key', True, 'text', None),
        ('PAYU_ENV', 'Ambiente', False, 'select', ['sandbox', 'production']),
    ]),
    ('Inicio de sesión con Google', [
        ('GOOGLE_CLIENT_ID', 'Client ID', False, 'text', None),
        ('GOOGLE_CLIENT_SECRET', 'Client Secret', True, 'text', None),
        ('GOOGLE_REDIRECT_URI', 'Redirect URI (staff)', False, 'text', None),
        ('GOOGLE_LOGIN_REDIRECT_URI', 'Redirect URI (login cliente)', False, 'text', None),
    ]),
    ('Correo (SMTP)', [
        ('MAIL_SERVER', 'Servidor SMTP', False, 'text', None),
        ('MAIL_PORT', 'Puerto', False, 'text', None),
        ('MAIL_USERNAME', 'Usuario', False, 'text', None),
        ('MAIL_PASSWORD', 'Contraseña', True, 'text', None),
        ('MAIL_DEFAULT_SENDER', 'Remitente por defecto', False, 'text', None),
    ]),
    ('reCAPTCHA', [
        ('RECAPTCHA_SITE_KEY', 'Site Key (pública)', False, 'text', None),
        ('RECAPTCHA_SECRET_KEY', 'Secret Key', True, 'text', None),
    ]),
    ('Meta Pixel / Conversions API', [
        ('META_PIXEL_ID', 'Pixel ID', False, 'text', None),
        ('META_CAPI_ACCESS_TOKEN', 'CAPI Access Token', True, 'text', None),
        ('META_CAPI_TEST_EVENT_CODE', 'Test Event Code', False, 'text', None),
    ]),
    ('Facturación / Cuenta de cobro (DIAN)', [
        ('BILLING_ID', 'NIT / Identificación', False, 'text', None),
        ('BILLING_NOMBRE', 'Nombre / Razón social', False, 'text', None),
        ('BILLING_EMAIL', 'Email de facturación', False, 'text', None),
        ('BILLING_TELEFONO', 'Teléfono', False, 'text', None),
        ('BILLING_TEXTO_PAGO', 'Texto de pago', False, 'text', None),
    ]),
    ('Facturación Electrónica (microservicio DIAN)', [
        ('DIAN_SERVICE_URL', 'URL del servicio (con /api/v1)', False, 'text', None),
        ('DIAN_API_KEY', 'API Key del tenant DIAN', True, 'text', None),
        ('DIAN_MASTER_KEY', 'Master Key (SSO panel DIAN)', True, 'text', None),
        ('DIAN_UI_URL', 'URL pública del panel DIAN', False, 'text', None),
    ]),
    ('Asistente IA (Ollama / OpenAI-compatible)', [
        ('AI_BASE_URL', 'URL del servidor IA (ej. http://10.200.0.3:11434)', False, 'text', None),
        ('AI_MODEL', 'Modelo (ej. qwen2.5:14b-instruct)', False, 'text', None),
        ('AI_API_KEY', 'API Key (vacío para Ollama)', True, 'text', None),
    ]),
]

_FIELD_BY_KEY = {f[0]: f for grp, fields in GROUPS for f in fields}
SECRET_KEYS = {f[0] for grp, fields in GROUPS for f in fields if f[2]}
MANAGED_KEYS = list(_FIELD_BY_KEY.keys())


def env_path(slug: str) -> Path:
    return Path(Config.INSTANCE_ENV_DIR) / f"{slug}.env"


def read_env(slug: str) -> dict:
    """Lee TODO el env de la instancia (preserva claves no-gestionadas)."""
    p = env_path(slug)
    data = {}
    if not p.is_file():
        return data
    for line in p.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip()
    return data


def _mask(value: str) -> str:
    if not value:
        return ''
    if len(value) <= 6:
        return '••••'
    return value[:4] + '••••' + value[-2:]


def get_integrations(slug: str) -> list:
    """Estructura por grupos con valores actuales; secretos enmascarados."""
    env = read_env(slug)
    ai_models = None  # se consulta una sola vez, perezosamente
    out = []
    for group, fields in GROUPS:
        items = []
        for key, label, secret, ftype, options in fields:
            raw = env.get(key, '')
            # Modelo IA → desplegable con los modelos reales del Ollama del tenant.
            if key == 'AI_MODEL':
                if ai_models is None:
                    ai_models = fetch_ai_models(env.get('AI_BASE_URL', ''))
                if ai_models:
                    ftype = 'select'
                    options = list(ai_models)
                    if raw and raw not in options:   # no perder el valor actual
                        options = [raw] + options
            items.append({
                'key': key, 'label': label, 'secret': secret, 'type': ftype,
                'options': options,
                'value': '' if secret else raw,         # secretos no se reenvían
                'masked': _mask(raw) if secret else '',
                'has_value': bool(raw),
            })
        out.append({'group': group, 'fields': items})
    return out


def save_integrations(slug: str, form) -> None:
    """Mezcla los valores del form con el env existente y reescribe el archivo.

    - Campos normales: se setean tal cual (vacío = limpia).
    - Secretos: si el form trae valor → se actualiza; si viene vacío → se conserva.
    """
    env = read_env(slug)
    for key in MANAGED_KEYS:
        if key not in form:
            continue
        submitted = (form.get(key) or '').strip()
        is_secret = _FIELD_BY_KEY[key][2]
        if is_secret:
            if submitted:                 # solo actualiza si escribió algo nuevo
                env[key] = submitted
        else:
            env[key] = submitted
    _write_env(slug, env)


def set_env_values(slug: str, values: dict) -> None:
    """Setea/actualiza claves puntuales del env de la instancia preservando
    el resto (usado por dian_service al provisionar credenciales)."""
    env = read_env(slug)
    env.update({k: str(v) for k, v in values.items()})
    _write_env(slug, env)


def _write_env(slug: str, data: dict) -> None:
    p = env_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in data.items()]
    p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
