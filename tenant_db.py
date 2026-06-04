"""Acceso a la BD de un tenant desde el maestro.

Resuelve el db_name del tenant (control plane) y abre conexión a su
`cyber_tNNN`. Reusa `db.get_tenant_conn`. Patrón espejo de
CyberShop/app/services/db_layer.tenant_cursor.
"""

from contextlib import contextmanager

from psycopg2.extras import DictCursor

from db import control_plane_cursor, get_tenant_conn


LOCAL_TENANT_ID = 1  # id local dentro de la BD del tenant (lo que usa el app)


def resolve_db_name(tenant_id: int) -> str:
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT db_name FROM tenant_databases WHERE tenant_id = %s",
            (tenant_id,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"El tenant {tenant_id} no tiene tenant_databases.")
    return row['db_name']


@contextmanager
def tenant_cursor(tenant_id: int, dict_cursor: bool = True):
    """Cursor sobre la BD del tenant con commit/rollback automáticos."""
    db_name = resolve_db_name(tenant_id)
    conn = get_tenant_conn(db_name)
    factory = DictCursor if dict_cursor else None
    cur = conn.cursor(cursor_factory=factory)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
