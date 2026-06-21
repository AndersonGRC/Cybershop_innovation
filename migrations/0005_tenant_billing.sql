-- ============================================================
-- Control plane — Migración 0005 (CyberShopAdmin)
-- Cobros / mora por tenant: tenant_billing + tenant_pagos
--
--   - tenant_billing: monto mensual, próximo vencimiento, flag de auto-suspensión.
--   - tenant_pagos:   historial de pagos registrados (manual / web).
--
-- Regla: tras 2 meses (60 días) de mora, los morosos con auto_suspender=TRUE se
-- suspenden (cron diario + botón). El tenant 1 (sitio del operador) nace con
-- auto_suspender=FALSE → nunca se auto-suspende.
--
-- Aplicar con: python tools/apply_migrations.py   (idempotente)
-- ============================================================

CREATE TABLE IF NOT EXISTS tenant_billing (
    tenant_id      INT           PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    monto_mensual  NUMERIC(12,2) NOT NULL DEFAULT 0,
    proxima_fecha  DATE,                                   -- próximo vencimiento
    auto_suspender BOOLEAN       NOT NULL DEFAULT TRUE,
    notas          TEXT,
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenant_pagos (
    id             SERIAL        PRIMARY KEY,
    tenant_id      INT           NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    monto          NUMERIC(12,2) NOT NULL,
    fecha          DATE          NOT NULL DEFAULT CURRENT_DATE,
    metodo         VARCHAR(40),
    nota           TEXT,
    cubre_hasta    DATE,                                   -- vencimiento al que llevó el pago
    registrado_por VARCHAR(120),
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tenant_pagos_tenant ON tenant_pagos(tenant_id, fecha DESC);

COMMENT ON TABLE tenant_billing IS 'Cobro mensual por cliente: monto, próximo vencimiento y auto-suspensión por mora.';
COMMENT ON TABLE tenant_pagos   IS 'Historial de pagos registrados por cliente (manual o web).';

-- El tenant 1 (sitio principal del operador) NUNCA se auto-suspende por mora.
INSERT INTO tenant_billing (tenant_id, auto_suspender)
VALUES (1, FALSE)
ON CONFLICT (tenant_id) DO UPDATE SET auto_suspender = FALSE;
