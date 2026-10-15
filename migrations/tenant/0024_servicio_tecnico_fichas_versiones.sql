-- ============================================================
-- 0024: Servicio Técnico — versiones de la ficha técnica
--
--   st_fichas_versiones  cada cambio de la ficha de un equipo (al volver a
--                        importar su Excel o PDF, al guardarla a mano o al
--                        editar el equipo) deja cómo quedó; la primera vez
--                        también cómo estaba antes. La versión anterior
--                        nunca se pierde. Deshacer una importación deja su
--                        versión activo = FALSE: nada se borra.
--
-- Aditiva e idempotente. El código (services/servicio_tecnico_service.py,
-- DDL_0024) tiene exactamente las mismas sentencias.
-- ============================================================

CREATE TABLE IF NOT EXISTS st_fichas_versiones (
    id              SERIAL       PRIMARY KEY,
    equipo_id       INTEGER      NOT NULL REFERENCES st_equipos(id),
    version         INTEGER      NOT NULL DEFAULT 1,
    estado          JSONB        NOT NULL DEFAULT '{}'::jsonb,
    cambios         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    origen          VARCHAR(20)  NOT NULL DEFAULT 'manual',
    importacion_id  INTEGER,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_por      INTEGER,
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_fichas_versiones_equipo ON st_fichas_versiones (equipo_id, id);
CREATE INDEX IF NOT EXISTS ix_st_fichas_versiones_importacion ON st_fichas_versiones (importacion_id);
