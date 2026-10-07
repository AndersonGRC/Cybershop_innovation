"""El día de pago del cliente no cambia (fecha de corte).

Caso real (panadería, oct-2026): vencía el 18 de septiembre, pagó el 7 de
octubre (19 días tarde) y el maestro dejó el próximo vencimiento en el 7 de
noviembre: contaba el mes desde el día del pago. Debe quedar el 18 de octubre.

Sin base de datos real: la regla es una función pura y lo demás se simula.
"""

import datetime
import os
from contextlib import contextmanager

import pytest

os.environ.setdefault('FLASK_SECRET_KEY', 'cobros-corte-test-only-secret')

import billing_service as bs  # noqa: E402

D = datetime.date


# ── La regla ────────────────────────────────────────────────────
@pytest.mark.parametrize('proxima, dia, pago, meses, esperado', [
    # Pagó tarde (la panadería): el mes va del 18 al 18, no desde el pago.
    (D(2026, 9, 18), None, D(2026, 10, 7), 1, D(2026, 10, 18)),
    # A tiempo, el mismo día y por adelantado: igual, sobre el corte.
    (D(2026, 10, 18), None, D(2026, 10, 18), 1, D(2026, 11, 18)),
    (D(2026, 10, 18), None, D(2026, 10, 10), 1, D(2026, 11, 18)),
    # Varios meses de una vez.
    (D(2026, 10, 18), None, D(2026, 10, 10), 3, D(2027, 1, 18)),
    # Con prórroga («Dar más plazo» hasta el 2-nov): el pago cubre el mes del corte.
    (D(2026, 11, 2), 18, D(2026, 10, 30), 1, D(2026, 11, 18)),
    # Fin de mes: el 31 en febrero es el 28, y en marzo vuelve al 31.
    (D(2027, 1, 31), 31, D(2027, 1, 30), 1, D(2027, 2, 28)),
    (D(2027, 2, 28), 31, D(2027, 2, 27), 1, D(2027, 3, 31)),
    (D(2028, 1, 31), 31, D(2028, 1, 31), 1, D(2028, 2, 29)),
    # Debía dos meses y pagó uno: sigue vencido (el pago no regala meses).
    (D(2026, 8, 18), None, D(2026, 10, 7), 1, D(2026, 9, 18)),
    # Cambio de año.
    (D(2026, 12, 18), None, D(2027, 1, 5), 1, D(2027, 1, 18)),
])
def test_el_dia_de_pago_no_cambia(proxima, dia, pago, meses, esperado):
    nueva, dia_corte = bs.proximo_vencimiento(proxima, dia, pago, meses)
    assert nueva == esperado
    assert dia_corte == (dia or proxima.day)


def test_primer_pago_sin_vencimiento_arranca_ese_dia():
    assert bs.proximo_vencimiento(None, None, D(2026, 10, 7), 1) == (D(2026, 11, 7), 7)


def test_meses_validos():
    assert bs._parse_meses('') == 1 and bs._parse_meses('3') == 3
    for malo in ('0', '13', 'dos'):
        with pytest.raises(ValueError):
            bs._parse_meses(malo)


# ── registrar_pago con la base simulada ─────────────────────────
class _Cursor:
    def __init__(self, fila):
        self.fila, self.sql = fila, []

    def execute(self, sql, params=None):
        self.sql.append((' '.join(sql.split()), params))

    def fetchone(self):
        return self.fila


@pytest.fixture()
def base(monkeypatch):
    estado = {'fila': None, 'cursores': [], 'motor': [], 'auditoria': [], 'reactivado': []}

    @contextmanager
    def cursor(dict_cursor=True):
        c = _Cursor(estado['fila'])
        estado['cursores'].append(c)
        yield c
    monkeypatch.setattr(bs, 'control_plane_cursor', cursor)
    monkeypatch.setattr(bs, '_ensure_tables', lambda: None)
    monkeypatch.setattr(bs, '_today', lambda: D(2026, 10, 7))
    monkeypatch.setattr(bs.audit_service, 'registrar', lambda *a, **k: estado['auditoria'].append((a, k)))
    monkeypatch.setattr(bs, '_sincronizar_motor', lambda *a, **k: estado['motor'].append((a, k)) or 1)
    import lifecycle_service
    monkeypatch.setattr(lifecycle_service, 'reactivate', lambda tid, actor=None: estado['reactivado'].append(tid))
    return estado


def _sql(estado, palabra):
    return [(s, p) for c in estado['cursores'] for s, p in c.sql if palabra in s]


def test_pago_tarde_de_la_panaderia(base):
    base['fila'] = {'proxima_fecha': D(2026, 9, 18), 'dia_corte': None, 'estado': 'activo'}
    nueva = bs.registrar_pago(14, '50000', fecha='2026-10-07', metodo='transferencia')
    assert nueva == D(2026, 10, 18)                       # no el 7 de noviembre
    insert = _sql(base, 'INSERT INTO tenant_pagos')[0][1]
    assert insert[5] == D(2026, 10, 18)                   # cubre_hasta
    assert _sql(base, 'UPDATE tenant_billing')[0][1] == (D(2026, 10, 18), 18, 14)
    assert base['motor'] == [((14, D(2026, 10, 18)), {'pago': True})]
    assert 'dia_corte=18' in base['auditoria'][0][1]['detalle']


def test_suspendido_que_queda_al_dia_se_reactiva_y_el_que_no_sigue_en_mora(base):
    base['fila'] = {'proxima_fecha': D(2026, 9, 18), 'dia_corte': 18, 'estado': 'suspendido'}
    bs.registrar_pago(14, '50000', fecha='2026-10-07')
    assert base['reactivado'] == [14]
    base['reactivado'].clear()
    base['fila'] = {'proxima_fecha': D(2026, 7, 18), 'dia_corte': 18, 'estado': 'suspendido'}
    assert bs.registrar_pago(14, '50000', fecha='2026-10-07') == D(2026, 8, 18)
    assert base['reactivado'] == []                       # debe más meses: sigue suspendido
    base['fila'] = {'proxima_fecha': D(2026, 7, 18), 'dia_corte': 18, 'estado': 'suspendido'}
    assert bs.registrar_pago(14, '150000', fecha='2026-10-07', meses=3) == D(2026, 10, 18)
    assert base['reactivado'] == [14]


def test_corregir_el_vencimiento_fija_el_dia_y_lleva_la_fecha_al_motor(base):
    base['fila'] = (D(2026, 11, 7),)                      # lo que dejó el error
    bs.set_config(14, proxima_fecha='2026-10-18', notas='corrige fecha de corte')
    update = _sql(base, 'UPDATE tenant_billing')[0]
    assert 'dia_corte = %s' in update[0] and tuple(update[1][:2]) == (D(2026, 10, 18), 18)
    assert base['motor'] == [((14, D(2026, 10, 18)), {'forzar': True})]
    # Guardar la configuración sin tocar la fecha no mueve el motor ni el día.
    base['motor'].clear()
    base['cursores'].clear()
    base['fila'] = (D(2026, 10, 18),)
    bs.set_config(14, monto_mensual='50000', proxima_fecha='2026-10-18')
    assert base['motor'] == [] and 'dia_corte' not in _sql(base, 'UPDATE tenant_billing')[0][0]


# ── Motor de cobro: misma fecha que el maestro ──────────────────
def test_sincronizar_motor_solo_adelanta_salvo_correccion(monkeypatch):
    llamadas = []
    monkeypatch.setattr(bs, '_motor_ejecutar', lambda sql, params, devolver=False: llamadas.append((sql, params)) or 1)
    bs._sincronizar_motor(14, D(2026, 10, 18), pago=True)
    sql, params = llamadas[-1]
    assert 'proximo_pago < %s' in sql and 'es_trial = FALSE' in sql and 'ultimo_recordatorio = NULL' in sql
    assert params == (D(2026, 10, 18), D(2026, 10, 18), 14, D(2026, 10, 18))
    bs._sincronizar_motor(14, D(2026, 10, 18), forzar=True)
    sql, params = llamadas[-1]
    assert 'proximo_pago < %s' not in sql and 'es_trial' not in sql and params == (D(2026, 10, 18), D(2026, 10, 18), 14)
    assert bs._sincronizar_motor(14, None) == 0


def test_si_el_motor_falla_el_pago_igual_queda(monkeypatch):
    def _rompe(*a, **k):
        raise RuntimeError('motor caído')
    monkeypatch.setattr(bs, '_motor_ejecutar', _rompe)
    assert bs._sincronizar_motor(14, D(2026, 10, 18)) == 0
