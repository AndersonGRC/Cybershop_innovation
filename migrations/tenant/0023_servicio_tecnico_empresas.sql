-- ============================================================
-- 0023: Servicio Técnico — carpetas por empresa
--
--   st_empresas  carpeta de cada empresa cliente: sus equipos (los
--                computadores de sus funcionarios) van juntos. La clave
--                (nombre sin tildes ni forma jurídica) no se repite
--                entre carpetas activas.
--   st_equipos   + empresa_id: la carpeta del equipo; sin empresa =
--                «Particulares» (los computadores normales).
--
-- Aditiva e idempotente. El código (services/servicio_tecnico_service.py,
-- DDL_0023) tiene exactamente las mismas sentencias.
-- ============================================================

CREATE TABLE IF NOT EXISTS st_empresas (
    id               SERIAL        PRIMARY KEY,
    nombre           VARCHAR(160)  NOT NULL,
    clave            VARCHAR(160)  NOT NULL,
    nit              VARCHAR(30),
    crm_contacto_id  INTEGER,
    activo           BOOLEAN       NOT NULL DEFAULT TRUE,
    creado_por       INTEGER,
    creado_en        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_st_empresas_clave ON st_empresas (clave) WHERE activo;
ALTER TABLE st_equipos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES st_empresas(id);
CREATE INDEX IF NOT EXISTS ix_st_equipos_empresa ON st_equipos (empresa_id);
