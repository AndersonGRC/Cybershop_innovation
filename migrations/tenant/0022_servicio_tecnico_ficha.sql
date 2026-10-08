-- ============================================================
-- 0022: Servicio Técnico — ficha técnica del equipo
--
--   st_equipos   + ficha (JSONB): contenido de la ficha técnica en PDF
--                  (estado rojo/azul, asignado a, características,
--                  vida útil, recomendaciones, problema, requerimientos)
--                + ficha_codigo: consecutivo de la ficha (no se repite
--                  entre equipos activos)
--
-- Aditiva e idempotente. El código (services/servicio_tecnico_service.py,
-- DDL_0022) tiene exactamente las mismas sentencias.
-- ============================================================

ALTER TABLE st_equipos ADD COLUMN IF NOT EXISTS ficha JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE st_equipos ADD COLUMN IF NOT EXISTS ficha_codigo VARCHAR(40);
CREATE UNIQUE INDEX IF NOT EXISTS ux_st_equipos_ficha_codigo ON st_equipos (lower(ficha_codigo))
    WHERE ficha_codigo IS NOT NULL AND activo;
