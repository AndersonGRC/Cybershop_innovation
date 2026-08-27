"""Cobros / mora por tenant (control plane).

Tablas: tenant_billing (config mensual) + tenant_pagos (historial).
Reutiliza lifecycle_service.suspend para apagar morosos. El tenant marcado con
auto_suspender=FALSE (p.ej. el 1, el del operador) nunca se suspende solo.
"""

import calendar
import datetime

from db import control_plane_cursor
import audit_service

# Backstop del control plane: sin días por cliente, se suspende a los 60 días.
MORA_DIAS_SUSPENSION = 60
# Plazo por defecto (días tras el vencimiento) cuando el operador NO fijó uno por
# cliente Y el cliente está en el motor de cobro automático. El operador puede
# sobrescribirlo por cliente con tenant_billing.dias_suspension.
DIAS_SUSPENSION_DEFAULT = 30


def _parse_dias(v):
    """Días de plazo -> int>=0 o None (vacío = usar el default)."""
    if v is None:
        return None
    s = str(v).strip()
    if s == '':
        return None
    try:
        return max(0, int(float(s)))
    except ValueError:
        return None


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
        # Aditivo: silenciar (por tenant) el pop-up de "plan por vencer" del cliente.
        cur.execute("ALTER TABLE tenant_billing "
                    "ADD COLUMN IF NOT EXISTS avisos_off BOOLEAN NOT NULL DEFAULT FALSE")
        # Aditivo: días de plazo (por cliente) antes de la suspensión automática.
        # NULL = usar el default (DIAS_SUSPENSION_DEFAULT / MORA_DIAS_SUSPENSION).
        cur.execute("ALTER TABLE tenant_billing "
                    "ADD COLUMN IF NOT EXISTS dias_suspension INT")
        # Aditivo: forzar mostrar el aviso (modo manual "mostrar siempre", aunque
        # el plan esté al día). Junto con avisos_off define el modo del aviso.
        cur.execute("ALTER TABLE tenant_billing "
                    "ADD COLUMN IF NOT EXISTS aviso_forzar BOOLEAN NOT NULL DEFAULT FALSE")
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
    avisos_off = bool(row.get('avisos_off')) if row else False
    aviso_forzar = bool(row.get('aviso_forzar')) if row else False
    aviso_modo = 'silenciar' if avisos_off else ('forzar' if aviso_forzar else 'auto')
    dias_susp = row.get('dias_suspension') if row else None
    estado, dias = _estado(proxima)
    motor = get_motor_info(tenant_id)
    # Umbral efectivo: si el operador fijó días por cliente, mandan; si no, 30 para
    # clientes en el motor (suspensión automática rápida) o el backstop de 60.
    default_grace = DIAS_SUSPENSION_DEFAULT if motor is not None else MORA_DIAS_SUSPENSION
    umbral = int(dias_susp) if dias_susp is not None else default_grace
    return {
        'configurado': bool(row),
        'monto_mensual': monto,
        'proxima_fecha': proxima,
        'auto_suspender': auto,
        'avisos_off': avisos_off,
        'aviso_forzar': aviso_forzar,
        'aviso_modo': aviso_modo,
        'dias_suspension': int(dias_susp) if dias_susp is not None else None,
        'notas': (row['notas'] if row else '') or '',
        'estado': estado,
        'dias': dias,
        'en_mora': estado == 'en_mora',
        'umbral_suspension': umbral,
        'a_suspension': max(0, umbral - dias) if estado == 'en_mora' else None,
        'ultimo_pago': historial[0] if historial else None,
        'historial': historial,
        'motor': motor,
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
def set_config(tenant_id, monto_mensual=None, proxima_fecha=None, auto_suspender=None,
               notas=None, avisos_off=None, dias_suspension=None):
    """Upsert de la configuración de cobro (solo toca lo que no es None).
    `dias_suspension` vacío ('') => NULL (usar el default)."""
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
                "INSERT INTO tenant_billing (tenant_id, monto_mensual, proxima_fecha, auto_suspender, notas, dias_suspension) "
                "VALUES (%s, COALESCE(%s,0), %s, COALESCE(%s,TRUE), %s, %s)",
                (tenant_id, monto, pf, auto_suspender, notas, _parse_dias(dias_suspension)))
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
        if avisos_off is not None:
            sets.append("avisos_off = %s"); params.append(bool(avisos_off))
        if dias_suspension is not None:
            sets.append("dias_suspension = %s"); params.append(_parse_dias(dias_suspension))
        if not sets:
            return
        sets.append("updated_at = NOW()")
        params.append(tenant_id)
        cur.execute(f"UPDATE tenant_billing SET {', '.join(sets)} WHERE tenant_id = %s", params)


def set_aviso_modo(tenant_id: int, modo: str) -> str:
    """Fija el modo del aviso de vencimiento en el panel del cliente:
      - 'auto'     : se muestra solo a 3 días de vencer o en mora (default).
      - 'forzar'   : se muestra SIEMPRE (activación manual, aunque esté al día).
      - 'silenciar': nunca se muestra.
    Se mapea a avisos_off + aviso_forzar. Devuelve el modo aplicado."""
    _ensure_tables()
    if modo not in ('auto', 'forzar', 'silenciar'):
        modo = 'auto'
    off = (modo == 'silenciar')
    forzar = (modo == 'forzar')
    with control_plane_cursor() as cur:
        cur.execute("SELECT 1 FROM tenant_billing WHERE tenant_id = %s", (tenant_id,))
        if cur.fetchone():
            cur.execute("UPDATE tenant_billing SET avisos_off = %s, aviso_forzar = %s, "
                        "updated_at = NOW() WHERE tenant_id = %s", (off, forzar, tenant_id))
        else:
            cur.execute("INSERT INTO tenant_billing (tenant_id, avisos_off, aviso_forzar) "
                        "VALUES (%s, %s, %s)", (tenant_id, off, forzar))
    audit_service.registrar('aviso_modo', tenant_id, actor='fADMIN', detalle=f"modo={modo}")
    return modo


def sync_billing_to_tenant(tenant_id: int) -> bool:
    """Sincroniza al `cliente_config` del tenant las claves que su app usa para
    el pop-up de "plan por vencer": `plan_vence` (fecha ISO o '') y
    `plan_avisos_off` ('true'/'false'). UPDATE→INSERT (cliente_config puede no
    tener índice único en 'clave'). Best-effort: no rompe si el tenant no existe."""
    b = get_billing(tenant_id)
    vence = b['proxima_fecha'].isoformat() if b.get('proxima_fecha') else ''
    avisos_off = 'true' if b.get('avisos_off') else 'false'
    aviso_forzar = 'true' if b.get('aviso_forzar') else 'false'
    try:
        from db import get_tenant_conn, control_plane_cursor
        with control_plane_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT db_name FROM tenant_databases WHERE tenant_id = %s", (tenant_id,))
            row = cur.fetchone()
        if not row:
            return False
        conn = get_tenant_conn(row['db_name'])
        try:
            cur = conn.cursor()
            for clave, valor in (('plan_vence', vence), ('plan_avisos_off', avisos_off),
                                 ('plan_aviso_forzar', aviso_forzar)):
                cur.execute("UPDATE cliente_config SET valor = %s WHERE clave = %s", (valor, clave))
                if cur.rowcount == 0:
                    cur.execute(
                        "INSERT INTO cliente_config (clave, valor, tipo, grupo) "
                        "VALUES (%s, %s, 'text', 'facturacion')", (clave, valor))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:  # noqa: BLE001
        return False


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
            lifecycle_service.reactivate(tenant_id, actor='pago')
        except Exception:  # noqa: BLE001
            pass
    audit_service.registrar('pago', tenant_id, actor=(registrado_por or 'fADMIN'),
                            detalle=f"monto={monto_f} cubre_hasta={nueva}")
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
def morosos(dias=None):
    """Tenants ACTIVOS, con auto_suspender=TRUE y suficiente mora para suspender.
    `dias=None` (default) usa el plazo POR CLIENTE (tenant_billing.dias_suspension)
    con fallback al backstop de 60. Si se pasa `dias`, se aplica ese umbral fijo a
    todos (compatibilidad)."""
    _ensure_tables()
    with control_plane_cursor(dict_cursor=True) as cur:
        if dias is None:
            cur.execute("""
                SELECT t.id, t.slug, t.nombre, b.proxima_fecha,
                       (CURRENT_DATE - b.proxima_fecha) AS dias_mora,
                       COALESCE(b.dias_suspension, %s) AS umbral
                FROM tenant_billing b
                JOIN tenants t ON t.id = b.tenant_id
                WHERE b.auto_suspender = TRUE
                  AND b.proxima_fecha IS NOT NULL
                  AND t.estado = 'activo'
                  AND (CURRENT_DATE - b.proxima_fecha) >= COALESCE(b.dias_suspension, %s)
                ORDER BY b.proxima_fecha ASC
            """, (MORA_DIAS_SUSPENSION, MORA_DIAS_SUSPENSION))
        else:
            limite = _today() - datetime.timedelta(days=dias)
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


def revisar_y_suspender(dias=None, por='cron'):
    """Suspende a los morosos elegibles. Devuelve la lista suspendida."""
    import lifecycle_service
    pendientes = morosos(dias)
    suspendidos = []
    for m in pendientes:
        try:
            lifecycle_service.suspend(m['id'], actor=f'morosos:{por}')
            suspendidos.append(m)
        except Exception:  # noqa: BLE001 — no abortar el lote por uno
            continue
    return suspendidos
