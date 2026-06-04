"""Operaciones sobre tenants: crear, listar, suspender, ver detalle.

create_tenant() es el orquestador end-to-end que reemplaza la cadena
de scripts CLI (createdb + migrate_prod_to_tenant.py + crear_sync_key.py).
"""

import re
import subprocess
from pathlib import Path

import psycopg2.sql as sql

from config import Config
from crypto import aes_gcm_encrypt
from db import control_plane_cursor, get_postgres_admin_conn, get_tenant_conn
from api_key_service import issue_key
import seed_service
import provisioning_service


# slug válido: minúsculas, números, guiones; sin doble guión; 3-40 chars.
_SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class TenantCreationError(Exception):
    """Algo falló creando el tenant. El mensaje describe en qué paso."""


# ──────────────────────────────────────────────
# Lectura
# ──────────────────────────────────────────────

def list_tenants(search: str = '') -> list:
    """Tabla de tenants con stats agregadas (count keys + última actividad)."""
    where = ''
    params = []
    if search.strip():
        where = "WHERE t.slug ILIKE %s OR t.nombre ILIKE %s"
        like = f'%{search.strip()}%'
        params = [like, like]

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(f"""
            SELECT
                t.id, t.slug, t.nombre, t.estado, t.plan, t.created_at,
                td.db_name,
                COALESCE(k.total_keys, 0)    AS total_keys,
                COALESCE(k.active_keys, 0)   AS active_keys,
                k.last_used_at
            FROM tenants t
            LEFT JOIN tenant_databases td ON td.tenant_id = t.id
            LEFT JOIN (
                SELECT tenant_id,
                       COUNT(*)                                       AS total_keys,
                       COUNT(*) FILTER (WHERE active)                 AS active_keys,
                       MAX(last_used_at)                              AS last_used_at
                FROM sync_api_keys
                GROUP BY tenant_id
            ) k ON k.tenant_id = t.id
            {where}
            ORDER BY t.created_at DESC
        """, params)
        return cur.fetchall()


def get_tenant(tenant_id: int) -> dict | None:
    """Trae info de un tenant + su tenant_databases."""
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT t.id, t.slug, t.nombre, t.estado, t.plan, t.created_at,
                   td.db_name, td.db_host, td.db_port, td.schema_version,
                   td.last_migrated_at
            FROM tenants t
            LEFT JOIN tenant_databases td ON td.tenant_id = t.id
            WHERE t.id = %s
        """, (tenant_id,))
        return cur.fetchone()


def set_estado(tenant_id: int, estado: str):
    """Cambia estado del tenant: 'activo' | 'suspendido' | 'cancelado'.

    Si pasa a 'suspendido', también desactiva todas sus API keys.
    Si pasa a 'activo', NO reactiva keys automáticamente (es manual,
    para que el admin elija cuál key vuelve a estar viva).
    """
    if estado not in ('activo', 'suspendido', 'cancelado'):
        raise ValueError(f"Estado inválido: {estado}")

    with control_plane_cursor() as cur:
        cur.execute(
            "UPDATE tenants SET estado = %s WHERE id = %s",
            (estado, tenant_id)
        )
        if estado in ('suspendido', 'cancelado'):
            cur.execute(
                "UPDATE sync_api_keys SET active = FALSE WHERE tenant_id = %s",
                (tenant_id,)
            )


def dashboard_stats() -> dict:
    """Stats agregadas para la home del admin."""
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE estado = 'activo')      AS tenants_activos,
                COUNT(*) FILTER (WHERE estado = 'suspendido')  AS tenants_suspendidos,
                COUNT(*)                                       AS tenants_total
            FROM tenants
        """)
        t = cur.fetchone()
        cur.execute("""
            SELECT
                COUNT(*)                              AS keys_total,
                COUNT(*) FILTER (WHERE active)        AS keys_activas,
                MAX(last_used_at)                     AS ultimo_sync
            FROM sync_api_keys
        """)
        k = cur.fetchone()
        cur.execute("""
            SELECT s.client_code, s.key_prefix, s.last_used_at,
                   t.slug, t.nombre
            FROM sync_api_keys s
            JOIN tenants t ON t.id = s.tenant_id
            WHERE s.last_used_at IS NOT NULL
            ORDER BY s.last_used_at DESC
            LIMIT 10
        """)
        actividad = cur.fetchall()

    return {
        'tenants_total':       t['tenants_total'],
        'tenants_activos':     t['tenants_activos'],
        'tenants_suspendidos': t['tenants_suspendidos'],
        'keys_total':          k['keys_total'],
        'keys_activas':        k['keys_activas'],
        'ultimo_sync':         k['ultimo_sync'],
        'actividad':           actividad,
    }


# ──────────────────────────────────────────────
# Creación de tenant nuevo (orquestador)
# ──────────────────────────────────────────────

def validate_slug(slug: str) -> str:
    """Normaliza y valida slug. Levanta TenantCreationError si inválido."""
    slug = (slug or '').strip().lower()
    if not _SLUG_RE.match(slug):
        raise TenantCreationError(
            f"Slug inválido: '{slug}'. Solo minúsculas, números y guiones "
            "(ej. 'panaderia-roma' o 'cyber-t042')."
        )
    if len(slug) < 3 or len(slug) > 40:
        raise TenantCreationError("Slug debe tener entre 3 y 40 caracteres.")
    return slug


def compute_db_name(slug: str) -> str:
    """Decide el db_name para un slug nuevo.

    - Si el slug calza el patrón cyber-tNNN, usa cyber_tNNN.
    - Si no, busca el siguiente cyber_tNNN disponible (auto-incremental).
    """
    m = re.match(r'^cyber-t(\d{3,5})$', slug)
    if m:
        return f"cyber_t{int(m.group(1)):03d}"

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT db_name FROM tenant_databases
            WHERE db_name ~ '^cyber_t[0-9]{3,5}$'
            ORDER BY db_name DESC LIMIT 1
        """)
        row = cur.fetchone()

    if not row:
        return 'cyber_t001'
    last = int(row['db_name'].replace('cyber_t', ''))
    return f'cyber_t{last + 1:03d}'


def _slug_exists(slug: str) -> bool:
    with control_plane_cursor() as cur:
        cur.execute("SELECT 1 FROM tenants WHERE slug = %s", (slug,))
        return cur.fetchone() is not None


def _db_exists(db_name: str) -> bool:
    conn = get_postgres_admin_conn(autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def _create_database(db_name: str):
    """CREATE DATABASE — debe correrse fuera de transacción."""
    conn = get_postgres_admin_conn(autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db_name),
                    sql.Identifier(Config.PG_USER),
                )
            )
    finally:
        conn.close()


def _apply_schema(db_name: str):
    """Aplica el SQL del schema base usando psql como subproceso.

    Usamos psql (no psycopg2 ejecutando el string) porque migrate_backup_db.sql
    puede contener comandos meta de psql (\\COPY, \\i, etc) y statement
    boundaries delicados que psycopg2 no parsea bien.
    """
    schema = Path(Config.TENANT_SCHEMA_FILE)
    if not schema.is_file():
        raise TenantCreationError(
            f"TENANT_SCHEMA_FILE no existe: {schema}\n"
            "Configurá la ruta correcta en .cybershop.conf"
        )

    psql = Config.PSQL_BIN
    env = {
        'PGPASSWORD': Config.PG_PASSWORD,
        'PGHOST':     Config.PG_HOST,
        'PGPORT':     str(Config.PG_PORT),
        'PGUSER':     Config.PG_USER,
    }
    import os
    full_env = {**os.environ, **env}

    cmd = [psql, '-d', db_name, '-f', str(schema),
           '-v', 'ON_ERROR_STOP=1', '--quiet']
    try:
        result = subprocess.run(
            cmd, env=full_env, capture_output=True, text=True, timeout=120
        )
    except FileNotFoundError as exc:
        raise TenantCreationError(
            f"No se encontró psql en '{psql}'. Configurá PSQL_BIN en .cybershop.conf"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise TenantCreationError(
            f"psql tardó más de 120s aplicando el schema a {db_name}"
        ) from exc

    if result.returncode != 0:
        raise TenantCreationError(
            f"psql falló aplicando schema a {db_name}:\n{result.stderr}"
        )


def _apply_seed(db_name: str, nombre: str, admin_email: str) -> dict:
    """Aplica el seed mínimo (roles, admin, colores, secciones) a la BD nueva
    y marca las migraciones de tenant actuales como aplicadas (el dump ya las
    incluye), para que `migrate_tenants` solo corra las futuras.

    Devuelve {'admin_email', 'admin_password'} (mostrar 1 vez).
    """
    import tenant_migrations
    conn = get_tenant_conn(db_name)
    try:
        seed = seed_service.apply_seed(conn, nombre=nombre, admin_email=admin_email)
        tenant_migrations.mark_all_applied(conn)
        return seed
    finally:
        conn.close()


def _insert_tenant_rows(slug: str, nombre: str, db_name: str) -> int:
    """INSERT en tenants + tenant_databases. Devuelve tenant_id."""
    db_password_enc = aes_gcm_encrypt(Config.PG_PASSWORD)

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "INSERT INTO tenants (slug, nombre) VALUES (%s, %s) RETURNING id",
            (slug, nombre)
        )
        tenant_id = cur.fetchone()['id']

        cur.execute(
            """
            INSERT INTO tenant_databases
                (tenant_id, db_host, db_port, db_name, db_user, db_password_enc, schema_version)
            VALUES (%s, %s, %s, %s, %s, %s, '0001')
            """,
            (
                tenant_id,
                Config.PG_HOST,
                Config.PG_PORT,
                db_name,
                Config.PG_USER,
                db_password_enc,
            )
        )

    return tenant_id


def create_tenant(slug: str, nombre: str, key_label: str = 'Primera key',
                  admin_email: str = '') -> dict:
    """Orquesta la creación end-to-end de un tenant nuevo.

    Pasos:
      1. Validar slug y nombre.
      2. Computar db_name único.
      3. Verificar que ni el slug ni la DB existan.
      4. CREATE DATABASE cyber_tNNN.
      5. Aplicar schema base con psql.
      6. Seed mínimo (roles, admin, colores, secciones).
      7. INSERT en tenants + tenant_databases.
      8. Emitir primera API key + client_code.

    Returns dict con todo lo necesario para mostrarle al admin:
      {tenant_id, slug, db_name, api_key, client_code, key_prefix,
       admin_email, admin_password}

    Si algo falla, levanta TenantCreationError con mensaje específico.
    """
    nombre = (nombre or '').strip()
    if not nombre or len(nombre) > 100:
        raise TenantCreationError("El nombre del tenant es obligatorio (max 100 chars).")

    slug = validate_slug(slug)
    admin_email = (admin_email or '').strip().lower() or f'admin@{slug}.local'

    if _slug_exists(slug):
        raise TenantCreationError(f"Ya existe un tenant con slug '{slug}'.")

    db_name = compute_db_name(slug)

    if _db_exists(db_name):
        raise TenantCreationError(
            f"Ya existe una base de datos '{db_name}' en Postgres. "
            "Borrala manualmente o elegí otro slug."
        )

    # Paso 4: crear DB
    try:
        _create_database(db_name)
    except Exception as exc:  # noqa: BLE001
        raise TenantCreationError(f"CREATE DATABASE {db_name} falló: {exc}") from exc

    # Paso 5: aplicar schema
    try:
        _apply_schema(db_name)
    except TenantCreationError:
        # Schema falló — la DB queda vacía. Reportar pero NO borrar (audit).
        raise
    except Exception as exc:  # noqa: BLE001
        raise TenantCreationError(
            f"Schema base falló en {db_name}: {exc}\n"
            f"BD huérfana — borrala manualmente: DROP DATABASE {db_name};"
        ) from exc

    # Paso 6: seed mínimo (roles, admin, colores, secciones)
    try:
        seed = _apply_seed(db_name, nombre, admin_email)
    except Exception as exc:  # noqa: BLE001
        raise TenantCreationError(
            f"Seed inicial falló en {db_name}: {exc}\n"
            f"BD huérfana — borrala manualmente: DROP DATABASE {db_name};"
        ) from exc

    # Paso 7: registrar en control plane
    try:
        tenant_id = _insert_tenant_rows(slug, nombre, db_name)
    except Exception as exc:  # noqa: BLE001
        raise TenantCreationError(
            f"INSERT en tenants/tenant_databases falló: {exc}\n"
            f"BD huérfana — borrala manualmente: DROP DATABASE {db_name};"
        ) from exc

    # Paso 7: primera API key
    try:
        key_info = issue_key(tenant_id, label=key_label)
    except Exception as exc:  # noqa: BLE001
        raise TenantCreationError(
            f"Tenant creado pero falló emisión de primera key: {exc}\n"
            f"Podés emitirla manualmente desde el detalle del tenant."
        ) from exc

    # Paso 9: aprovisionar instancia + dominio (puerto, env, runtime; service/Caddy en Linux)
    prov = {'port': None, 'domain': None, 'instance_status': 'pending'}
    try:
        prov = provisioning_service.provision(tenant_id, slug, db_name, subdomain=slug)
    except Exception as exc:  # noqa: BLE001
        # No abortamos: el tenant ya existe; se puede reaprovisionar desde el detalle.
        prov['error'] = str(exc)

    return {
        'tenant_id':      tenant_id,
        'slug':           slug,
        'nombre':         nombre,
        'db_name':        db_name,
        'api_key':        key_info['api_key'],
        'client_code':    key_info['client_code'],
        'key_prefix':     key_info['key_prefix'],
        'key_id':         key_info['id'],
        'admin_email':    seed['admin_email'],
        'admin_password': seed['admin_password'],
        'port':           prov.get('port'),
        'domain':         prov.get('domain'),
        'instance_status': prov.get('instance_status'),
    }
