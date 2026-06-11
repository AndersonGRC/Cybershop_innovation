"""API interna del maestro — venta automática de clientes.

Endpoints JSON consumidos por el app principal (mismo servidor) cuando un
pago de plan se aprueba. NO son para humanos:
- El maestro escucha solo en 127.0.0.1 (nadie externo llega aquí).
- Cada request exige el header X-Internal-Key == Config.INTERNAL_API_KEY
  (secreto compartido en el env de ambas apps; comparación constante).
- Si INTERNAL_API_KEY no está configurada, la API queda deshabilitada (503).
"""

import hmac
from functools import wraps

from flask import Blueprint, jsonify, request

from config import Config

bp = Blueprint('internal_api', __name__, url_prefix='/internal/api/v1')


def require_internal_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = (getattr(Config, 'INTERNAL_API_KEY', '') or '').strip()
        if not expected:
            return jsonify({'error': 'API interna deshabilitada (sin INTERNAL_API_KEY)'}), 503
        recibido = (request.headers.get('X-Internal-Key') or '').strip()
        if not recibido or not hmac.compare_digest(recibido, expected):
            return jsonify({'error': 'No autorizado'}), 401
        return fn(*args, **kwargs)
    return wrapper


@bp.route('/tenants/create', methods=['POST'])
@require_internal_key
def create_tenant_internal():
    """Crea un cliente completo (BD + seed + control plane + key + instancia +
    dominio + SSL) y aplica los módulos del plan. Tarda 30-90s (SSL).

    Body: {slug, nombre, email, plan}  →  201 {tenant_id, domain, admin_email,
    admin_password, client_code, port, ...} | 400 error de validación."""
    import tenant_service
    data = request.get_json(silent=True) or {}
    slug = (data.get('slug') or '').strip().lower()
    nombre = (data.get('nombre') or '').strip()
    email = (data.get('email') or '').strip().lower()
    plan = (data.get('plan') or 'estandar').strip()
    try:
        result = tenant_service.create_tenant(
            slug=slug, nombre=nombre,
            key_label='Venta automática', admin_email=email)
    except tenant_service.TenantCreationError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        return jsonify({'error': f'Error interno creando el cliente: {exc}'}), 500

    try:
        import module_service as ms
        if plan in ms.PLAN_MODULES:
            ms.apply_plan(result['tenant_id'], plan)
            result['modulos_plan'] = plan
    except Exception as exc:  # noqa: BLE001
        # No abortar: el tenant existe; los módulos se ajustan desde el panel.
        result['modulos_plan'] = f'fallo apply_plan: {exc}'

    return jsonify(result), 201


def _accion_lifecycle(tenant_id, accion):
    import tenant_service
    import lifecycle_service as lc
    if not tenant_service.get_tenant(tenant_id):
        return jsonify({'error': 'Tenant no existe'}), 404
    try:
        if accion == 'suspend':
            lc.suspend(tenant_id)
        else:
            lc.reactivate(tenant_id)
        return jsonify({'ok': True, 'accion': accion, 'tenant_id': tenant_id}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({'error': str(exc)}), 500


@bp.route('/tenants/<int:tenant_id>/suspend', methods=['POST'])
@require_internal_key
def suspend_internal(tenant_id):
    """Suspende la instancia (no-pago). Mismo camino que el botón del panel."""
    return _accion_lifecycle(tenant_id, 'suspend')


@bp.route('/tenants/<int:tenant_id>/reactivate', methods=['POST'])
@require_internal_key
def reactivate_internal(tenant_id):
    """Reactiva la instancia (renovación pagada)."""
    return _accion_lifecycle(tenant_id, 'reactivate')
