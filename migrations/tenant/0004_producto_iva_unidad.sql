-- 0004_producto_iva_unidad.sql — IVA/impuesto y unidad de medida por producto.
-- Opcionales, con default seguro (sin IVA / por unidad). Aditivo e idempotente.
-- 'impuesto': excluido | 0 | 5 | 19   (excluido = sin IVA; base para facturación DIAN)
-- 'unidad_medida': unidad | libra | kilo | gramo | docena | litro

ALTER TABLE productos ADD COLUMN IF NOT EXISTS impuesto      varchar(12) DEFAULT 'excluido';
ALTER TABLE productos ADD COLUMN IF NOT EXISTS unidad_medida varchar(12) DEFAULT 'unidad';
