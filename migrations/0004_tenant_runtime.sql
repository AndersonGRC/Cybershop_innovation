-- ============================================================
-- Control plane — Migración 0004 (CyberShopAdmin)
-- Tabla: tenant_runtime
--
-- Datos de ejecución por cliente en el modelo "una instancia por cliente,
-- mismo servidor, puerto distinto, dominio propio":
--   - port:            puerto local del gunicorn de ese cliente (único)
--   - subdomain:       <subdomain>.BASE_DOMAIN
--   - custom_domain:   dominio propio opcional del cliente
--   - instance_status: estado de la instancia (pending/running/stopped)
--
-- Aplicar con: python tools/apply_migrations.py
-- ============================================================

CREATE TABLE IF NOT EXISTS tenant_runtime (
    tenant_id       INT         PRIMARY KEY REFERENCES tenants(id),
    port            INT         UNIQUE,
    subdomain       TEXT        UNIQUE,
    custom_domain   TEXT        UNIQUE,
    instance_status TEXT        NOT NULL DEFAULT 'pending'
                    CHECK (instance_status IN ('pending', 'running', 'stopped', 'cancelled')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tenant_runtime IS
    'Runtime por cliente: puerto del gunicorn, subdominio y dominio propio.';
