-- ============================================================
-- Control plane — Migración 0003 (CyberShopAdmin)
-- Tabla: admin_users
--
-- Usuarios del panel de administración SaaS (CyberShopAdmin).
-- Separados de usuarios_globales (que son para autenticación API
-- de clientes finales).
--
-- Aplicar con:
--   psql -d saas_control_plane -f migrations/0003_admin_users.sql
-- o:
--   python tools/apply_migrations.py
-- ============================================================

CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE IF NOT EXISTS admin_users (
    id            SERIAL      PRIMARY KEY,
    email         CITEXT      UNIQUE NOT NULL,
    contraseña    TEXT        NOT NULL,                  -- werkzeug pbkdf2:sha256
    nombre        TEXT        NOT NULL,
    is_super      BOOLEAN     NOT NULL DEFAULT FALSE,
    active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_users_active
    ON admin_users(active) WHERE active;

COMMENT ON TABLE admin_users IS
    'Usuarios del panel de administración SaaS (CyberShopAdmin). Distintos de usuarios_globales.';

COMMENT ON COLUMN admin_users.is_super IS
    'Reservado para futuros niveles de permiso. Hoy todos los activos tienen acceso total.';
