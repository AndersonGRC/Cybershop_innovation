"""Cobros / mora por tenant (control plane).

Tablas: tenant_billing (config mensual) + tenant_pagos (historial).
Reutiliza lifecycle_service.suspend para apagar morosos. El tenant marcado con
auto_suspender=FALSE (p.ej. el 1, el del operador) nunca se suspende solo.
"""

import calendar
import datetime

from db import control_plane_cursor

# Tras 2 meses de mora se suspende (configurable).
MORA_DIAS_SUSPENSION = 60


# ── utilidades de fecha ────────────────────────────────────────
def _add_months(d: datetime.date, n: int = 1) -> datetime.date:
    """Suma n meses a una fecha, ajustando el día al último del mes si hace falta."""
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def _today() -> datetime.date:
    return datetime.date.today()


def _parse_date(v):
    if not v:
        return None
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.datetime.strptime(str(v).strip(), '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


# ── tabla defensiva (si la migración aún no corrió) ────────────
def _ensure_tables():
    with control_plane_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenant_billing (
                tenant_id INT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                monto_mensual NUMERIC(12,2) NOT NULL DEFAULT 0,
                proxima_fecha DATE,
                auto_suspender BOOLEAN NOT NULL DEFAULT TRUE,
                notas TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenant_pagos (
                id SERIAL PRIMARY KEY,
                tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                monto NUMERIC(12,2) NOT NULL,
                fecha DATE NOT NULL DEFAULT CURRENT_DATE,
                metodo VARCHAR(40), nota TEXT, cubre_hasta DATE,
                registrado_por VARCHAR(120),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""")


# ── estado de pago ─────────────────────────────────────────────
def _estado(proxima_fecha):
    """('al_dia'|'en_mora'|'sin_config', dias) — dias>0 vencidos en mora; dias>=0 restantes al día."""
    if not proxima_fecha:
        return 'sin_config', 0
    hoy = _today()
    if hoy <= proxima_fecha:
        return 'al_dia', (proxima_fecha - hoy).days
    return 'en_mora', (hoy - proxima_fecha).days


# ── lectura ────────────────────────────────────────────────────
def get_billing(tenant_id: int) -> dict:
    _ensure_tables()
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT * FROM tenant_billing WHERE tenant_id = %s", (tenant_id,))
        row = cur.fetchone()
        cur.execute(
            "SELECT id, monto, fecha, metodo, nota, cubre_hasta, registrado_por "
            "FROM tenant_pagos WHERE tenant_id = %s ORDER BY fecha DESC, id DESC LIMIT 24",
            (tenant_id,))
        historial = cur.fetchall()

    monto = float(row['monto_mensual']) if row else 0.0
    proxima = row['proxima_fecha'] if row else None
    auto = bool(row['auto_suspender']) if row else True
    estado, dias = _estado(proxima)
    return {
        'configurado': bool(row),
        'monto_mensual': monto,
        'proxima_fecha': proxima,
        'auto_suspender': auto,
        'notas': (row['notas'] if row else '') or '',
        'estado': estado,
        'dias': dias,
        'en_mora': estado == 'en_mora',
        'umbral_suspension': MORA_DIAS_SUSPENSION,
        'a_suspension': max(0, MORA_DIAS_SUSPENSION - dias) if estado == 'en_mora' else None,
        'ultimo_pago': historial[0] if historial else None,
        'historial': historial,
        'motor': get_motor_info(tenant_id),
    }


def get_motor_info(tenant_id: int):
    """Estado del MOTOR de cobro automático (tabla plan_compras en la BD del
    tenant operador, id=1): próximo pago, último recordatorio, si es prueba
    gratis y el LINK de renovación/pago para compartir por WhatsApp.
    None si el tenant no está en el motor (o el motor no responde)."""
    try:
        from db import get_tenant_conn, control_plane_cursor
        with control_plane_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT db_name FROM tenant_databases WHERE tenant_id = 1")
            fila = cur.fetchone()
        if not fila:
            return None
        conn = get_tenant_conn(fila['db_name'])
        try:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT plan_key, proximo_pago, ultimo_recordatorio, es_trial, "
                    "       suspendida_por_pago, token_renovacion, buyer_email "
                    "FROM plan_compras WHERE tenant_id = %s AND estado = 'ACTIVADA' "
                    "ORDER BY id DESC LIMIT 1",
                    (tenant_id,))
                m = cur.fetchone()
        finally:
            conn.close()
        if not m:
            return None
        return {
            'plan_key': m['plan_key'],
            'proximo_pago': m['proximo_pago'],
            'ultimo_recordatorio': m['ultimo_recordatorio'],
            'es_trial': bool(m.get('es_trial')),
            'suspendida_por_pago': bool(m['suspendida_por_pago']),
            'buyer_email': m['buyer_email'],
            'link_pago': (f"https://cybershopcol.com/renovar/{m['token_renovacion']}"
                          if m['token_renovacion'] else None),
        }
    except Exception:
        return None


# ── escritura ──────────────────────────────────────────────────
def set_config(tenant_id, monto_mensual=None, proxima_fecha=None, auto_suspender=None, notas=None):
    """Upsert de la configuración de cobro (solo toca lo que no es None)."""
    _ensure_tables()
    monto = None
    if monto_mensual is not None and str(monto_mensual).strip() != '':
        try:
            monto = float(str(monto_mensual).replace(',', '').replace('$', '').strip())
        except ValueError:
            monto = None
    pf = _parse_date(proxima_fecha) if proxima_fecha is not None else None
    with control_plane_cursor() as cur:
        cur.execute("SELECT 1 FROM tenant_billing WHERE tenant_id = %s", (tenant_id,))
        existe = cur.fetchone() is not None
        if not existe:
            cur.execute(
                "INSERT INTO tenant_billing (tenant_id, monto_mensual, proxima_fecha, auto_suspender, notas) "
                "VALUES (%s, COALESCE(%s,0), %s, COALESCE(%s,TRUE), %s)",
                (tenant_id, monto, pf, auto_suspender, notas))
            return
        sets, params = [], []
        if monto is not None:
            sets.append("monto_mensual = %s"); params.append(monto)
        if proxima_fecha is not None:
            sets.append("proxima_fecha = %s"); params.append(pf)
        if auto_suspender is not None:
            sets.append("auto_suspender = %s"); params.append(bool(auto_suspender))
        if notas is not None:
            sets.append("notas = %s"); params.append(notas)
        if not sets:
            return
        sets.append("updated_at = NOW()")
        params.append(tenant_id)
        cur.execute(f"UPDATE tenant_billing SET {', '.join(sets)} WHERE tenant_id = %s", params)


def registrar_pago(tenant_id, monto, fecha=None, metodo=None, nota=None, registrado_por=None):
    """Registra un pago y avanza el próximo vencimiento +1 mes.

    Base del avance: el vencimiento vigente si aún no venció (prepago), o la fecha
    del pago si ya estaba en mora / sin fecha.
    """
    _ensure_tables()
    fecha = _parse_date(fecha) or _today()
    try:
        monto_f = float(str(monto).replace(',', '').replace('$', '').strip())
    except (TypeError, ValueError):
        raise ValueError("Monto inválido")

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT b.proxima_fecha, t.estado "
            "FROM tenants t LEFT JOIN tenant_billing b ON b.tenant_id = t.id "
            "WHERE t.id = %s", (tenant_id,))
        row = cur.fetchone()
        proxima = row['proxima_fecha'] if row else None
        estado_actual = row['estado'] if row else None
        tiene_billing = bool(row and proxima is not None) or _billing_existe(cur, tenant_id)

        base = proxima if (proxima and proxima > fecha) else fecha
        nueva = _add_months(base, 1)

        cur.execute(
            "INSERT INTO tenant_pagos (tenant_id, monto, fecha, metodo, nota, cubre_hasta, registrado_por) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (tenant_id, monto_f, fecha, metodo, nota, nueva, registrado_por))
        if tiene_billing:
            cur.execute("UPDATE tenant_billing SET proxima_fecha = %s, updated_at = NOW() WHERE tenant_id = %s",
                        (nueva, tenant_id))
        else:
            cur.execute("INSERT INTO tenant_billing (tenant_id, proxima_fecha) VALUES (%s,%s)",
                        (tenant_id, nueva))

    # Si estaba suspendido y el pago lo deja al día, reactivar el cliente.
    if estado_actual == 'suspendido' and nueva >= _today():
        try:
            import lifecycle_service
            lifecycle_service.reactivate(tenant_id)
        except Exception:  # noqa: BLE001
            pass
    return nueva


def _billing_existe(cur, tenant_id):
    cur.execute("SELECT 1 FROM tenant_billing WHERE tenant_id = %s", (tenant_id,))
    return cur.fetchone() is not None


def extender_plazo(tenant_id, dias=None, nueva_fecha=None):
    """Empuja el vencimiento sin registrar pago (más plazo)."""
    _ensure_tables()
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT proxima_fecha FROM tenant_billing WHERE tenant_id = %s", (tenant_id,))
        row = cur.fetchone()
        actual = (row['proxima_fecha'] if row else None) or _today()
        if nueva_fecha:
            destino = _parse_date(nueva_fecha)
        else:
            try:
                destino = actual + datetime.timedelta(days=int(dias))
            except (TypeError, ValueError):
                raise ValueError("Días inválidos")
        if not destino:
            raise ValueError("Fecha inválida")
        if row:
            cur.execute("UPDATE tenant_billing SET proxima_fecha = %s, updated_at = NOW() WHERE tenant_id = %s",
                        (destino, tenant_id))
        else:
            cur.execute("INSERT INTO tenant_billing (tenant_id, proxima_fecha) VALUES (%s,%s)",
                        (tenant_id, destino))
    return destino


# ── morosos / auto-suspensión ─────────────────────────────────
def morosos(dias=MORA_DIAS_SUSPENSION):
    """Tenants ACTIVOS, con auto_suspender=TRUE y +`dias` de mora."""
    _ensure_tables()
    limite = _today() - datetime.timedelta(days=dias)
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT t.id, t.slug, t.nombre, b.proxima_fecha,
                   (CURRENT_DATE - b.proxima_fecha) AS dias_mora
            FROM tenant_billing b
            JOIN tenants t ON t.id = b.tenant_id
            WHERE b.auto_suspender = TRUE
              AND b.proxima_fecha IS NOT NULL
              AND b.proxima_fecha < %s
              AND t.estado = 'activo'
            ORDER BY b.proxima_fecha ASC
        """, (limite,))
        return cur.fetchall()


def revisar_y_suspender(dias=MORA_DIAS_SUSPENSION, por='cron'):
    """Suspende a los morosos elegibles. Devuelve la lista suspendida."""
    import lifecycle_service
    pendientes = morosos(dias)
    suspendidos = []
    for m in pendientes:
        try:
            lifecycle_service.suspend(m['id'])
            suspendidos.append(m)
        except Exception:  # noqa: BLE001 — no abortar el lote por uno
            continue
    return suspendidos
