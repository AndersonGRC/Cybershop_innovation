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
