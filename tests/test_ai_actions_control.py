"""El control de acciones IA es explícito y la auditoría se consulta por BD."""

from contextlib import contextmanager

import module_service as modules


def test_acciones_no_se_encienden_por_plan_ultra():
    assert 'ai_actions' in modules.MODULE_BY_CODE
    assert modules.MODULE_BY_CODE['ai_actions'][4] == 'ia_acciones_habilitadas'
    assert modules.MODULE_BY_CODE['ai_actions'][5] is False
    assert 'ai_actions' not in modules.PLAN_MODULES['ultra']


def test_historial_ia_consulta_solo_base_del_cliente_pedido(monkeypatch):
    vistos = []

    class Cursor:
        def execute(self, sql):
            vistos.append(sql)

        def fetchone(self):
            return {'tabla': 'ia_acciones_pendientes'}

        def fetchall(self):
            return [{'id': 'uuid-1', 'tipo': 'crear_contacto',
                     'estado': 'ejecutada', 'usuario_id': 7, 'resumen': 'Crear Ana',
                     'creado_en': None, 'decidido_en': None}]

    @contextmanager
    def cursor(tenant_id):
        vistos.append(('tenant_id', tenant_id))
        yield Cursor()

    monkeypatch.setattr(modules, 'tenant_cursor', cursor)
    acciones = modules.get_ai_actions_audit(8)
    assert vistos[0] == ('tenant_id', 8)
    assert acciones[0]['tipo'] == 'crear_contacto'
    assert all('payload' not in sql for sql in vistos[1:])
