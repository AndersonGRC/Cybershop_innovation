"""timezone_service.py — Zona horaria por tenant (IANA) para el admin maestro.

La app cliente lee ``APP_TIMEZONE`` de su ``.env`` de instancia y la aplica al
proceso (``datetime.now()``) y a la sesión de PostgreSQL (``CURRENT_TIMESTAMP``/
``now()``). Aquí vive la lista curada para el desplegable del panel y los helpers
para leer/validar/escribir la zona configurada de una instancia.

No es retroactivo: solo cambia lo que se registra de ahí en adelante.
"""

import integrations_service as ints

DEFAULT_TZ = 'America/Bogota'
ENV_KEY = 'APP_TIMEZONE'

# (IANA, etiqueta visible, offset aprox). Curada: LatAm + zonas comunes.
TIMEZONES = [
    ('America/Bogota',                 'Colombia (Bogotá)',            'UTC−5'),
    ('America/Lima',                   'Perú (Lima)',                  'UTC−5'),
    ('America/Guayaquil',              'Ecuador (Guayaquil)',          'UTC−5'),
    ('America/Panama',                 'Panamá',                       'UTC−5'),
    ('America/Mexico_City',            'México (Ciudad de México)',    'UTC−6'),
    ('America/Costa_Rica',             'Costa Rica',                   'UTC−6'),
    ('America/Guatemala',              'Guatemala',                    'UTC−6'),
    ('America/El_Salvador',            'El Salvador',                  'UTC−6'),
    ('America/Tegucigalpa',            'Honduras',                     'UTC−6'),
    ('America/Managua',                'Nicaragua',                    'UTC−6'),
    ('America/Caracas',                'Venezuela (Caracas)',          'UTC−4'),
    ('America/La_Paz',                 'Bolivia (La Paz)',             'UTC−4'),
    ('America/Santo_Domingo',          'Rep. Dominicana',              'UTC−4'),
    ('America/Puerto_Rico',            'Puerto Rico',                  'UTC−4'),
    ('America/Santiago',               'Chile (Santiago)',             'UTC−4/−3'),
    ('America/Asuncion',               'Paraguay (Asunción)',          'UTC−4/−3'),
    ('America/Argentina/Buenos_Aires', 'Argentina (Buenos Aires)',     'UTC−3'),
    ('America/Montevideo',             'Uruguay (Montevideo)',         'UTC−3'),
    ('America/Sao_Paulo',              'Brasil (São Paulo)',           'UTC−3'),
    ('America/New_York',               'EE.UU. Este (Nueva York)',     'UTC−5/−4'),
    ('America/Chicago',                'EE.UU. Centro (Chicago)',      'UTC−6/−5'),
    ('America/Denver',                 'EE.UU. Montaña (Denver)',      'UTC−7/−6'),
    ('America/Los_Angeles',            'EE.UU. Pacífico (Los Ángeles)', 'UTC−8/−7'),
    ('Europe/Madrid',                  'España (Madrid)',              'UTC+1/+2'),
    ('UTC',                            'UTC (universal)',              'UTC+0'),
]

_VALID = {z[0] for z in TIMEZONES}


def is_valid(tz: str) -> bool:
    return tz in _VALID


def current_tz(slug: str) -> str:
    """Zona horaria actual de la instancia (de su .env); default si no está."""
    try:
        return (ints.read_env(slug).get(ENV_KEY) or '').strip() or DEFAULT_TZ
    except Exception:
        return DEFAULT_TZ


def set_tz(slug: str, tz: str) -> None:
    """Escribe APP_TIMEZONE en el .env de la instancia (no reinicia; el que llama
    decide reiniciar para aplicar)."""
    ints.set_env_values(slug, {ENV_KEY: tz})
