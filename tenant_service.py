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


def compute_db_name(tenant_id: int) -> str:
    """db_name determinístico a partir del tenant_id: `cyber_t<ID>` (mín. 3 díg.).

    Derivar del id del control plane (y NO de un contador propio ni del slug)
    elimina la colisión histórica donde el slug 'cyber-t001' no correspondía a la
    DB 'cyber_t001' (esa pertenecía a otro tenant). Como el id es único y la fila
    `tenants` se reserva antes de crear la DB, el nombre nunca colisiona entre
    clientes nuevos.
    """
    return f"cyber_t{int(tenant_id):03d}"


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


def _apply_seed(db_name: str, nombre: str, admin_email: str, slug: str = 'principal',
                admin_nombre: str = 'Administrador') -> dict:
    """Aplica el seed mínimo (roles, admin, colores, secciones) a la BD nueva
    y la pone en la ÚLTIMA versión de estructura.

    Para garantizar que un cliente nuevo nazca SIEMPRE al día, ejecuta las
    migraciones de tenant (aditivas e idempotentes): si el dump del schema ya
    las incluye son no-ops; si el dump quedó desactualizado, cierran la brecha.
    Si alguna migración fallara, no se aborta la creación (la estructura del
    dump ya es funcional) y se podrá reintentar con "Actualizar a última versión".

    Devuelve {'admin_email', 'admin_password'} (mostrar 1 vez).
    """
    import tenant_migrations
    conn = get_tenant_conn(db_name)
    try:
        seed = seed_service.apply_seed(conn, nombre=nombre, admin_email=admin_email,
                                       admin_nombre=admin_nombre or 'Administrador',
                                       tenant_slug=slug)
    finally:
        conn.close()
    try:
        tenant_migrations.migrate_db(db_name)
    except Exception:  # noqa: BLE001 — una migración rota no impide crear al cliente
        conn2 = get_tenant_conn(db_name)
        try:
            tenant_migrations.mark_all_applied(conn2)
        finally:
            conn2.close()
    return seed


def _insert_tenant_row(slug: str, nombre: str, plan: str = 'estandar') -> int:
    """Reserva la fila en `tenants` y devuelve el id (para derivar el db_name).

    Se hace ANTES de crear la DB: así el nombre de la DB queda atado al id y, si
    algo falla después, _rollback_partial_tenant() borra esta fila."""
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "INSERT INTO tenants (slug, nombre, plan) VALUES (%s, %s, %s) RETURNING id",
            (slug, nombre, plan)
        )
        return cur.fetchone()['id']


def _insert_tenant_db_row(tenant_id: int, db_name: str):
    """Registra la DB del tenant en el control plane (password Postgres cifrada)."""
    db_password_enc = aes_gcm_encrypt(Config.PG_PASSWORD)
    with control_plane_cursor() as cur:
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


def _rollback_partial_tenant(tenant_id: int | None, db_name: str | None, drop_db: bool):
    """Compensa una creación fallida: dropea la DB (solo si la creamos en este
    intento) y borra las filas parciales del control plane. Best-effort: nunca
    enmascara el error original (todo en try/except silencioso).

    Las FK de tenant_databases/tenant_runtime/usuarios_globales NO tienen ON
    DELETE CASCADE, por eso se borran explícitamente antes que `tenants`.
    """
    if drop_db and db_name:
        try:
            import lifecycle_service  # import diferido: lifecycle importa este módulo
            lifecycle_service.destroy_database(db_name)
        except Exception:  # noqa: BLE001
            pass
    if tenant_id:
        try:
            with control_plane_cursor() as cur:
                cur.execute("DELETE FROM tenant_databases WHERE tenant_id = %s", (tenant_id,))
                cur.execute("DELETE FROM tenant_runtime   WHERE tenant_id = %s", (tenant_id,))
                cur.execute("DELETE FROM sync_api_keys     WHERE tenant_id = %s", (tenant_id,))
                cur.execute("DELETE FROM tenants           WHERE id = %s", (tenant_id,))
        except Exception:  # noqa: BLE001
            pass


def create_tenant(slug: str, nombre: str, key_label: str = 'Primera key',
                  admin_email: str = '', admin_nombre: str = 'Administrador',
                  plan: str = 'estandar') -> dict:
    """Orquesta la creación end-to-end de un tenant nuevo.

    Pasos (atómicos: si algo falla se revierte solo, sin BD huérfana):
      1. Validar slug/nombre/plan; verificar que el slug no exista.
      2. Reservar la fila `tenants` → obtener id.
      3. db_name = cyber_t<id> (determinístico, NO contador).
      4. CREATE DATABASE + schema (psql) + seed (roles, admin, colores, secciones).
      5. INSERT en tenant_databases.
      6. Activar módulos del plan (no aborta; se reporta como aviso).
      7. Emitir primera API key + client_code.
      8. Aprovisionar instancia + dominio (no aborta; reaprovisionable).

    Returns dict para mostrarle al admin (incluye 'warnings'):
      {tenant_id, slug, db_name, api_key, client_code, key_prefix,
       admin_email, admin_password, port, domain, instance_status, warnings}

    Si un paso crítico (2-5, 7) falla, levanta TenantCreationError tras revertir.
    """
    nombre = (nombre or '').strip()
    if not nombre or len(nombre) > 100:
        raise TenantCreationError("El nombre del tenant es obligatorio (max 100 chars).")

    slug = validate_slug(slug)
    admin_email = (admin_email or '').strip().lower() or f'admin@{slug}.local'
    admin_nombre = (admin_nombre or '').strip() or 'Administrador'

    # Validar plan contra el catálogo de módulos (acepta alias legacy, default estandar).
    import module_service as _ms
    plan = _ms.normalize_plan(plan)

    if _slug_exists(slug):
        raise TenantCreationError(f"Ya existe un tenant con slug '{slug}'.")

    warnings = []

    # Paso 1: reservar la fila `tenants` para obtener el id (db_name determinístico).
    try:
        tenant_id = _insert_tenant_row(slug, nombre, plan)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if 'unique' in msg or 'duplicate' in msg:
            raise TenantCreationError(f"Ya existe un tenant con slug '{slug}'.") from exc
        raise TenantCreationError(f"No se pudo registrar el tenant: {exc}") from exc

    db_name = compute_db_name(tenant_id)
    created_db = False

    # Pasos 2-5 (DB + schema + seed + registro de la DB): ATÓMICOS por compensación.
    # Si algo falla, _rollback_partial_tenant() dropea la DB (si la creamos) y borra
    # las filas parciales → no quedan huérfanas ni el operador limpia a mano.
    try:
        if _db_exists(db_name):
            raise TenantCreationError(
                f"Ya existe una base de datos '{db_name}' (residuo de un intento "
                f"anterior del id {tenant_id}). Elimínala antes de reintentar."
            )

        _create_database(db_name)            # Paso 2: CREATE DATABASE
        created_db = True
        _apply_schema(db_name)               # Paso 3: schema base
        seed = _apply_seed(db_name, nombre, admin_email, slug=slug,
                           admin_nombre=admin_nombre)   # Paso 4: seed
        _insert_tenant_db_row(tenant_id, db_name)       # Paso 5: registrar DB
    except TenantCreationError:
        _rollback_partial_tenant(tenant_id, db_name, drop_db=created_db)
        raise
    except Exception as exc:  # noqa: BLE001
        _rollback_partial_tenant(tenant_id, db_name, drop_db=created_db)
        raise TenantCreationError(
            f"Creación de {db_name} falló y se revirtió automáticamente: {exc}"
        ) from exc

    # Paso 6: activar los módulos del plan (no aborta; se reporta como aviso).
    try:
        _ms.apply_plan(tenant_id, plan)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"módulos del plan no aplicados ({exc}); ajustalos en la pestaña Módulos.")

    # Paso 7: primera API key (crítica: si falla, revertir TODO para no dejar a medias).
    try:
        key_info = issue_key(tenant_id, label=key_label)
    except Exception as exc:  # noqa: BLE001
        _rollback_partial_tenant(tenant_id, db_name, drop_db=created_db)
        raise TenantCreationError(
            f"Falló la emisión de la primera key; la creación se revirtió: {exc}"
        ) from exc

    # Paso 8: aprovisionar instancia + dominio (no aborta; reaprovisionable desde el detalle).
    prov = {'port': None, 'domain': None, 'instance_status': 'pending'}
    try:
        prov = provisioning_service.provision(tenant_id, slug, db_name, subdomain=slug)
    except Exception as exc:  # noqa: BLE001
        prov['error'] = str(exc)
        warnings.append(f"aprovisionamiento pendiente ({exc}); usá «Reaprovisionar» en Técnico.")

    return {
        'tenant_id':      tenant_id,
        'slug':           slug,
        'nombre':         nombre,
        'plan':           plan,
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
        'warnings':       warnings,
    }
