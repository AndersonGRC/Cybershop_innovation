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


# ── Fecha de corte: el día de pago del cliente NO cambia ───────
# Si vence el 18 y paga el 7 del mes siguiente, el pago cubre su mes (del 18 al
# 18) y el próximo vence otra vez el 18. Antes, un pago tarde contaba el mes
# desde el día del pago y el día de cobro se corría cada vez.
def _con_dia(anio: int, mes: int, dia: int) -> datetime.date:
    """El día de corte en ese mes (el 31 en febrero es el 28 o 29)."""
    return datetime.date(anio, mes, min(int(dia), calendar.monthrange(anio, mes)[1]))


def _sumar_ciclos(d: datetime.date, meses: int, dia: int) -> datetime.date:
    """La fecha de corte `meses` meses después (o antes, si es negativo)."""
    m = d.month - 1 + meses
    return _con_dia(d.year + m // 12, m % 12 + 1, dia)


def corte_del_ciclo(proxima: datetime.date, dia: int) -> datetime.date:
    """Fecha de corte del ciclo que vence en `proxima`: el día de corte de ese
    mes si ya llegó, o el del mes anterior. Así una prórroga («Dar más plazo»)
    no corre el día de pago: el pago sigue cubriendo el mes desde el corte."""
    corte = _con_dia(proxima.year, proxima.month, dia)
    if corte > proxima:
        corte = _sumar_ciclos(corte, -1, dia)
    return corte


def proximo_vencimiento(proxima, dia_corte, fecha_pago, meses=1):
    """(nuevo vencimiento, día de corte) después de un pago de `meses` meses.

    Con vencimiento vigente, cuenta desde la fecha de corte del ciclo, pague
    tarde, a tiempo o por adelantado. Sin vencimiento (primer pago) el período
    arranca el día del pago y ese pasa a ser el día de corte."""
    if proxima:
        dia = int(dia_corte or proxima.day)
        return _sumar_ciclos(corte_del_ciclo(proxima, dia), meses, dia), dia
    return _sumar_ciclos(fecha_pago, meses, fecha_pago.day), fecha_pago.day


def _parse_meses(v) -> int:
    try:
        meses = int(str(v).strip()) if v not in (None, '') else 1
    except ValueError:
        raise ValueError("Meses inválidos")
    if not 1 <= meses <= 12:
        raise ValueError("Un pago cubre de 1 a 12 meses")
    return meses


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
        # Aditivo: día del mes en que vence el cliente (su fecha de corte). NULL =
        # el día de proxima_fecha. Lo fija el operador al corregir el vencimiento.
        cur.execute("ALTER TABLE tenant_billing "
                    "ADD COLUMN IF NOT EXISTS dia_corte SMALLINT")
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
    dia_corte = (row.get('dia_corte') if row else None) or (proxima.day if proxima else None)
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
        'dia_corte': dia_corte,
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


def _whatsapp_url(telefono):
    digitos = ''.join(ch for ch in str(telefono or '') if ch.isdigit())
    if len(digitos) == 10:
        digitos = '57' + digitos
    return f'https://wa.me/{digitos}' if len(digitos) >= 11 else None


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
                    "       suspendida_por_pago, token_renovacion, buyer_email, "
                    "       buyer_telefono, buyer_nombre "
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
            'buyer_telefono': m.get('buyer_telefono') or '',
            'buyer_nombre': m.get('buyer_nombre') or '',
            'whatsapp_url': _whatsapp_url(m.get('buyer_telefono')),
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
    corregida = False
    with control_plane_cursor() as cur:
        cur.execute("SELECT proxima_fecha FROM tenant_billing WHERE tenant_id = %s", (tenant_id,))
        fila = cur.fetchone()
        existe = fila is not None
        if not existe:
            cur.execute(
                "INSERT INTO tenant_billing (tenant_id, monto_mensual, proxima_fecha, auto_suspender, notas, "
                "dias_suspension, dia_corte) "
                "VALUES (%s, COALESCE(%s,0), %s, COALESCE(%s,TRUE), %s, %s, %s)",
                (tenant_id, monto, pf, auto_suspender, notas, _parse_dias(dias_suspension),
                 pf.day if pf else None))
            corregida = pf is not None
        else:
            corregida = proxima_fecha is not None and pf != fila[0]
    if not existe:
        if corregida:
            _sincronizar_motor(tenant_id, pf, forzar=True)
        return
    with control_plane_cursor() as cur:
        sets, params = [], []
        if monto is not None:
            sets.append("monto_mensual = %s"); params.append(monto)
        if proxima_fecha is not None:
            sets.append("proxima_fecha = %s"); params.append(pf)
        if corregida:
            # El operador corrigió el vencimiento: ese día pasa a ser su día de pago.
            sets.append("dia_corte = %s"); params.append(pf.day if pf else None)
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
    if corregida and pf:
        audit_service.registrar('vencimiento_corregido', tenant_id, actor='fADMIN',
                                detalle=f"proxima_fecha={pf} dia_corte={pf.day}")
        # Corrección explícita: el motor (recordatorios) toma la misma fecha.
        _sincronizar_motor(tenant_id, pf, forzar=True)


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


def registrar_pago(tenant_id, monto, fecha=None, metodo=None, nota=None, registrado_por=None, meses=1):
    """Registra un pago de `meses` meses y corre el vencimiento DESDE SU FECHA DE
    CORTE: el día de pago del cliente no cambia aunque pague tarde o antes
    (ver `proximo_vencimiento`). Si el pago no alcanza a cubrir hasta hoy, el
    cliente sigue en mora (debe más meses). Devuelve el nuevo vencimiento."""
    _ensure_tables()
    fecha = _parse_date(fecha) or _today()
    meses = _parse_meses(meses)
    try:
        monto_f = float(str(monto).replace(',', '').replace('$', '').strip())
    except (TypeError, ValueError):
        raise ValueError("Monto inválido")

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT b.proxima_fecha, b.dia_corte, t.estado "
            "FROM tenants t LEFT JOIN tenant_billing b ON b.tenant_id = t.id "
            "WHERE t.id = %s", (tenant_id,))
        row = cur.fetchone()
        proxima = row['proxima_fecha'] if row else None
        estado_actual = row['estado'] if row else None
        tiene_billing = bool(row and proxima is not None) or _billing_existe(cur, tenant_id)

        nueva, dia = proximo_vencimiento(proxima, row['dia_corte'] if row else None, fecha, meses)

        cur.execute(
            "INSERT INTO tenant_pagos (tenant_id, monto, fecha, metodo, nota, cubre_hasta, registrado_por) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (tenant_id, monto_f, fecha, metodo, nota, nueva, registrado_por))
        if tiene_billing:
            cur.execute("UPDATE tenant_billing SET proxima_fecha = %s, dia_corte = COALESCE(dia_corte, %s), "
                        "updated_at = NOW() WHERE tenant_id = %s", (nueva, dia, tenant_id))
        else:
            cur.execute("INSERT INTO tenant_billing (tenant_id, proxima_fecha, dia_corte) VALUES (%s,%s,%s)",
                        (tenant_id, nueva, dia))

    # Si estaba suspendido y el pago lo deja al día, reactivar el cliente.
    if estado_actual == 'suspendido' and nueva >= _today():
        try:
            import lifecycle_service
            lifecycle_service.reactivate(tenant_id, actor='pago')
        except Exception:  # noqa: BLE001
            pass
    audit_service.registrar('pago', tenant_id, actor=(registrado_por or 'fADMIN'),
                            detalle=f"monto={monto_f} meses={meses} cubre_hasta={nueva} dia_corte={dia}")
    # Los recordatorios del motor usan la misma fecha desde ya (no esperan al cron).
    _sincronizar_motor(tenant_id, nueva, pago=True)
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
    # Prórroga: el día de pago (dia_corte) no cambia; el motor no avisa antes de tiempo.
    _sincronizar_motor(tenant_id, destino)
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


# ── Motor de cobro ↔ ciclo de vida del cliente ─────────────────
# El motor (plan_compras) vive en la BD del operador (tenant 1). Al cancelar o
# eliminar una tienda hay que cerrar su compra: si no, el cron seguía mandando
# recordatorios con link de pago y, si la persona pagaba, se intentaba
# reactivar una tienda que ya no existe.

def _conexion_operador():
    from db import get_tenant_conn, control_plane_cursor
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT db_name FROM tenant_databases WHERE tenant_id = 1")
        fila = cur.fetchone()
    if not fila:
        return None
    return get_tenant_conn(fila['db_name'])


def _motor_ejecutar(sql_texto, params, devolver=False):
    conn = _conexion_operador()
    if conn is None:
        return [] if devolver else 0
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT to_regclass('plan_compras') IS NOT NULL AS hay")
            if not cur.fetchone()['hay']:
                return [] if devolver else 0
            cur.execute(sql_texto, params)
            resultado = [dict(f) for f in cur.fetchall()] if devolver else cur.rowcount
        conn.commit()
        return resultado
    finally:
        conn.close()


def _sincronizar_motor(tenant_id: int, fecha, forzar: bool = False, pago: bool = False) -> int:
    """Lleva el vencimiento del maestro al motor de cobro (plan_compras), que es
    el que manda los recordatorios. Por defecto solo lo ADELANTA (un pago en
    línea pudo dejar el motor más adelante); con `forzar` (el operador corrigió
    la fecha a mano) lo deja igual al del maestro. Reinicia los recordatorios
    del ciclo. Nunca rompe la operación del maestro: devuelve las filas tocadas."""
    if not fecha:
        return 0
    try:
        sql = ("UPDATE plan_compras SET proximo_pago = %s, ultimo_recordatorio = NULL, "
               "suspendida_por_pago = CASE WHEN %s >= CURRENT_DATE THEN FALSE ELSE suspendida_por_pago END"
               + (", es_trial = FALSE" if pago else "")
               + " WHERE tenant_id = %s AND estado = 'ACTIVADA' AND renovacion_de IS NULL")
        params = [fecha, fecha, tenant_id]
        if not forzar:
            sql += " AND (proximo_pago IS NULL OR proximo_pago < %s)"
            params.append(fecha)
        return _motor_ejecutar(sql, tuple(params))
    except Exception:  # noqa: BLE001
        return 0


def cerrar_compra_motor(tenant_id: int, estado: str) -> int:
    """Tienda cancelada (CANCELADA) o eliminada (ELIMINADA): su compra deja de
    cobrarse. Devuelve cuántas filas cerró. Nunca borra la compra (historial)."""
    if estado not in ('CANCELADA', 'ELIMINADA'):
        raise ValueError('Estado de cierre inválido')
    return _motor_ejecutar(
        "UPDATE plan_compras SET estado = %s "
        "WHERE tenant_id = %s AND renovacion_de IS NULL AND estado IN ('ACTIVADA', 'CANCELADA')",
        (estado, tenant_id))


def reabrir_compra_motor(tenant_id: int) -> int:
    """Una tienda cancelada (soft) que se reactiva vuelve al ciclo de cobro."""
    return _motor_ejecutar(
        "UPDATE plan_compras SET estado = 'ACTIVADA' "
        "WHERE tenant_id = %s AND renovacion_de IS NULL AND estado = 'CANCELADA'",
        (tenant_id,))


def pruebas_por_limpiar(dias_gracia: int = 7) -> list:
    """Pruebas gratis que NO pagaron y vencieron hace más de `dias_gracia` días
    (o ya están canceladas): candidatas a eliminar para liberar el servidor.
    Una prueba que pagó deja de ser es_trial y nunca aparece aquí."""
    return _motor_ejecutar(
        """SELECT tenant_id, nombre_negocio, buyer_nombre, buyer_email, buyer_telefono,
                  dominio, slug, proximo_pago, estado, suspendida_por_pago,
                  (CURRENT_DATE - proximo_pago) AS dias_vencida
           FROM plan_compras
           WHERE es_trial = TRUE AND referencia_pedido LIKE 'TRIAL-%%'
             AND renovacion_de IS NULL AND tenant_id IS NOT NULL
             AND (estado = 'CANCELADA'
                  OR (estado = 'ACTIVADA' AND proximo_pago < CURRENT_DATE - %s))
           ORDER BY proximo_pago""",
        (int(dias_gracia),), devolver=True)


def es_prueba_sin_pagar(tenant_id: int) -> bool:
    """¿Este cliente fue una prueba gratis que nunca pagó?"""
    filas = _motor_ejecutar(
        "SELECT 1 FROM plan_compras WHERE tenant_id = %s AND referencia_pedido LIKE 'TRIAL-%%' "
        "AND es_trial = TRUE AND renovacion_de IS NULL LIMIT 1",
        (tenant_id,), devolver=True)
    return bool(filas)
