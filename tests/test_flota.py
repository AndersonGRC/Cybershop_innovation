"""Vistas de la flota (cobros e IA): cálculo, solo lectura y páginas.

Sin bases reales: los cursores y conexiones se simulan."""

import datetime
import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault('FLASK_SECRET_KEY', 'flota-test-only-secret')
os.environ.setdefault('SESSION_COOKIE_SECURE', 'false')

import fleet_service as fs  # noqa: E402

HOY = datetime.date(2026, 10, 2)


class CursorFalso:
    """Devuelve una respuesta por cada execute (en orden)."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.sql = []
        self._actual = None

    def execute(self, sql, params=None):
        self.sql.append(sql)
        self._actual = self.respuestas.pop(0)

    def fetchone(self):
        return self._actual

    def fetchall(self):
        return self._actual


def _cp(respuestas):
    cur = CursorFalso(respuestas)

    @contextmanager
    def fabrica(dict_cursor=True):
        yield cur
    return fabrica, cur


def _fila(id_, nombre, proxima, monto=100000, estado='activo', dias_susp=None, auto=True):
    return {'id': id_, 'slug': f's{id_}', 'nombre': nombre, 'estado': estado, 'plan': 'ultra',
            'monto_mensual': monto, 'proxima_fecha': proxima, 'auto_suspender': auto, 'dias_suspension': dias_susp}


@pytest.fixture
def cobros(monkeypatch):
    filas = [
        _fila(1, 'Al día', HOY + datetime.timedelta(days=20)),
        _fila(2, 'Por vencer', HOY + datetime.timedelta(days=3)),
        _fila(3, 'Mora', HOY - datetime.timedelta(days=10), dias_susp=15),
        _fila(4, 'Sin config', None, monto=0),
        _fila(5, 'Prueba', HOY + datetime.timedelta(days=5), monto=0),
        _fila(6, 'Suspendido', HOY - datetime.timedelta(days=70), estado='suspendido'),
    ]
    fabrica, _ = _cp([{'hay': True}, filas, {'n': 2}])
    monkeypatch.setattr(fs, 'control_plane_cursor', fabrica)
    monkeypatch.setattr(fs, '_hoy', lambda: HOY)
    monkeypatch.setattr(fs, '_motor_por_cliente', lambda: {
        5: {'es_trial': True, 'buyer_nombre': 'Ana', 'buyer_telefono': '3001234567', 'suspendida_por_pago': False},
        3: {'es_trial': False, 'buyer_nombre': 'Luis', 'buyer_telefono': '', 'suspendida_por_pago': False},
    })
    return fs.cobros_flota()


def test_estados_y_orden(cobros):
    estados = [(c['nombre'], c['estado_cobro']) for c in cobros['clientes']]
    assert estados[0] == ('Suspendido', 'en_mora') and estados[1] == ('Mora', 'en_mora')
    assert dict(estados) == {'Al día': 'al_dia', 'Por vencer': 'por_vencer', 'Mora': 'en_mora',
                             'Sin config': 'sin_config', 'Prueba': 'por_vencer', 'Suspendido': 'en_mora'}


def test_dias_a_suspension_usa_el_plazo_del_cliente(cobros):
    mora = next(c for c in cobros['clientes'] if c['nombre'] == 'Mora')
    assert mora['dias'] == 10 and mora['a_suspension'] == 5


def test_resumen(cobros):
    r = cobros['resumen']
    assert r['en_mora'] == 2 and r['por_vencer'] == 2 and r['sin_config'] == 1
    assert r['pruebas'] == 1 and r['cancelados'] == 2 and r['suspendidos'] == 1
    # Ingreso: activos que no son prueba (al día, por vencer, mora; sin config = 0).
    assert r['ingreso_mensual'] == 300000
    prueba = next(c for c in cobros['clientes'] if c['nombre'] == 'Prueba')
    assert prueba['es_prueba'] and prueba['whatsapp_url'] == 'https://wa.me/573001234567'


def test_sin_tabla_de_cobros_no_falla(monkeypatch):
    fabrica, cur = _cp([{'hay': False}, [_fila(1, 'X', None)], {'n': 0}])
    monkeypatch.setattr(fs, 'control_plane_cursor', fabrica)
    monkeypatch.setattr(fs, '_motor_por_cliente', lambda: {})
    datos = fs.cobros_flota()
    assert datos['clientes'][0]['estado_cobro'] == 'sin_config'
    assert 'tenant_billing' not in cur.sql[1]


def test_conexiones_a_clientes_son_de_solo_lectura(monkeypatch):
    conn = MagicMock()
    monkeypatch.setattr(fs, 'get_tenant_conn', lambda db: conn)
    fs._conn_lectura('cyber_t001')
    conn.set_session.assert_called_once_with(readonly=True, autocommit=True)


def test_ia_flota(monkeypatch):
    tenants = [
        {'id': 1, 'slug': 'a', 'nombre': 'A', 'estado': 'activo', 'db_name': 'cyber_t001'},
        {'id': 2, 'slug': 'b', 'nombre': 'B', 'estado': 'activo', 'db_name': 'cyber_t002'},
        {'id': 3, 'slug': 'c', 'nombre': 'C', 'estado': 'activo', 'db_name': None},
    ]
    fabrica, _ = _cp([tenants])
    monkeypatch.setattr(fs, 'control_plane_cursor', fabrica)
    config = {
        'cyber_t001': [{'clave': 'ia_habilitado', 'valor': 'true'}, {'clave': 'chat_publico_habilitado', 'valor': 'true'}],
        'cyber_t002': [],
    }

    def conexion(db):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchall.return_value = config[db]
        return conn
    monkeypatch.setattr(fs, '_conn_lectura', conexion)
    envs = {'a': {'AI_MODEL': 'qwen', 'AI_NUBE_API_KEY': 'k', 'AI_NUBE_PRESUPUESTO_USD': '2'}, 'b': {}, 'c': {}}
    import integrations_service as ints
    monkeypatch.setattr(ints, 'read_env', lambda slug: envs[slug])
    monkeypatch.setattr(ints, 'fetch_ai_models', lambda url, timeout=3.0: ['qwen', 'gemma'])

    datos = fs.ia_flota()
    a, b, c = datos['clientes']
    assert a['modulos']['ai_assistant'] and a['modulos']['ai_public'] and not a['modulos']['ai_actions']
    assert a['respaldo'] and a['respaldo_usd'] == 2 and a['modelo_instalado']
    assert not b['alguna_ia'] and c['error'] == 'Sin BD aprovisionada'
    assert datos['resumen']['con_ia'] == 1 and datos['resumen']['con_respaldo'] == 1
    assert datos['servidores'][0]['responde'] and datos['servidores'][0]['clientes'] == 1


# ── Páginas ────────────────────────────────────────────────────
@pytest.fixture
def cliente():
    from app import create_app
    app = create_app()
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False, WTF_CSRF_ENABLED=False)
    c = app.test_client()
    with c.session_transaction() as s:
        s['admin_id'] = 1
    with patch('auth.current_admin', return_value={'id': 1, 'email': 'op@x.com', 'nombre': 'Op'}):
        yield c


COBROS = {'clientes': [{'id': 3, 'slug': 's3', 'nombre': 'Mora SAS', 'estado': 'activo', 'plan': 'ultra',
                        'monto': 100000, 'proxima_fecha': HOY, 'estado_cobro': 'en_mora', 'dias': 10,
                        'auto_suspender': True, 'a_suspension': 5, 'en_motor': True, 'es_prueba': False,
                        'suspendida_por_pago': False, 'contacto': 'Luis', 'whatsapp_url': None}],
          'resumen': {'activos': 1, 'suspendidos': 0, 'cancelados': 0, 'en_mora': 1, 'por_vencer': 0,
                      'sin_config': 0, 'pruebas': 0, 'ingreso_mensual': 100000, 'cartera_vencida': 100000},
          'dias_por_vencer': 7}


def test_pagina_cobros(cliente):
    with patch('fleet_service.cobros_flota', return_value=COBROS):
        html = cliente.get('/cobros').get_data(as_text=True)
    assert 'Mora SAS' in html and 'en mora · 10 d' in html and 'se suspende en 5 d' in html


def test_pagina_ia(cliente):
    datos = {'clientes': [{'id': 1, 'slug': 'a', 'nombre': 'Café A', 'estado': 'activo', 'modulos': {'ai_assistant': True},
                           'error': None, 'modelo': '', 'servidor': 'http://x', 'respaldo': False, 'respaldo_usd': 0,
                           'respaldo_publico': False, 'alguna_ia': True, 'sin_modelo': True}],
             'servidores': [{'url': 'http://x', 'clientes': 1, 'modelos': [], 'responde': False}],
             'resumen': {'con_ia': 1, 'sin_modelo': 1, 'con_respaldo': 0, 'respaldo_usd': 0, 'errores': 0,
                         'por_modulo': {'ai_assistant': 1}},
             'nombres_modulos': {'ai_assistant': 'Asistente IA'}}
    with patch('fleet_service.ia_flota', return_value=datos):
        html = cliente.get('/ia').get_data(as_text=True)
    assert 'Café A' in html and 'sin modelo' in html and 'no responde' in html


def test_panel_y_lista_con_cobros(cliente):
    stats = {'tenants_total': 1, 'tenants_activos': 1, 'tenants_suspendidos': 0, 'keys_total': 0,
             'keys_activas': 0, 'ultimo_sync': None, 'actividad': []}
    with patch('tenant_service.dashboard_stats', return_value=stats), \
         patch('fleet_service.cobros_flota', return_value=COBROS):
        panel = cliente.get('/').get_data(as_text=True)
    assert 'Requieren atención' in panel and 'Mora SAS' in panel
    fila = {'id': 3, 'slug': 's3', 'nombre': 'Mora SAS', 'estado': 'activo', 'plan': 'ultra', 'db_name': 'cyber_t003',
            'active_keys': 0, 'total_keys': 0, 'last_used_at': None, 'created_at': datetime.datetime(2026, 1, 1)}
    with patch('tenant_service.list_tenants', return_value=[fila]), \
         patch('fleet_service.cobros_flota', return_value=COBROS):
        lista = cliente.get('/tenants/').get_data(as_text=True)
    assert 'mora 10 d' in lista


def test_panel_carga_si_falla_el_cobro(cliente):
    stats = {'tenants_total': 0, 'tenants_activos': 0, 'tenants_suspendidos': 0, 'keys_total': 0,
             'keys_activas': 0, 'ultimo_sync': None, 'actividad': []}
    with patch('tenant_service.dashboard_stats', return_value=stats), \
         patch('fleet_service.cobros_flota', side_effect=RuntimeError('BD caída')):
        r = cliente.get('/')
    assert r.status_code == 200 and 'Requieren atención' not in r.get_data(as_text=True)
