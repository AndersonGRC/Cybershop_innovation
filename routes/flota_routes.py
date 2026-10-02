"""Vistas de toda la flota (solo lectura): cobros e inteligencia artificial."""

from flask import Blueprint, render_template

from auth import login_required
import fleet_service

bp = Blueprint('flota', __name__)


@bp.route('/cobros')
@login_required
def cobros():
    error = None
    try:
        datos = fleet_service.cobros_flota()
    except Exception as exc:  # noqa: BLE001
        datos, error = {'clientes': [], 'resumen': {}, 'dias_por_vencer': fleet_service.DIAS_POR_VENCER}, str(exc)
    return render_template('flota_cobros.html', error=error, **datos)


@bp.route('/ia')
@login_required
def ia():
    error = None
    try:
        datos = fleet_service.ia_flota()
    except Exception as exc:  # noqa: BLE001
        datos, error = {'clientes': [], 'servidores': [], 'resumen': {}, 'nombres_modulos': {}}, str(exc)
    return render_template('flota_ia.html', error=error, **datos)
