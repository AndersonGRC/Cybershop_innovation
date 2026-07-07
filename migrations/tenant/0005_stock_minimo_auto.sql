-- 0005_stock_minimo_auto.sql — Stock mínimo automático = 5 (no editable por el usuario).
-- Cambia el default a 5 y pone en 5 los que estaban en 0/NULL. Aditivo e idempotente.

ALTER TABLE productos ALTER COLUMN stock_minimo SET DEFAULT 5;
UPDATE productos SET stock_minimo = 5 WHERE COALESCE(stock_minimo, 0) = 0;
