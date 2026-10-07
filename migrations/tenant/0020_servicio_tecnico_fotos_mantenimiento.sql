-- ============================================================
-- 0020: Servicio Técnico — fotos, mantenimientos y recordatorios
--
--   st_fotos            fotos del equipo (JPEG reducido + miniatura, sin
--                       metadatos). Viven en la base de cada cliente: el
--                       código es compartido entre tiendas, así ninguna
--                       foto queda en una carpeta común. Retirar una foto
--                       la marca activo = FALSE; no se borra.
--   st_mantenimientos   mantenimientos preventivos y correctivos hechos
--   st_equipos          + mant_cada_meses, mant_proximo (plan preventivo)
--   st_seguimientos     + motivo (recordatorios programados a mano)
--
-- Solo aditivo e idempotente. Debe ser IDÉNTICO a DDL_0020 de
-- CyberShop/app/services/servicio_tecnico_service.py (lo vigila
-- tests/test_servicio_tecnico.py).
-- ============================================================
CREATE TABLE IF NOT EXISTS st_fotos (
    id           SERIAL       PRIMARY KEY,
    equipo_id    INTEGER      NOT NULL REFERENCES st_equipos(id),
    orden_id     INTEGER      REFERENCES st_ordenes(id),
    momento      VARCHAR(20)  NOT NULL DEFAULT 'ficha',
    descripcion  VARCHAR(200),
    mime         VARCHAR(40)  NOT NULL,
    ancho        INTEGER,
    alto         INTEGER,
    bytes        INTEGER      NOT NULL,
    contenido    BYTEA        NOT NULL,
    miniatura    BYTEA        NOT NULL,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_por   INTEGER,
    creado_en    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_fotos_equipo ON st_fotos (equipo_id, activo);

CREATE TABLE IF NOT EXISTS st_mantenimientos (
    id             SERIAL        PRIMARY KEY,
    equipo_id      INTEGER       NOT NULL REFERENCES st_equipos(id),
    orden_id       INTEGER       REFERENCES st_ordenes(id),
    tipo           VARCHAR(20)   NOT NULL,
    fecha          DATE          NOT NULL DEFAULT CURRENT_DATE,
    descripcion    TEXT          NOT NULL,
    hallazgos      TEXT,
    tecnico_id     INTEGER,
    costo          NUMERIC(14,2),
    proxima_fecha  DATE,
    creado_por     INTEGER,
    creado_en      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_mantenimientos_equipo ON st_mantenimientos (equipo_id, fecha);

ALTER TABLE st_equipos ADD COLUMN IF NOT EXISTS mant_cada_meses SMALLINT;
ALTER TABLE st_equipos ADD COLUMN IF NOT EXISTS mant_proximo DATE;
ALTER TABLE st_seguimientos ADD COLUMN IF NOT EXISTS motivo VARCHAR(300);
CREATE INDEX IF NOT EXISTS ix_st_seguimientos_equipo ON st_seguimientos (equipo_id, estado);
