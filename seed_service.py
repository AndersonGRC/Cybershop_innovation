"""Seed mínimo de un tenant nuevo (tras aplicar el schema).

Inserta SOLO los datos imprescindibles para que el cliente pueda entrar y su
sitio público no se rompa:
  - roles (los 7 del sistema)
  - 1 usuario admin (rol propietario=2) con password temporal
  - cliente_config: empresa_nombre + paleta de colores de marca (azules, NO blanco)
  - config_secciones: secciones públicas activas
  - 1 género de muestra (catálogo no vacío)

NO copia datos del maestro (cuyos colores están dañados); usa defaults limpios.
"""

import secrets
import string

from werkzeug.security import generate_password_hash


# Los 7 roles del sistema (idénticos al maestro).
ROLES = [
    (1, 'admin'), (2, 'usuario'), (3, 'cliente'), (4, 'Empleado'),
    (5, 'Contador'), (6, 'Mesero'), (7, 'Cajero'),
]

# Paleta de marca CyberShop por defecto (canónica de _PUBLIC_COLOR_FIELDS).
BRAND_COLORS = {
    'color_secundario': '#0e1b33',
    'color_transicion': '#16315f',
    'color_fondo_destacado': '#edf3ff',
    'color_primario': '#122C94',
    'color_primario_oscuro': '#091C5A',
    'color_botones': '#122C94',
    'color_hover_menu': '#fb8500',
    'color_acento': '#e60023',
    'color_acento_secundario': '#fb8500',
    'color_producto_boton': '#091C5A',
    'color_producto_popup': '#122C94',
    'color_exito': '#28a745',
    'color_exito_hover': '#218838',
    'color_carrito': '#122C94',
    'color_carrito_hover': '#091C5A',
    'color_alerta_fondo': '#ffffff',
    'color_alerta_texto': '#333333',
    'color_alerta_confirmar': '#122C94',
    'color_alerta_cancelar': '#dc3545',
}

SECCIONES = [
    'mostrar_modulo_ventas', 'mostrar_about', 'mostrar_mision_vision',
    'mostrar_publicaciones', 'mostrar_mapa', 'mostrar_contacto',
    'mostrar_nav_productos', 'mostrar_nav_servicios',
    'mostrar_nav_quienes_somos', 'mostrar_nav_contacto',
]

_PWD_ALPHABET = string.ascii_letters + string.digits


def generate_temp_password(n: int = 12) -> str:
    return ''.join(secrets.choice(_PWD_ALPHABET) for _ in range(n))


def apply_seed(conn, *, nombre, admin_email, admin_nombre='Administrador',
               admin_password=None, tenant_local_id=1) -> dict:
    """Aplica el seed sobre la conexión de la BD del tenant (ya con schema).

    Devuelve {'admin_email', 'admin_password'} (password en claro, mostrar 1 vez).
    """
    admin_email = (admin_email or '').strip().lower()
    admin_password = admin_password or generate_temp_password()
    pwd_hash = generate_password_hash(admin_password)

    cur = conn.cursor()

    # 1) roles
    for rid, rnombre in ROLES:
        cur.execute(
            "INSERT INTO roles (id, nombre) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (rid, rnombre),
        )
    # Reajustar la secuencia de roles (insertamos ids explícitos)
    cur.execute("SELECT pg_get_serial_sequence('roles', 'id')")
    seq = cur.fetchone()[0]
    if seq:
        cur.execute(
            f"SELECT setval(%s, (SELECT GREATEST(COALESCE(MAX(id),1),1) FROM roles), true)",
            (seq,),
        )

    # 2) usuario admin (rol propietario=2) — solo si no hay admin aún
    cur.execute("SELECT 1 FROM usuarios WHERE rol_id IN (1, 2) LIMIT 1")
    if not cur.fetchone():
        cur.execute(
            'INSERT INTO usuarios (nombre, email, "contraseña", rol_id, estado, tenant_id) '
            'VALUES (%s, %s, %s, 2, %s, %s)',
            (admin_nombre, admin_email, pwd_hash, 'habilitado', tenant_local_id),
        )

    # 3) cliente_config: empresa + colores de marca
    cur.execute(
        "INSERT INTO cliente_config (clave, valor, tipo, grupo) VALUES (%s, %s, 'text', 'empresa') "
        "ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor",
        ('empresa_nombre', nombre),
    )
    cur.execute(
        "INSERT INTO cliente_config (clave, valor, tipo, grupo) VALUES (%s, %s, 'text', 'empresa') "
        "ON CONFLICT (clave) DO NOTHING",
        ('empresa_email', admin_email),
    )
    for clave, valor in BRAND_COLORS.items():
        cur.execute(
            "INSERT INTO cliente_config (clave, valor, tipo, grupo) VALUES (%s, %s, 'color', 'colores') "
            "ON CONFLICT (clave) DO NOTHING",
            (clave, valor),
        )

    # 4) config_secciones (todas activas)
    for clave in SECCIONES:
        cur.execute(
            "INSERT INTO config_secciones (clave, valor) VALUES (%s, 'true') "
            "ON CONFLICT (clave) DO NOTHING",
            (clave,),
        )

    # 5) género de muestra (catálogo no vacío)
    cur.execute("SELECT 1 FROM generos LIMIT 1")
    if not cur.fetchone():
        cur.execute("INSERT INTO generos (nombre) VALUES ('General')")

    conn.commit()
    return {'admin_email': admin_email, 'admin_password': admin_password}
