"""Vistas de la flota completa — SOLO LECTURA.

Junta en una sola consulta lo que la ficha del cliente muestra de a uno:
cobros (tenant_billing + motor plan_compras) e inteligencia artificial
(módulos en la BD de cada cliente + variables de su instancia).

Nada aquí escribe: las conexiones a la BD del operador y de los clientes se
abren en modo solo lectura y cualquier falla de un cliente se informa sin
romper la vista.
"""

import datetime

from psycopg2.extras import RealDictCursor

from config import Config
from db import control_plane_cursor, get_tenant_conn

ESTADOS_VIVOS = ('activo', 'suspendido')
DIAS_POR_VENCER = 7


def _hoy():
    return datetime.date.today()


def _conn_lectura(db_name):
    conn = get_tenant_conn(db_name)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def _whatsapp_url(telefono):
    digitos = ''.join(ch for ch in str(telefono or '') if ch.isdigit())
    if len(digitos) == 10:
        digitos = '57' + digitos
    return f'https://wa.me/{digitos}' if len(digitos) >= 11 else None


# ── Cobros ─────────────────────────────────────────────────────
def _motor_por_cliente():
    """{tenant_id: compra activa} del motor de cobro (BD del operador)."""
    try:
        with control_plane_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT db_name FROM tenant_databases WHERE tenant_id = 1")
            fila = cur.fetchone()
        if not fila:
            return {}
        conn = _conn_lectura(fila['db_name'])
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT to_regclass('plan_compras') IS NOT NULL AS hay")
                if not cur.fetchone()['hay']:
                    return {}
                cur.execute("""
                    SELECT DISTINCT ON (tenant_id)
                           tenant_id, plan_key, proximo_pago, es_trial,
                           suspendida_por_pago, buyer_nombre, buyer_telefono
                    FROM plan_compras
                    WHERE estado = 'ACTIVADA' AND tenant_id IS NOT NULL
                    ORDER BY tenant_id, id DESC
                """)
                return {f['tenant_id']: dict(f) for f in cur.fetchall()}
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — el motor es opcional para esta vista
        return {}


def cobros_flota():
    """Estado de cobro de cada cliente vivo + resumen para el panel."""
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT to_regclass('tenant_billing') IS NOT NULL AS hay")
        hay_billing = cur.fetchone()['hay']
        columnas_billing = ("b.monto_mensual, b.proxima_fecha, b.auto_suspender, b.dias_suspension"
                            if hay_billing else
                            "NULL::numeric AS monto_mensual, NULL::date AS proxima_fecha, "
                            "TRUE AS auto_suspender, NULL::int AS dias_suspension")
        union = "LEFT JOIN tenant_billing b ON b.tenant_id = t.id" if hay_billing else ""
        cur.execute(f"""
            SELECT t.id, t.slug, t.nombre, t.estado, t.plan, {columnas_billing}
            FROM tenants t {union}
            WHERE t.estado IN %s
            ORDER BY t.nombre
        """, (ESTADOS_VIVOS,))
        filas = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS n FROM tenants WHERE estado = 'cancelado'")
        cancelados = cur.fetchone()['n']

    import billing_service as bs
    motor = _motor_por_cliente()
    hoy = _hoy()
    clientes = []
    for f in filas:
        m = motor.get(f['id'])
        proxima = f['proxima_fecha']
        if not proxima:
            estado, dias = 'sin_config', None
        elif hoy <= proxima:
            estado, dias = ('por_vencer' if (proxima - hoy).days <= DIAS_POR_VENCER else 'al_dia'), (proxima - hoy).days
        else:
            estado, dias = 'en_mora', (hoy - proxima).days
        umbral = f['dias_suspension'] if f['dias_suspension'] is not None else (
            bs.DIAS_SUSPENSION_DEFAULT if m else bs.MORA_DIAS_SUSPENSION)
        clientes.append({
            'id': f['id'], 'slug': f['slug'], 'nombre': f['nombre'], 'estado': f['estado'], 'plan': f['plan'],
            'monto': float(f['monto_mensual'] or 0), 'proxima_fecha': proxima,
            'estado_cobro': estado, 'dias': dias,
            'auto_suspender': bool(f['auto_suspender']),
            'a_suspension': max(0, umbral - dias) if estado == 'en_mora' and f['auto_suspender'] else None,
            'en_motor': m is not None,
            'es_prueba': bool(m and m.get('es_trial')),
            'suspendida_por_pago': bool(m and m.get('suspendida_por_pago')),
            'contacto': (m or {}).get('buyer_nombre') or '',
            'whatsapp_url': _whatsapp_url((m or {}).get('buyer_telefono')),
        })

    orden = {'en_mora': 0, 'por_vencer': 1, 'sin_config': 2, 'al_dia': 3}
    clientes.sort(key=lambda c: (orden[c['estado_cobro']], -(c['dias'] or 0) if c['estado_cobro'] == 'en_mora' else (c['dias'] or 0)))
    activos = [c for c in clientes if c['estado'] == 'activo']
    resumen = {
        'activos': len(activos),
        'suspendidos': sum(1 for c in clientes if c['estado'] == 'suspendido'),
        'cancelados': cancelados,
        'en_mora': sum(1 for c in clientes if c['estado_cobro'] == 'en_mora'),
        'por_vencer': sum(1 for c in clientes if c['estado_cobro'] == 'por_vencer'),
        'sin_config': sum(1 for c in clientes if c['estado_cobro'] == 'sin_config'),
        'pruebas': sum(1 for c in clientes if c['es_prueba']),
        'ingreso_mensual': sum(c['monto'] for c in activos if not c['es_prueba']),
        'cartera_vencida': sum(c['monto'] for c in clientes if c['estado_cobro'] == 'en_mora'),
    }
    return {'clientes': clientes, 'resumen': resumen, 'dias_por_vencer': DIAS_POR_VENCER}


def cobro_por_cliente():
    """{tenant_id: fila de cobros_flota} para la lista de clientes."""
    try:
        return {c['id']: c for c in cobros_flota()['clientes']}
    except Exception:  # noqa: BLE001 — la lista funciona aunque falle el cobro
        return {}


# ── Inteligencia artificial ────────────────────────────────────
def _ia_de_cliente(tenant):
    """Módulos IA (BD del cliente) + configuración de su instancia (env)."""
    import integrations_service as ints
    import module_service as ms

    fila = {'id': tenant['id'], 'slug': tenant['slug'], 'nombre': tenant['nombre'],
            'estado': tenant['estado'], 'modulos': {}, 'error': None}
    codigos_ia = [m for m in ms.MODULES if m[3] == 'inteligencia']
    if tenant.get('db_name'):
        try:
            conn = _conn_lectura(tenant['db_name'])
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT clave, valor FROM cliente_config WHERE clave = ANY(%s)",
                                ([m[4] for m in codigos_ia],))
                    guardado = {r['clave']: r['valor'] for r in cur.fetchall()}
            finally:
                conn.close()
            for code, nombre, _d, _c, clave, default in codigos_ia:
                fila['modulos'][code] = ms._as_bool(guardado.get(clave), default)
        except Exception as exc:  # noqa: BLE001
            fila['error'] = f'No se pudo leer su BD ({exc.__class__.__name__})'
    else:
        fila['error'] = 'Sin BD aprovisionada'
    try:
        env = ints.read_env(tenant['slug'])
    except Exception:  # noqa: BLE001
        env = {}
    fila['modelo'] = env.get('AI_MODEL', '')
    fila['servidor'] = env.get('AI_BASE_URL', '') or Config.AI_DEFAULT_BASE_URL
    presupuesto = env.get('AI_NUBE_PRESUPUESTO_USD', '0') or '0'
    try:
        presupuesto_n = float(presupuesto)
    except ValueError:
        presupuesto_n = 0.0
    fila['respaldo'] = bool(env.get('AI_NUBE_API_KEY')) and presupuesto_n > 0
    fila['respaldo_usd'] = presupuesto_n
    fila['respaldo_publico'] = env.get('AI_NUBE_PARA_PUBLICO', 'false') == 'true'
    fila['alguna_ia'] = any(fila['modulos'].values())
    fila['sin_modelo'] = fila['alguna_ia'] and not fila['modelo']
    return fila


def ia_flota(probar_servidores=True):
    """IA de cada cliente vivo + estado de los servidores de IA usados."""
    import integrations_service as ints
    import module_service as ms

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT t.id, t.slug, t.nombre, t.estado, td.db_name
            FROM tenants t LEFT JOIN tenant_databases td ON td.tenant_id = t.id
            WHERE t.estado IN %s ORDER BY t.nombre
        """, (ESTADOS_VIVOS,))
        tenants = cur.fetchall()
    clientes = [_ia_de_cliente(dict(t)) for t in tenants]

    servidores = {}
    for c in clientes:
        if c['alguna_ia']:
            servidores.setdefault(c['servidor'], {'url': c['servidor'], 'clientes': 0, 'modelos': None})
            servidores[c['servidor']]['clientes'] += 1
    if probar_servidores:
        for s in servidores.values():
            modelos = ints.fetch_ai_models(s['url'], timeout=3.0)
            s['responde'] = bool(modelos)
            s['modelos'] = modelos
            for c in clientes:
                if c['servidor'] == s['url'] and c['modelo'] and modelos:
                    c['modelo_instalado'] = c['modelo'] in modelos

    nombres = {m[0]: m[1] for m in ms.MODULES if m[3] == 'inteligencia'}
    resumen = {
        'con_ia': sum(1 for c in clientes if c['alguna_ia']),
        'sin_modelo': sum(1 for c in clientes if c['sin_modelo']),
        'con_respaldo': sum(1 for c in clientes if c['respaldo']),
        'respaldo_usd': sum(c['respaldo_usd'] for c in clientes if c['respaldo']),
        'errores': sum(1 for c in clientes if c['error']),
        'por_modulo': {code: sum(1 for c in clientes if c['modulos'].get(code)) for code in nombres},
    }
    return {'clientes': clientes, 'servidores': list(servidores.values()), 'resumen': resumen,
            'nombres_modulos': nombres}
