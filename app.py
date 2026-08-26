"""CyberShopAdmin — panel SaaS de administración de tenants.

Levanta el servidor:
    run.bat  (Windows dev)         → http://localhost:5002
    systemd  (Linux prod)          → ver deploy/cybershop-admin.service
"""

import logging
import os
import sys
import time as _time

# Zona horaria del proceso del maestro (Colombia por defecto). El servidor corre
# en UTC; sin esto datetime.now()/logs quedarían adelantados. Override por env
# MASTER_TIMEZONE. Se fija antes de usar datetime.
os.environ['TZ'] = os.getenv('MASTER_TIMEZONE', 'America/Bogota')
if hasattr(_time, 'tzset'):
    _time.tzset()

from flask import Flask, redirect, url_for, g, jsonify, request
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from routes import register_blueprints
from auth import current_admin


csrf = CSRFProtect()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)

    # Confiar en X-Forwarded-* de Nginx (en prod)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Logging básico a stdout (systemd journal captura)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout,
    )

    register_blueprints(app)

    # API servidor-a-servidor: no usa cookies de navegador y autentica cada
    # request con X-Internal-Key. Mantenerla exenta evita romper la venta
    # automática; el resto del panel, incluido /autorizar-ip, sí exige CSRF.
    from routes.internal_api import bp as internal_api_bp
    csrf.exempt(internal_api_bp)

    # Inyectar admin actual en templates
    @app.context_processor
    def inject_admin():
        return {'admin': current_admin()}

    # Home → dashboard si logueado, login si no
    @app.before_request
    def reset_g_cache():
        # current_admin cachea en g — limpiar al inicio de cada request
        if hasattr(g, '_current_admin'):
            delattr(g, '_current_admin')

    @app.errorhandler(404)
    def not_found(_e):
        return 'Página no encontrada', 404

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        if request.is_json or request.path.startswith('/internal/'):
            return jsonify({'error': 'Token CSRF inválido o ausente'}), 400
        return ('Solicitud inválida o sesión vencida. Recarga la página e '
                'inténtalo nuevamente.', 400)

    @app.errorhandler(500)
    def server_error(_e):
        app.logger.exception('500 Internal Server Error')
        return 'Error interno del servidor', 500

    return app


app = create_app()


if __name__ == '__main__':
    # Bind a 127.0.0.1 por defecto: el panel solo se alcanza vía nginx (que
    # aplica el allow-list + TLS). Defensa en profundidad sobre el firewall.
    app.run(host=Config.HOST, port=Config.PORT, debug=False)
