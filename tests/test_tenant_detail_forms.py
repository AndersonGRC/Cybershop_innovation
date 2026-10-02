"""La ficha del cliente se puede reorganizar, pero el backend debe recibir
exactamente lo mismo que antes (foto en tests/snapshots/tenant_detail_forms.json,
tomada antes de rediseñar la ficha).

Reglas:
- Cada formulario conserva acción, método, campos editables y valores enviados.
- Integraciones puede partirse en varios formularios hacia la misma ruta: entre
  todos cubren los mismos campos y ninguno se repite (el guardado solo toca las
  claves que recibe).
- Módulos puede mostrarse en varias pestañas: cada formulario envía TODOS los
  módulos activos (el guardado reemplaza la lista completa) y entre todos se
  puede encender o apagar cada módulo.
"""

import json
import os
from collections import Counter
from pathlib import Path

import pytest

import form_contract as fc

FOTO = json.loads((Path(__file__).parent / 'snapshots' / 'tenant_detail_forms.json').read_text(encoding='utf-8'))
INTEGRACIONES = '/tenants/7/integraciones'
MODULOS = '/tenants/7/modulos'


def _clave(f):
    return json.dumps(f, sort_keys=True, ensure_ascii=False)


@pytest.fixture(scope='module', params=['con_bd', 'sin_bd'])
def escenario(request):
    os.environ.setdefault('FLASK_SECRET_KEY', 'form-contract-test-only-secret')
    html = fc.render(request.param == 'con_bd')
    return request.param, [fc.firma(f) for f in fc.formularios(html)], html


def test_formularios_simples_identicos(escenario):
    nombre, nuevos, _ = escenario
    especiales = {INTEGRACIONES, MODULOS}
    antes = Counter(_clave(f) for f in FOTO[nombre] if f['action'] not in especiales)
    ahora = Counter(_clave(f) for f in nuevos if f['action'] not in especiales)
    assert ahora == antes


def test_integraciones_cubren_los_mismos_campos_sin_repetir(escenario):
    nombre, nuevos, _ = escenario
    antes = [f for f in FOTO[nombre] if f['action'] == INTEGRACIONES]
    ahora = [f for f in nuevos if f['action'] == INTEGRACIONES]
    assert len(antes) == 1 and ahora
    campos = [c for f in ahora for c in f['editables']]
    assert len(campos) == len(set(campos)), 'un campo de integraciones aparece en dos formularios'
    assert sorted(campos) == antes[0]['editables']
    assert all(f['method'] == 'post' and not f['envia'] for f in ahora)


def test_modulos_envian_siempre_todos_los_activos(escenario):
    nombre, nuevos, _ = escenario
    antes = [f for f in FOTO[nombre] if f['action'] == MODULOS]
    ahora = [f for f in nuevos if f['action'] == MODULOS]
    plan_antes = [f for f in antes if f['editables'] == ['plan']]
    plan_ahora = [f for f in ahora if f['editables'] == ['plan']]
    assert plan_ahora == plan_antes
    lista_antes = [f for f in antes if f['editables'] != ['plan']]
    lista_ahora = [f for f in ahora if f['editables'] != ['plan']]
    assert len(lista_antes) == len(lista_ahora) == 0 or lista_antes
    if not lista_antes:
        return
    activos = lista_antes[0]['envia']
    todos = {tuple(o) for o in lista_antes[0]['opciones']}
    for f in lista_ahora:
        assert f['editables'] == ['modulo']
        assert f['envia'] == activos, 'un formulario de módulos apagaría módulos que no muestra'
    assert {tuple(o) for f in lista_ahora for o in f['opciones']} == todos


def test_pestanas_accesibles(escenario):
    _, _, html = escenario
    assert 'role="tablist"' in html and 'aria-selected' in html
