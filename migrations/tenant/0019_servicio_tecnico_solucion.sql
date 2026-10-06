-- ============================================================
-- 0019: Servicio Técnico — solución de la orden y su clasificación
--
--   solucion             qué se hizo (lo escribe el técnico)
--   falla_categoria      tipo de falla (pantalla, batería/carga, no enciende…)
--   componente           pieza afectada
--   solucion_categoria   tipo de solución (cambio de pieza, limpieza, formateo…)
--   etiquetas            palabras clave para buscar
--   resumen_caso         «problema → solución» en una frase
--   clasificacion_fuente 'reglas' | 'ia' | 'manual'
--
-- Así el historial se puede consultar: qué falla tuvo un equipo y cómo se
-- solucionó, qué fallas son más comunes, etc.
--
-- Aditiva e idempotente; idéntica a DDL_0019 de
-- services/servicio_tecnico_service.py (lo vigila una prueba).
-- ============================================================

ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS solucion TEXT;
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS falla_categoria VARCHAR(40);
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS componente VARCHAR(40);
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS solucion_categoria VARCHAR(40);
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS etiquetas VARCHAR(300);
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS resumen_caso VARCHAR(400);
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS clasificacion_fuente VARCHAR(10);
ALTER TABLE st_ordenes ADD COLUMN IF NOT EXISTS clasificado_en TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_st_ordenes_falla_categoria ON st_ordenes (falla_categoria);
CREATE INDEX IF NOT EXISTS ix_st_ordenes_solucion_categoria ON st_ordenes (solucion_categoria);
