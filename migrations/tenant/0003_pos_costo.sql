-- 0003_pos_costo.sql — Costo/COGS y stock mínimo (aditivo, idempotente).
-- Habilita: margen (precio - costo), reporte de rentabilidad y alertas de stock bajo.

ALTER TABLE productos          ADD COLUMN IF NOT EXISTS costo          numeric(12,2) DEFAULT 0;
ALTER TABLE productos          ADD COLUMN IF NOT EXISTS stock_minimo   integer       DEFAULT 0;

-- Snapshot del costo al momento de la venta (margen histórico correcto aunque el costo cambie después).
ALTER TABLE detalle_venta_pos  ADD COLUMN IF NOT EXISTS costo_unitario numeric       DEFAULT 0;
