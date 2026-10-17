"""Correo de bienvenida de los clientes creados desde el maestro.

El maestro le pide al sitio de CyberShop (tenant primario) enviar «¡Tu tienda está
lista!» con usuario y contraseña temporal, por la red interna y con el secreto
compartido. Sin red: urlopen está simulado.
"""

import io
import json
import os
import urllib.error

import pytest

os.environ.setdefault('FLASK_SECRET_KEY', 'bienvenida-test-only-secret')

import bienvenida_service as bv  # noqa: E402

RESULTADO = {'tenant_id': 41, 'slug': 'panaderia-qa', 'plan': 'estandar', 'domain': 'panaderia-qa.cybershopcol.com',
             'admin_email': 'duena@ejemplo.com', 'admin_password': 'Temp-Abc123', 'client_code': 'CS-1234'}


@pytest.fixture
def red(monkeypatch):
    monkeypatch.setattr(bv.Config, 'INTERNAL_API_KEY', 'clave-qa')
    monkeypatch.setattr(bv, 'url_operador', lambda: 'http://127.0.0.1:8001')
    llamadas = []

    def responder(cuerpo=None, error=None):
        def urlopen(peticion, timeout=None):
            llamadas.append(peticion)
            if error:
                raise error
            return io.BytesIO(json.dumps(cuerpo).encode())
        monkeypatch.setattr(bv.urllib.request, 'urlopen', urlopen)
    return responder, llamadas


def test_pide_el_correo_al_sitio_de_cybershop(red):
    responder, llamadas = red
    responder({'ok': True})
    assert bv.enviar(RESULTADO, admin_nombre='Dueña QA') == (True, '')
    peticion = llamadas[0]
    assert peticion.full_url == 'http://127.0.0.1:8001/internal/api/v1/correo-bienvenida'
    assert peticion.get_header('X-internal-key') == 'clave-qa'
    datos = json.loads(peticion.data)
    assert datos == {'admin_email': 'duena@ejemplo.com', 'admin_nombre': 'Dueña QA',
                     'admin_password': 'Temp-Abc123', 'dominio': 'panaderia-qa.cybershopcol.com',
                     'plan': 'estandar', 'client_code': 'CS-1234'}


def test_si_el_sitio_no_lo_envia_se_avisa(red):
    responder, _ = red
    responder({'ok': False})
    assert bv.enviar(RESULTADO) == (False, 'el correo no salió')
    responder(error=urllib.error.HTTPError('u', 403, 'no', {}, None))
    ok, motivo = bv.enviar(RESULTADO)
    assert not ok and '403' in motivo
    responder(error=TimeoutError())
    ok, motivo = bv.enviar(RESULTADO)
    assert not ok and 'no se pudo contactar' in motivo


def test_sin_clave_no_se_intenta(monkeypatch):
    monkeypatch.setattr(bv.Config, 'INTERNAL_API_KEY', '')
    ok, motivo = bv.enviar(RESULTADO)
    assert not ok and 'INTERNAL_API_KEY' in motivo
