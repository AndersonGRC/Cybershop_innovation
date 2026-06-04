"""Migraciones ADITIVAS para las BDs de los clientes (tenants).

Permite actualizar el esquema de TODOS los clientes existentes sin afectar sus
datos: cada archivo `migrations/tenant/*.sql` debe ser idempotente y aditivo
(`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`,
`CREATE INDEX IF NOT EXISTS`). Nunca DROP/ALTER destructivo.

Cada BD de tenant lleva una tabla `tenant_schema_migrations` con lo aplicado,
así re-correr es seguro (se saltan las ya aplicadas). Como las migraciones son
idempotentes, aplicarlas a un cliente nuevo (que ya tiene todo por el dump del
schema) tampoco rompe nada.
"""

from pathlib import Path

from db import control_plane_cursor, get_tenant_conn


TENANT_MIGRATIONS_DIR = Path(__file__).parent / 'migrations' / 'tenant'


def _files():
    if not TENANT_MIGRATIONS_DIR.is_dir():
        return []
    return sorted(TENANT_MIGRATIONS_DIR.glob('*.sql'))


def _ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_schema_migrations (
            filename   TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def _applied(cur):
    _ensure_table(cur)
    cur.execute("SELECT filename FROM tenant_schema_migrations")
    return {r[0] for r in cur.fetchall()}


def list_tenant_dbs():
    """Tenants con BD viva (excluye cancelados, cuya BD pudo ser borrada)."""
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            """
            SELECT t.id, t.slug, t.estado, td.db_name
            FROM tenants t JOIN tenant_databases td ON td.tenant_id = t.id
            WHERE t.estado <> 'cancelado'
            ORDER BY t.id
            """
        )
        return cur.fetchall()


def mark_all_applied(conn):
    """Marca TODAS las migraciones actuales como aplicadas (para clientes nuevos
    cuyo dump del schema ya las incluye)."""
    cur = conn.cursor()
    _ensure_table(cur)
    for f in _files():
        cur.execute(
            "INSERT INTO tenant_schema_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING",
            (f.name,),
        )
    conn.commit()


def pending_for(db_name):
    conn = get_tenant_conn(db_name)
    try:
        cur = conn.cursor()
        done = _applied(cur)
        return [f.name for f in _files() if f.name not in done]
    finally:
        conn.close()


def migrate_db(db_name, dry_run=False):
    """Aplica las migraciones pendientes a una BD de tenant. Devuelve la lista
    de archivos aplicados."""
    conn = get_tenant_conn(db_name)
    applied = []
    try:
        cur = conn.cursor()
        done = _applied(cur)
        for f in _files():
            if f.name in done:
                continue
            if not dry_run:
                cur.execute(f.read_text(encoding='utf-8'))
                cur.execute(
                    "INSERT INTO tenant_schema_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING",
                    (f.name,),
                )
                conn.commit()
            applied.append(f.name)
    finally:
        conn.close()
    return applied


def migrate_all(dry_run=False, only_slug=None):
    """Aplica migraciones pendientes a todos los tenants (o uno). Devuelve
    {slug: [archivos] | 'ERROR: ...'}."""
    results = {}
    for t in list_tenant_dbs():
        if only_slug and t['slug'] != only_slug:
            continue
        try:
            results[t['slug']] = migrate_db(t['db_name'], dry_run=dry_run)
        except Exception as exc:  # noqa: BLE001
            results[t['slug']] = f"ERROR: {exc}"
    return results
