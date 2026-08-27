"""Bitácora inmutable de acciones sensibles (control plane) — DAT-01.

Aditivo y best-effort: registrar() NUNCA rompe la acción que audita (si la BD de
auditoría falla, la acción original sigue). Tabla append-only (sin UPDATE/DELETE
desde el código); útil para responder "¿quién/qué suspendió al tenant X y cuándo?".
"""
from db import control_plane_cursor

_ENSURED = False


def _ensure():
    global _ENSURED
    if _ENSURED:
        return
    with control_plane_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auditoria_acciones (
                id        BIGSERIAL PRIMARY KEY,
                ts        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                accion    VARCHAR(60) NOT NULL,
                tenant_id INT,
                actor     VARCHAR(120),
                detalle   TEXT
            )""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_tenant_ts "
                    "ON auditoria_acciones (tenant_id, ts DESC)")
    _ENSURED = True


def registrar(accion, tenant_id=None, actor=None, detalle=None):
    """Registra una acción sensible. Best-effort: no propaga errores."""
    try:
        _ensure()
        with control_plane_cursor() as cur:
            cur.execute(
                "INSERT INTO auditoria_acciones (accion, tenant_id, actor, detalle) "
                "VALUES (%s, %s, %s, %s)",
                (str(accion)[:60], tenant_id, (str(actor) if actor else 'sistema')[:120],
                 (str(detalle)[:2000] if detalle is not None else None)),
            )
    except Exception:  # noqa: BLE001 — la auditoría nunca rompe la acción auditada
        pass


def listar(tenant_id=None, limite=200):
    """Últimas acciones (global o por tenant), más recientes primero."""
    _ensure()
    with control_plane_cursor(dict_cursor=True) as cur:
        if tenant_id is not None:
            cur.execute("SELECT id, ts, accion, tenant_id, actor, detalle FROM auditoria_acciones "
                        "WHERE tenant_id = %s ORDER BY ts DESC, id DESC LIMIT %s", (tenant_id, limite))
        else:
            cur.execute("SELECT id, ts, accion, tenant_id, actor, detalle FROM auditoria_acciones "
                        "ORDER BY ts DESC, id DESC LIMIT %s", (limite,))
        return cur.fetchall()


def listar_con_slug(limite=200):
    """Vista global con el slug del tenant (para la página /auditoria)."""
    _ensure()
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT a.id, a.ts, a.accion, a.tenant_id, a.actor, a.detalle, t.slug
            FROM auditoria_acciones a
            LEFT JOIN tenants t ON t.id = a.tenant_id
            ORDER BY a.ts DESC, a.id DESC LIMIT %s""", (limite,))
        return cur.fetchall()
