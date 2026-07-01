"""Configuración del sitio de cada cliente, administrada desde el maestro.

Lee/escribe `cliente_config` (empresa + colores) y `config_secciones` de la
BD del tenant — las MISMAS tablas que el app ya consume. Espejo multi-cliente
de /admin/configuracion-cliente y /admin/sitio-publico. SIN tocar el app.
"""

import os
import uuid

from config import Config
from tenant_db import tenant_cursor


# Datos de empresa editables.
EMPRESA_FIELDS = [
    ('empresa_nombre', 'Nombre de la empresa', 'text'),
    ('empresa_email', 'Email de contacto', 'text'),
    ('empresa_telefono', 'Teléfono', 'text'),
    ('empresa_whatsapp', 'WhatsApp', 'text'),
    ('empresa_direccion', 'Dirección', 'text'),
    ('empresa_website', 'Sitio web', 'text'),
    ('empresa_copyright', 'Copyright (pie de página)', 'text'),
]

# Colores de marca editables (mismas claves que el app).
COLOR_FIELDS = [
    ('color_primario', 'Color principal'),
    ('color_primario_oscuro', 'Principal oscuro'),
    ('color_secundario', 'Navbar y footer'),
    ('color_transicion', 'Gradiente header'),
    ('color_botones', 'Botones'),
    ('color_acento', 'Acento'),
    ('color_acento_secundario', 'Acento secundario'),
    ('color_hover_menu', 'Hover de menú'),
    ('color_fondo_destacado', 'Fondo destacado'),
    ('color_exito', 'Botón comprar'),
    ('color_carrito', 'Carrito'),
]

# Secciones públicas (toggles).
SECTION_FIELDS = [
    ('mostrar_modulo_ventas', 'Tienda y carrito'),
    ('mostrar_about', 'Quiénes somos (menú + bloque del home)'),
    ('mostrar_mision_vision', 'Misión y visión'),
    ('mostrar_publicaciones', 'Novedades del home'),
    ('mostrar_modulo_software', 'Módulo Software POS (pestaña + landing + checkout) — off por defecto'),
    ('mostrar_software_banner', 'Banda del Software (CTA a /software)'),
    ('mostrar_mapa', 'Mapa de ubicación'),
    ('mostrar_contacto', 'Contáctanos (menú + formulario del home)'),
    ('mostrar_nav_productos', 'Menú: Productos'),
    ('mostrar_nav_servicios', 'Menú: Servicios'),
    ('mostrar_login', 'Acceso / Login de clientes (botón Ingresar + /login)'),
]

# Claves "espejo": una sola casilla controla varias claves que el app lee por
# separado. "Quiénes somos" unifica el bloque del home (mostrar_about) y el ítem
# de menú (mostrar_nav_quienes_somos) → se escriben siempre con el mismo valor.
_SECTION_ALIASES = {
    'mostrar_about': ['mostrar_nav_quienes_somos'],
    'mostrar_contacto': ['mostrar_nav_contacto'],
}

_ALL_CONFIG_KEYS = [k for k, *_ in EMPRESA_FIELDS] + [k for k, _ in COLOR_FIELDS]
_SECTION_KEYS = [k for k, _ in SECTION_FIELDS] + [
    a for aliases in _SECTION_ALIASES.values() for a in aliases
]

# Defaults cuando la clave no existe en la BD del cliente. Casi todo es ON por
# defecto, pero la venta del Software CyberShop es OFF (espejo del app, que
# usa config_global.get('mostrar_modulo_software', false)).
_SECTION_DEFAULTS = {'mostrar_modulo_software': False}


def get_config(tenant_id: int) -> dict:
    """Valores de TODOS los campos del sitio (catalogo completo).

    Prioridad de lectura (igual que el app): public_site_settings (estructurada)
    -> cliente_config (legacy) -> default del catalogo.
    """
    from tenant_site_fields import SITE_FIELDS
    keys = [f['key'] for f in SITE_FIELDS]
    structured, legacy = {}, {}
    with tenant_cursor(tenant_id) as cur:
        cur.execute("SELECT to_regclass('public.public_site_settings')")
        if cur.fetchone()[0]:
            cur.execute("SELECT key, value FROM public_site_settings WHERE key = ANY(%s)", (keys,))
            structured = {r['key']: r['value'] for r in cur.fetchall()}
        cur.execute("SELECT clave, valor FROM cliente_config WHERE clave = ANY(%s)", (keys,))
        legacy = {r['clave']: r['valor'] for r in cur.fetchall()}
    values = {}
    for f in SITE_FIELDS:
        k = f['key']
        v = structured.get(k)
        if v is None or v == '':
            v = legacy.get(k)
        if v is None or v == '':
            v = f.get('default') or ''
        values[k] = v
    return {'values': values}


def save_config(tenant_id: int, form) -> int:
    """Guarda los campos enviados en AMBAS tablas (estructurada + legacy),
    igual que hace el app, para que el cambio surta efecto siempre.
    Devuelve cuantos campos se guardaron."""
    from tenant_site_fields import SITE_FIELDS
    guardados = 0
    with tenant_cursor(tenant_id) as cur:
        # La tabla estructurada puede no existir en BDs antiguas (legacy)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public_site_settings (
                key VARCHAR(120) PRIMARY KEY,
                value TEXT,
                value_type VARCHAR(30),
                group_name VARCHAR(60),
                description TEXT,
                sort_order INTEGER,
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        for f in SITE_FIELDS:
            k = f['key']
            if k not in form:
                continue
            v = (form.get(k) or '').strip()
            if f.get('type') == 'color' and not v:
                continue   # un color vacio romperia el sitio
            cur.execute(
                """
                UPDATE public_site_settings
                   SET value = %s, value_type = %s, group_name = %s,
                       description = %s, sort_order = %s, updated_at = NOW()
                 WHERE key = %s
                """,
                (v, f.get('type'), f.get('group'), f.get('description'), f.get('order'), k),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO public_site_settings (key, value, value_type, group_name, description, sort_order, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (k, v, f.get('type'), f.get('group'), f.get('description'), f.get('order')),
                )
            _upsert(cur, k, v, f.get('type') or 'text', f.get('group') or 'general')
            guardados += 1
    return guardados


_LOGO_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif')


def save_logo(tenant_id: int, file_storage) -> str:
    """Sube el logo del sitio público del tenant y actualiza `empresa_logo_url`.

    Replica a `public_site_service.save_public_logo` del app: guarda el archivo
    en el static COMPARTIDO (`<APP_DIR>/app/static/media/public_site/`) con un
    nombre único, y escribe la URL en AMBAS tablas del tenant
    (public_site_settings estructurada + cliente_config legacy), igual que
    `save_config`, para que el cambio surta efecto siempre.

    Devuelve la URL pública del logo (p.ej. `/static/media/public_site/...`).
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No se recibió ningún archivo.")

    _, ext = os.path.splitext(file_storage.filename)
    ext = ext.lower()
    if ext not in _LOGO_EXTS:
        ext = '.png'

    rel_dir = 'static/media/public_site'
    abs_dir = os.path.join(Config.APP_DIR, 'app', rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    filename = f'logo_publico_{uuid.uuid4().hex[:12]}{ext}'
    file_storage.save(os.path.join(abs_dir, filename))
    logo_url = f'/{rel_dir}/{filename}'

    with tenant_cursor(tenant_id) as cur:
        # estructurada (la que el app lee PRIMERO) — crear si la BD es legacy
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public_site_settings (
                key VARCHAR(120) PRIMARY KEY,
                value TEXT,
                value_type VARCHAR(30),
                group_name VARCHAR(60),
                description TEXT,
                sort_order INTEGER,
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            UPDATE public_site_settings
               SET value = %s, value_type = 'text', group_name = 'sitio_publico', updated_at = NOW()
             WHERE key = 'empresa_logo_url'
            """,
            (logo_url,),
        )
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO public_site_settings (key, value, value_type, group_name, updated_at)
                VALUES ('empresa_logo_url', %s, 'text', 'sitio_publico', NOW())
                """,
                (logo_url,),
            )
        # legacy: cliente_config
        _upsert(cur, 'empresa_logo_url', logo_url, 'text', 'sitio_publico')

    return logo_url


def get_sections(tenant_id: int) -> dict:
    """Devuelve {key: bool} de config_secciones (default True si no existe)."""
    with tenant_cursor(tenant_id) as cur:
        cur.execute(
            "SELECT clave, valor FROM config_secciones WHERE clave = ANY(%s)",
            (_SECTION_KEYS,),
        )
        stored = {r['clave']: r['valor'] for r in cur.fetchall()}
    return {k: _as_bool(stored.get(k), _SECTION_DEFAULTS.get(k, True)) for k, _ in SECTION_FIELDS}


def _write_section_flag(cur, clave, valor):
    """Escribe un flag de sección en AMBAS tablas (estructurada + legacy).

    UPDATE→INSERT (no ON CONFLICT): `config_secciones` puede no tener índice
    único en `clave` en BDs de clientes.
    """
    # --- legacy: config_secciones ---
    cur.execute("UPDATE config_secciones SET valor = %s WHERE clave = %s", (valor, clave))
    if cur.rowcount == 0:
        cur.execute("INSERT INTO config_secciones (clave, valor) VALUES (%s, %s)", (clave, valor))
    # --- estructurada: public_site_settings (la que el app lee PRIMERO) ---
    cur.execute(
        """
        UPDATE public_site_settings
           SET value = %s, value_type = 'boolean',
               group_name = 'secciones', updated_at = NOW()
         WHERE key = %s
        """,
        (valor, clave),
    )
    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO public_site_settings (key, value, value_type, group_name, updated_at)
            VALUES (%s, %s, 'boolean', 'secciones', NOW())
            """,
            (clave, valor),
        )


def save_sections(tenant_id: int, form) -> None:
    """Guarda los toggles de secciones en AMBAS tablas (estructurada + legacy).

    El app (`public_site_service.get_public_sections`) lee PRIMERO
    `public_site_settings` y solo cae a `config_secciones` si la clave no existe
    allí. Si solo escribiéramos `config_secciones`, el cambio del maestro NO
    surtiría efecto cuando `public_site_settings` ya tiene la clave (caso real:
    "Misión y visión" no desaparecía). Por eso escribimos en las dos, igual que
    hace `save_config`. Además, una casilla puede manejar varias claves espejo
    (`_SECTION_ALIASES`): p.ej. "Quiénes somos" controla bloque + menú a la vez.
    """
    with tenant_cursor(tenant_id) as cur:
        # La tabla estructurada puede no existir en BDs antiguas (legacy).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public_site_settings (
                key VARCHAR(120) PRIMARY KEY,
                value TEXT,
                value_type VARCHAR(30),
                group_name VARCHAR(60),
                description TEXT,
                sort_order INTEGER,
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        for clave, _label in SECTION_FIELDS:
            valor = 'true' if form.get(clave) else 'false'
            for k in [clave] + _SECTION_ALIASES.get(clave, []):
                _write_section_flag(cur, k, valor)


def _upsert(cur, clave, valor, tipo, grupo):
    """Escribe una clave en cliente_config sin depender de un índice único.

    La tabla cliente_config de los tenants NO siempre tiene índice único en
    `clave`, así que ON CONFLICT fallaba. UPDATE→INSERT es idempotente y
    self-healing (si hay filas duplicadas, las normaliza todas).
    """
    cur.execute(
        "UPDATE cliente_config SET valor = %s, tipo = %s, grupo = %s WHERE clave = %s",
        (valor, tipo, grupo, clave),
    )
    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO cliente_config (clave, valor, tipo, grupo) VALUES (%s, %s, %s, %s)",
            (clave, valor, tipo, grupo),
        )


def set_values(tenant_id: int, mapping: dict, grupo: str = 'empresa', tipo: str = 'text') -> int:
    """Escribe varias claves en cliente_config (omite vacías). Devuelve cuántas.

    Usa el mismo UPDATE→INSERT robusto que el resto del servicio (no depende de
    índice único). Útil al crear un cliente para sembrar sus datos de contacto.
    """
    n = 0
    with tenant_cursor(tenant_id) as cur:
        for clave, valor in (mapping or {}).items():
            valor = (valor or '').strip()
            if not valor:
                continue
            _upsert(cur, clave, valor, tipo, grupo)
            n += 1
    return n


def _as_bool(value, default=True):
    if value is None:
        return default
    return str(value).strip().lower() not in {'false', '0', 'no', 'off', ''}
