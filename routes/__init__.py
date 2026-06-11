"""Registro de blueprints."""

from routes.auth_routes import bp as auth_bp
from routes.dashboard_routes import bp as dashboard_bp
from routes.tenant_routes import bp as tenant_bp
from routes.internal_api import bp as internal_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(internal_bp)
