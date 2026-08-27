"""Dashboard home — stats agregadas."""

from flask import Blueprint, render_template

from auth import login_required
import tenant_service


bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    stats = tenant_service.dashboard_stats()
    return render_template('dashboard.html', stats=stats)


@bp.route('/salud')
@login_required
def salud():
    """Muestra el último resultado del monitor de salud de la flota (lo escribe el
    cron cada ~10 min en /var/lib/cybershop/health_last.txt)."""
    import os
    import time
    path = '/var/lib/cybershop/health_last.txt'
    reporte = None
    edad = None
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            reporte = f.read()
        edad = int(time.time() - os.path.getmtime(path))
    except Exception:  # noqa: BLE001
        pass
    return render_template('salud.html', reporte=reporte, edad=edad)


@bp.route('/auditoria')
@login_required
def auditoria():
    """Vista global de acciones sensibles (suspensiones, pagos, avisos…) de todos
    los clientes. Registro append-only (audit_service)."""
    import audit_service
    filas = audit_service.listar_con_slug(limite=200)
    return render_template('auditoria.html', filas=filas)
