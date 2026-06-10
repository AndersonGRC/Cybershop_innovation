"""Configuración del sitio de cada cliente, administrada desde el maestro.

Lee/escribe `cliente_config` (empresa + colores) y `config_secciones` de la
BD del tenant — las MISMAS tablas que el app ya consume. Espejo multi-cliente
de /admin/configuracion-cliente y /admin/sitio-publico. SIN tocar el app.
"""

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
    ('mostrar_about', 'Bloque quiénes somos'),
    ('mostrar_mision_vision', 'Misión y visión'),
    ('mostrar_publicaciones', 'Novedades del home'),
    ('mostrar_modulo_software', 'Módulo Software POS (pestaña + landing + checkout) — off por defecto'),
    ('mostrar_software_banner', 'Banda del Software (CTA a /software)'),
    ('mostrar_mapa', 'Mapa de ubicación'),
    ('mostrar_contacto', 'Formulario de contacto'),
    ('mostrar_nav_productos', 'Menú: Productos'),
    ('mostrar_nav_servicios', 'Menú: Servicios'),
    ('mostrar_nav_quienes_somos', 'Menú: Quiénes somos'),
    ('mostrar_nav_contacto', 'Menú: Contáctanos'),
]

_ALL_CONFIG_KEYS = [k for k, *_ in EMPRESA_FIELDS] + [k for k, _ in COLOR_FIELDS]
_SECTION_KEYS = [k for k, _ in SECTION_FIELDS]

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
                INSERT INTO public_site_settings (key, value, value_type, group_name, description, sort_order, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                """,
                (k, v, f.get('type'), f.get('group'), f.get('description'), f.get('order')),
            )
            cur.execute(
                """
                INSERT INTO cliente_config (clave, valor, tipo, grupo)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
                """,
                (k, v, f.get('type') or 'text', f.get('group') or 'general'),
            )
            guardados += 1
    return guardados


def get_sections(tenant_id: int) -> dict:
    """Devuelve {key: bool} de config_secciones (default True si no existe)."""
    with tenant_cursor(tenant_id) as cur:
        cur.execute(
            "SELECT clave, valor FROM config_secciones WHERE clave = ANY(%s)",
            (_SECTION_KEYS,),
        )
        stored = {r['clave']: r['valor'] for r in cur.fetchall()}
    return {k: _as_bool(stored.get(k), _SECTION_DEFAULTS.get(k, True)) for k, _ in SECTION_FIELDS}


def save_sections(tenant_id: int, form) -> None:
    """Guarda los toggles de secciones (checkbox: presente=true)."""
    with tenant_cursor(tenant_id) as cur:
        for clave, _label in SECTION_FIELDS:
            valor = 'true' if form.get(clave) else 'false'
            cur.execute(
                """
                INSERT INTO config_secciones (clave, valor) VALUES (%s, %s)
                ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
                """,
                (clave, valor),
            )


def _upsert(cur, clave, valor, tipo, grupo):
    cur.execute(
        """
        INSERT INTO cliente_config (clave, valor, tipo, grupo)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
        """,
        (clave, valor, tipo, grupo),
    )


def _as_bool(value, default=True):
    if value is None:
        return default
    return str(value).strip().lower() not in {'false', '0', 'no', 'off', ''}
