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

    # --- Tenant provisioning ---
    TENANT_SCHEMA_FILE = os.getenv(
        'TENANT_SCHEMA_FILE',
        str(Path(__file__).parent.parent / 'CyberShop' / 'app' / 'migrate_backup_db.sql'),
    )
    PSQL_BIN = os.getenv('PSQL_BIN', 'psql')
