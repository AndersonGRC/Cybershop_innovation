"""Configuración centralizada de CyberShopAdmin."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.cybershop.conf')


class Config:
    # --- Flask ---
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError(
            "FLASK_SECRET_KEY no está configurada en .cybershop.conf"
        )
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600 * 8  # 8 horas

    # --- Server ---
    PORT = int(os.getenv('PORT', '5002'))
    # 127.0.0.1: el panel solo se sirve detrás de nginx (allow-list + TLS).
    HOST = os.getenv('HOST', '127.0.0.1')

    # --- Postgres: control plane ---
    CP_DB_NAME     = os.getenv('CONTROL_PLANE_DB_NAME', 'saas_control_plane')
    CP_DB_HOST     = os.getenv('CONTROL_PLANE_DB_HOST', 'localhost')
    CP_DB_PORT     = int(os.getenv('CONTROL_PLANE_DB_PORT', '5432'))
    CP_DB_USER     = os.getenv('CONTROL_PLANE_DB_USER', 'postgres')
    CP_DB_PASSWORD = os.getenv('CONTROL_PLANE_DB_PASSWORD', '')

    # --- Postgres: para crear tenants ---
    PG_HOST     = os.getenv('DB_HOST', 'localhost')
    PG_PORT     = int(os.getenv('DB_PORT', '5432'))
    PG_USER     = os.getenv('DB_USER', 'postgres')
    PG_PASSWORD = os.getenv('DB_PASSWORD', '')

    # --- Cifrado AES-GCM ---
    KMS_KEY = os.getenv('KMS_KEY', '')

    # --- PIN de acceso al panel maestro (numérico). Vacío = usar email/password ---
    # API interna (venta automática): secreto compartido con el app principal
    INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', '')

    MASTER_PIN = os.getenv('MASTER_PIN', '')

    # --- Facturación electrónica (microservicio FacturacionDIAN) ---
    # URL base del API del microservicio (incluye /api/v1) y su MASTER_API_KEY.
    # Con esto el maestro provisiona tenants DIAN y escribe las DIAN_* en el
    # env de cada instancia al activar el módulo facturacion_electronica.
    DIAN_SERVICE_URL = os.getenv('DIAN_SERVICE_URL', 'http://127.0.0.1:5003/api/v1')
    DIAN_MASTER_KEY = os.getenv('DIAN_MASTER_KEY', '')
    # URL pública del panel DIAN (SSO desde la app del cliente). Vacío = /ui.
    DIAN_UI_URL = os.getenv('DIAN_UI_URL', '')

    # --- Tenant provisioning ---
    # DB maestra (plantilla de estructura) de la que se genera el schema dump.
    MASTER_DB_NAME = os.getenv('MASTER_DB_NAME', 'cybershop')
    TENANT_SCHEMA_FILE = os.getenv(
        'TENANT_SCHEMA_FILE',
        str(Path(__file__).parent / 'schema' / 'tenant_schema.sql'),
    )
    # Seed mínimo (roles, admin, colores, secciones) aplicado tras el schema.
    TENANT_SEED_FILE = os.getenv(
        'TENANT_SEED_FILE',
        str(Path(__file__).parent / 'schema' / 'tenant_seed.sql'),
    )
    PSQL_BIN = os.getenv('PSQL_BIN', 'psql')

    # --- EnvironmentFile por instancia (integraciones + runtime por cliente) ---
    # Local dev: carpeta del repo. Producción: /etc/cybershop.
    INSTANCE_ENV_DIR = os.getenv(
        'INSTANCE_ENV_DIR',
        str(Path(__file__).parent / 'instances'),
    )

    # --- Asistente IA (Ollama) ---
    # El servidor de IA es el MISMO equipo para todos los tenants (la PC del
    # proveedor). Se usa como valor por defecto del campo AI_BASE_URL para que
    # configurar un cliente sea, en la práctica, solo elegir el modelo.
    AI_DEFAULT_BASE_URL = os.getenv('AI_DEFAULT_BASE_URL', 'http://10.200.0.3:11434')
    # Caché de la lista de modelos por base_url: permite que el desplegable de
    # "Modelo" siga funcionando aunque la PC de IA esté apagada al abrir el panel.
    AI_MODELS_CACHE_FILE = os.getenv(
        'AI_MODELS_CACHE_FILE',
        str(Path(INSTANCE_ENV_DIR) / '.ai_models_cache.json'),
    )

    # --- Aprovisionamiento de instancia + dominio (1C) ---
    BASE_DOMAIN = os.getenv('BASE_DOMAIN', 'cybershopcol.com')   # subdominios *.BASE_DOMAIN
    CERTBOT_EMAIL = os.getenv('CERTBOT_EMAIL', 'cybershop.digitalsales@gmail.com')
    SERVER_IP = os.getenv('SERVER_IP', '38.134.148.47')          # IP a la que apuntar el DNS
    APP_DIR = os.getenv('APP_DIR', '/var/www/CyberShop')          # código compartido (prod)
    # Tenant primario (sitio principal): corre en el servicio `cybershop`, NO en
    # la plantilla `cybershop@<slug>`. Para que el restart del panel apunte al
    # servicio correcto y sus integraciones se apliquen en vivo.
    PRIMARY_TENANT_SLUG = os.getenv('PRIMARY_TENANT_SLUG', 'cyber-t001')
    PORT_MIN = int(os.getenv('PORT_MIN', '8100'))
    PORT_MAX = int(os.getenv('PORT_MAX', '8999'))
    BACKUP_DIR = os.getenv('BACKUP_DIR', '/var/backups/cybershop')

    # --- Reverse proxy (cuadra el dominio del cliente con su puerto) ---
    PROXY_BACKEND = os.getenv('PROXY_BACKEND', 'nginx')           # 'nginx' | 'caddy'
    NGINX_SITES_AVAILABLE = os.getenv('NGINX_SITES_AVAILABLE', '/etc/nginx/sites-available')
    NGINX_SITES_ENABLED = os.getenv('NGINX_SITES_ENABLED', '/etc/nginx/sites-enabled')
    CADDY_SITES_DIR = os.getenv('CADDY_SITES_DIR', '/etc/caddy/sites')
    # Cert wildcard *.BASE_DOMAIN (opcional): si se define, los subdominios usan
    # HTTPS de inmediato sin certbot por dominio.
    WILDCARD_SSL_CERT = os.getenv('WILDCARD_SSL_CERT', '')
    WILDCARD_SSL_KEY = os.getenv('WILDCARD_SSL_KEY', '')
