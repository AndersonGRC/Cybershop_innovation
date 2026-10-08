-- ============================================================
-- 0021: Servicio Técnico — documentos del equipo e importación
--
--   st_importaciones    lotes de «Traer desde Excel o PDF»: archivos,
--                       filas leídas (para revisar antes de guardar),
--                       ajustes y lo que se creó (para poder deshacerlo)
--   st_documentos       PDF, Excel e imágenes de fichas guardados en la
--                       base del cliente. Quitar uno lo marca
--                       activo = FALSE; no se borra.
--   st_equipos          + importacion_id (lote del que salió)
--   st_mantenimientos   + importacion_id, + activo (deshacer un lote
--                       retira sus mantenimientos sin borrarlos)
--
-- Aditiva e idempotente. El código (services/servicio_tecnico_service.py,
-- DDL_0021) tiene exactamente las mismas sentencias.
-- ============================================================

CREATE TABLE IF NOT EXISTS st_importaciones (
    id              SERIAL       PRIMARY KEY,
    estado          VARCHAR(20)  NOT NULL DEFAULT 'leyendo',
    archivos        JSONB        NOT NULL DEFAULT '[]'::jsonb,
    filas           JSONB        NOT NULL DEFAULT '[]'::jsonb,
    ajustes         JSONB        NOT NULL DEFAULT '{}'::jsonb,
    resultado       JSONB,
    creado_por      INTEGER,
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    importado_por   INTEGER,
    importado_en    TIMESTAMPTZ,
    deshecho_por    INTEGER,
    deshecho_en     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_st_importaciones_creado ON st_importaciones (creado_en);

CREATE TABLE IF NOT EXISTS st_documentos (
    id              SERIAL        PRIMARY KEY,
    equipo_id       INTEGER       REFERENCES st_equipos(id),
    orden_id        INTEGER       REFERENCES st_ordenes(id),
    importacion_id  INTEGER       REFERENCES st_importaciones(id),
    nombre          VARCHAR(200)  NOT NULL,
    descripcion     VARCHAR(200),
    mime            VARCHAR(120)  NOT NULL,
    bytes           INTEGER       NOT NULL,
    huella          VARCHAR(64)   NOT NULL,
    contenido       BYTEA         NOT NULL,
    texto           TEXT,
    activo          BOOLEAN       NOT NULL DEFAULT TRUE,
    creado_por      INTEGER,
    creado_en       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_documentos_equipo ON st_documentos (equipo_id, activo);
CREATE INDEX IF NOT EXISTS ix_st_documentos_importacion ON st_documentos (importacion_id);
CREATE INDEX IF NOT EXISTS ix_st_documentos_huella ON st_documentos (huella);

ALTER TABLE st_equipos ADD COLUMN IF NOT EXISTS importacion_id INTEGER;
ALTER TABLE st_mantenimientos ADD COLUMN IF NOT EXISTS importacion_id INTEGER;
ALTER TABLE st_mantenimientos ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS ix_st_equipos_importacion ON st_equipos (importacion_id);
