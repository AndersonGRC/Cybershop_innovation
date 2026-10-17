"""Toda tienda nueva creada desde el maestro sale con SU WhatsApp.

Es el botón «Chatea con nosotros» de su página: sin un número propio la tienda no
tiene botón (ya no se usa el de CyberShop). No crea BD ni instancia: create_tenant y
set_values están simulados.
"""

import os

import pytest
from flask import get_flashed_messages


os.environ.setdefault('FLASK_SECRET_KEY', 'nuevo-cliente-whatsapp-test-only-secret')

BASE = {'slug': 'panaderia-qa', 'nombre': 'Panadería QA', 'admin_email': 'duena@ejemplo.com',
        'admin_nombre': 'Dueña', 'plan': 'estandar', 'timezone': 'America/Bogota'}


@pytest.fixture
def nuevo_env(monkeypatch):
    from app import create_app
    from routes import tenant_routes

    app = create_app()
    app.config.update(TESTING=True)
    creados, contacto = [], []
    monkeypatch.setattr(tenant_routes.tenant_service, 'create_tenant',
                        lambda **kw: creados.append(kw) or {'tenant_id': 41, 'warnings': []})
    monkeypatch.setattr(tenant_routes.ccs, 'set_values',
                        lambda tenant_id, valores: contacto.append((tenant_id, valores)))
    # Sin red: el correo de bienvenida queda anotado (tests/test_bienvenida.py lo prueba).
    monkeypatch.setattr(tenant_routes.bienvenida, 'enviar', lambda result, admin_nombre='': (True, ''))

    def enviar(**campos):
        with app.test_request_context('/tenants/nuevo', method='POST', data={**BASE, **campos}):
            respuesta = tenant_routes.nuevo.__wrapped__()
            return respuesta, get_flashed_messages()
    return enviar, creados, contacto


def test_sin_whatsapp_no_se_crea_el_cliente(nuevo_env):
    enviar, creados, contacto = nuevo_env
    pagina, mensajes = enviar(empresa_whatsapp='', empresa_telefono='(601) 234 5678')
    assert not creados and not contacto, 'se valida antes de crear la BD'
    assert any('Escribe el WhatsApp del negocio' in m for m in mensajes)
    assert 'name="empresa_whatsapp" required' in pagina and 'Panadería QA' in pagina, 'conserva lo escrito'


def test_el_whatsapp_de_cybershop_no_sirve(nuevo_env):
    enviar, creados, _ = nuevo_env
    _, mensajes = enviar(empresa_whatsapp='302 797 4969')
    assert not creados and any('WhatsApp de CyberShop' in m for m in mensajes)


def test_guarda_su_whatsapp_y_si_no_hay_telefono_usa_el_mismo(nuevo_env):
    enviar, creados, contacto = nuevo_env
    respuesta, _ = enviar(empresa_whatsapp='+57 300 123 4567', empresa_telefono='')
    assert respuesta.status_code == 302 and len(creados) == 1
    assert contacto == [(41, {'empresa_telefono': '3001234567', 'empresa_whatsapp': '573001234567'})]


def test_conserva_su_telefono_fijo(nuevo_env):
    enviar, _, contacto = nuevo_env
    enviar(empresa_whatsapp='3104445566', empresa_telefono='(601) 234 5678')
    assert contacto == [(41, {'empresa_telefono': '(601) 234 5678', 'empresa_whatsapp': '573104445566'})]


def test_al_crear_se_envia_la_bienvenida(nuevo_env, monkeypatch):
    from routes import tenant_routes
    pedidos = []
    monkeypatch.setattr(tenant_routes.bienvenida, 'enviar',
                        lambda result, admin_nombre='': pedidos.append((result, admin_nombre)) or (True, ''))
    enviar, creados, _ = nuevo_env
    _, mensajes = enviar(empresa_whatsapp='3001234567')
    assert len(creados) == 1 and pedidos[0][1] == 'Dueña' and pedidos[0][0]['tenant_id'] == 41
    assert any('correo de bienvenida' in m for m in mensajes)


def test_si_la_bienvenida_falla_la_tienda_queda_y_se_avisa(nuevo_env, monkeypatch):
    from routes import tenant_routes
    monkeypatch.setattr(tenant_routes.bienvenida, 'enviar',
                        lambda result, admin_nombre='': (False, 'el sitio principal respondió 502'))
    enviar, creados, _ = nuevo_env
    respuesta, mensajes = enviar(empresa_whatsapp='3001234567')
    assert respuesta.status_code == 302 and len(creados) == 1
    assert any('No se pudo enviar el correo de bienvenida' in m and '502' in m for m in mensajes)
