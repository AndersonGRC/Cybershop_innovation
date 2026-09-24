"""Contrato local del botón: código compartido y BD/recarga de un solo cliente.

No invoca Git, systemd ni una base real; la instalación del helper en el VPS
se verifica aparte antes de publicar.
"""

import os

import pytest
from flask import get_flashed_messages


os.environ.setdefault('FLASK_SECRET_KEY', 'update-app-route-test-only-secret')


@pytest.fixture
def update_env(monkeypatch):
    from app import create_app
    from routes import tenant_routes
    import provisioning_service
    import tenant_migrations

    app = create_app()
    app.config.update(TESTING=True)
    tenant = {'id': 17, 'slug': 'cliente-a', 'db_name': 'cyber_t017'}
    monkeypatch.setattr(tenant_routes.tenant_service, 'get_tenant', lambda _id: tenant)
    events = []
    monkeypatch.setattr(provisioning_service, 'deploy_code',
                        lambda include_public=False: (events.append(('deploy', include_public))
                                                      or ('updated', 'sha-prueba')))
    monkeypatch.setattr(tenant_migrations, 'migrate_db',
                        lambda db: (events.append(('migrate', db)) or ['0015_ia_acciones_pendientes.sql']))
    monkeypatch.setattr(tenant_routes.billing_service, 'sync_billing_to_tenant',
                        lambda tid: events.append(('billing', tid)))
    monkeypatch.setattr(provisioning_service, 'reload_service',
                        lambda slug: events.append(('reload', slug)))
    return app, tenant_routes.instancia_accion.__wrapped__, events


def test_actualizar_migra_y_recarga_solo_cliente_seleccionado(update_env):
    app, action, events = update_env
    with app.test_request_context('/tenants/17/instancia', method='POST',
                                  data={'accion': 'update'}):
        response = action(17)
        messages = get_flashed_messages()

    assert response.status_code == 302
    assert events == [('deploy', False), ('migrate', 'cyber_t017'),
                      ('billing', 17), ('reload', 'cliente-a')]
    assert any('Cliente actualizado' in message for message in messages)


def test_gate_publico_bloquea_migracion_y_recarga(update_env, monkeypatch):
    app, action, events = update_env
    import provisioning_service

    monkeypatch.setattr(provisioning_service, 'deploy_code',
                        lambda include_public=False: (events.append(('deploy', include_public))
                                                      or ('blocked', 'cambio público')))
    with app.test_request_context('/tenants/17/instancia', method='POST',
                                  data={'accion': 'update'}):
        action(17)
        messages = get_flashed_messages()

    assert events == [('deploy', False)]
    assert any('No se actualizó' in message for message in messages)


@pytest.mark.parametrize('code_status', ['updated', 'uptodate'])
def test_migracion_fallida_no_recarga_pero_codigo_ya_esta_en_disco(
    update_env, monkeypatch, code_status,
):
    app, action, events = update_env
    import tenant_migrations
    import provisioning_service

    monkeypatch.setattr(provisioning_service, 'deploy_code',
                        lambda include_public=False: (events.append(('deploy', include_public))
                                                      or (code_status, 'sha-prueba')))

    def fail(db):
        events.append(('migrate', db))
        raise RuntimeError('migración fallida')

    monkeypatch.setattr(tenant_migrations, 'migrate_db', fail)
    with app.test_request_context('/tenants/17/instancia', method='POST',
                                  data={'accion': 'update'}):
        action(17)
        messages = get_flashed_messages()

    assert events == [('deploy', False), ('migrate', 'cyber_t017')]
    assert any('migración fallida' in message for message in messages)
    assert any('Actualización parcial' in message for message in messages)


def test_deploy_normal_bloquea_ruta_publica_antes_de_apply(monkeypatch):
    import provisioning_service as prov

    calls = []
    monkeypatch.setattr(prov, 'IS_LINUX', True)
    monkeypatch.setattr(prov, '_run_deploy',
                        lambda subcmd: (calls.append(subcmd) or
                                        (0, 'app/templates/index.html\napp/services/ia_acciones.py')))

    status, message = prov.deploy_code()

    assert status == 'blocked'
    assert 'app/templates/index.html' in message
    assert calls == ['changes']


def test_deploy_completo_aplica_ruta_publica_si_se_solicita(monkeypatch):
    import provisioning_service as prov

    calls = []
    monkeypatch.setattr(prov, 'IS_LINUX', True)

    def run(subcmd):
        calls.append(subcmd)
        return (0, 'app/templates/index.html') if subcmd == 'changes' else (0, 'sha-prueba')

    monkeypatch.setattr(prov, '_run_deploy', run)

    status, message = prov.deploy_code(include_public=True)

    assert status == 'updated'
    assert 'público' in message
    assert calls == ['changes', 'apply']


def test_migracion_ia_acciones_esta_en_catalogo_del_maestro():
    import tenant_migrations

    assert '0015_ia_acciones_pendientes.sql' in {path.name for path in tenant_migrations._files()}
