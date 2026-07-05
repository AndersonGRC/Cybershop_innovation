"""Módulos por cliente — administrados desde el maestro.

Controla los módulos vía `cliente_config[config_key]` (p.ej. `pos_habilitado`),
que es exactamente el flag que el app de cada cliente lee para activar/ocultar
cada módulo (fallback de `tenant_features`). No usa las tablas `saas_*` (que en
el maestro están SIN constraints/uso). SIN tocar el app.
"""

from tenant_db import tenant_cursor


# Catálogo de módulos (espejo de MODULE_DEFINITIONS del app).
# (code, nombre, descripcion, categoria, config_key, default)
MODULES = [
    ('orders', 'Pedidos', 'Pedidos web y seguimiento comercial.', 'ventas', 'pedidos_habilitado', True),
    ('pos', 'Punto de Venta', 'Ventas rápidas, historial POS y facturación mostrador.', 'ventas', 'pos_habilitado', True),
    ('caja', 'Caja / Arqueo', 'Apertura de caja con base, movimientos de efectivo y cuadre diario. Al desactivarlo el POS cobra sin exigir caja abierta.', 'ventas', 'caja_habilitado', True),
    ('quotes', 'Cotizaciones', 'Cotizaciones PDF y seguimiento.', 'ventas', 'cotizaciones_habilitado', True),
    ('billing', 'Cuentas de Cobro', 'Documentos de cobro para contratistas y servicios.', 'ventas', 'cuentas_cobro_habilitado', True),
    ('coupons', 'Cupones', 'Promociones y descuentos por código.', 'ventas', 'cupones_habilitado', True),
    ('inventory', 'Inventario', 'Catálogo, stock, géneros y reseñas.', 'catalogo', 'inventario_habilitado', True),
    ('wishlist', 'Wishlist', 'Favoritos de clientes y estadísticas.', 'catalogo', 'wishlist_habilitado', True),
    ('content', 'Contenido Web', 'Publicaciones, slides y servicios del sitio.', 'contenido', 'contenido_web_habilitado', True),
    ('users', 'Usuarios', 'Gestión y creación de usuarios administrativos.', 'administracion', 'usuarios_habilitado', True),
    ('payroll', 'Nómina', 'Empleados, periodos, novedades y liquidaciones.', 'administracion', 'nomina_habilitada', True),
    ('crm', 'CRM', 'Contactos, tareas y actividades comerciales.', 'clientes', 'crm_habilitado', True),
    ('accounting', 'Contabilidad', 'Movimientos, plantillas y cierres contables.', 'finanzas', 'contabilidad_habilitada', True),
    ('support', 'Soporte', 'Tickets de clientes y configuración del canal.', 'clientes', 'soporte_habilitado', True),
    ('video', 'Videollamadas', 'Salas de videollamadas con Jitsi.', 'clientes', 'video_habilitado', True),
    ('share', 'Compartir Archivos', 'Carpetas y archivos compartidos por link.', 'clientes', 'share_habilitado', True),
    ('restaurant_tables', 'Mesas Restaurante', 'Plano de mesas, cuenta abierta y consumos.', 'operacion', 'restaurant_tables_habilitado', True),
    ('facturacion_electronica', 'Facturación DIAN', 'Facturación electrónica integrada con DIAN.', 'finanzas', 'facturacion_electronica', False),
    ('ai_assistant', 'Asistente IA', 'IA para descripciones, SEO y auto-respuestas. Cada cliente con su propio agente aislado a su BD.', 'inteligencia', 'ia_habilitado', False),
]

MODULE_BY_CODE = {m[0]: m for m in MODULES}
CONFIG_KEY_BY_CODE = {m[0]: m[4] for m in MODULES}
ALL_CODES = [m[0] for m in MODULES]
_ALL_CONFIG_KEYS = [m[4] for m in MODULES]

# Defaults por plan (qué módulos vienen activos). El operador puede ajustar.
PLAN_MODULES = {
    'basico':   {'pos', 'caja', 'inventory', 'orders', 'content', 'users'},
    'estandar': {'pos', 'caja', 'inventory', 'orders', 'content', 'users', 'quotes',
                 'billing', 'coupons', 'wishlist', 'crm', 'support'},
    'ultra':    set(ALL_CODES) - {'facturacion_electronica'},
}
PLANS = list(PLAN_MODULES.keys())

# Nombres de plan legacy que aún viven en la tabla `tenants` (default histórico
# 'standard', clientes 'legacy'). Se aceptan como alias para que "Aplicar plan"
# funcione desde el panel SIN mutar la data existente.
PLAN_ALIASES = {
    'standard': 'estandar',
    'std':      'estandar',
    'legacy':   'estandar',
    'basic':    'basico',
}


def normalize_plan(plan: str) -> str:
    """Devuelve un plan válido del catálogo. Resuelve alias legacy y normaliza
    a minúsculas; si no calza con nada, cae a 'estandar'."""
    p = (plan or '').strip().lower()
    p = PLAN_ALIASES.get(p, p)
    return p if p in PLAN_MODULES else 'estandar'


def _as_bool(value, default):
    if value is None:
        return default
    return str(value).strip().lower() not in {'false', '0', 'no', 'off', ''}


def get_modules(tenant_id: int) -> list:
    """Lista de módulos del cliente con su is_active resuelto desde cliente_config."""
    with tenant_cursor(tenant_id) as cur:
        cur.execute(
            "SELECT clave, valor FROM cliente_config WHERE clave = ANY(%s)",
            (_ALL_CONFIG_KEYS,),
        )
        stored = {r['clave']: r['valor'] for r in cur.fetchall()}
    out = []
    for code, nombre, desc, cat, ck, default in MODULES:
        out.append({
            'code': code, 'nombre': nombre, 'descripcion': desc, 'categoria': cat,
            'is_active': _as_bool(stored.get(ck), default),
        })
    return out


def _upsert_flag(cur, config_key, active, descripcion):
    """Activa/desactiva un flag de módulo en cliente_config.

    No usa `ON CONFLICT` porque la tabla `cliente_config` de los tenants NO
    tiene índice único en `clave` (varía por cliente), y ON CONFLICT exige uno
    → "there is no unique or exclusion constraint matching the ON CONFLICT
    specification". Hacemos UPDATE y, si no afectó filas, INSERT. Idempotente.
    """
    valor = 'true' if active else 'false'
    cur.execute(
        "UPDATE cliente_config SET valor = %s, grupo = 'modulos' WHERE clave = %s",
        (valor, config_key),
    )
    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO cliente_config (clave, valor, tipo, grupo, descripcion, orden)
            VALUES (%s, %s, 'boolean', 'modulos', %s, 0)
            """,
            (config_key, valor, descripcion),
        )


def set_module(tenant_id: int, code: str, active: bool):
    meta = MODULE_BY_CODE.get(code)
    if not meta:
        raise ValueError(f"Módulo desconocido: {code}")
    with tenant_cursor(tenant_id) as cur:
        _upsert_flag(cur, meta[4], active, meta[2])


def apply_plan(tenant_id: int, plan: str):
    """Activa/desactiva todos los módulos según los defaults del plan.

    Acepta nombres legacy (p.ej. 'standard') vía normalize_plan(), de modo que el
    botón "Aplicar plan" del panel funcione aunque la fila `tenants` traiga el
    nombre viejo."""
    plan = normalize_plan(plan)
    enabled = PLAN_MODULES[plan]
    with tenant_cursor(tenant_id) as cur:
        for code, nombre, desc, cat, ck, default in MODULES:
            _upsert_flag(cur, ck, code in enabled, desc)


def save_modules(tenant_id: int, active_codes) -> None:
    """Guarda el estado de TODOS los módulos: activo si su code está en
    `active_codes` (set/list), inactivo si no. (Para el form de checkboxes.)"""
    active = set(active_codes or [])
    with tenant_cursor(tenant_id) as cur:
        for code, nombre, desc, cat, ck, default in MODULES:
            _upsert_flag(cur, ck, code in active, desc)
