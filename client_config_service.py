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


def get_config(tenant_id: int) -> dict:
    """Devuelve {empresa: {k:v}, colores: {k:v}} desde cliente_config."""
    with tenant_cursor(tenant_id) as cur:
        cur.execute(
            "SELECT clave, valor FROM cliente_config WHERE clave = ANY(%s)",
            (_ALL_CONFIG_KEYS,),
        )
        values = {r['clave']: r['valor'] for r in cur.fetchall()}
    return {
        'empresa': {k: values.get(k, '') for k, *_ in EMPRESA_FIELDS},
        'colores': {k: values.get(k, '') for k, _ in COLOR_FIELDS},
    }


def save_config(tenant_id: int, form) -> None:
    """Guarda empresa + colores (solo claves conocidas)."""
    with tenant_cursor(tenant_id) as cur:
        for clave, _label, *_ in EMPRESA_FIELDS:
            if clave in form:
                _upsert(cur, clave, form.get(clave, '').strip(), 'text', 'empresa')
        for clave, _label in COLOR_FIELDS:
            if clave in form:
                _upsert(cur, clave, form.get(clave, '').strip(), 'color', 'colores')


def get_sections(tenant_id: int) -> dict:
    """Devuelve {key: bool} de config_secciones (default True si no existe)."""
    with tenant_cursor(tenant_id) as cur:
        cur.execute(
            "SELECT clave, valor FROM config_secciones WHERE clave = ANY(%s)",
            (_SECTION_KEYS,),
        )
        stored = {r['clave']: r['valor'] for r in cur.fetchall()}
    return {k: _as_bool(stored.get(k), True) for k, _ in SECTION_FIELDS}


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
