-- ============================================================
-- 0025: Cotizaciones — notas adicionales
--
--   cotizaciones.notas_adicionales  texto libre que el negocio escribe al hacer
--                                   la cotización (impuestos, condiciones de
--                                   pago, entrega, garantía…). Sale al final del
--                                   PDF, antes de la firma; vacía = no sale.
--
-- Las cotizaciones existentes quedan en NULL: sus PDF no cambian.
-- Aditiva e idempotente. El código (routes/quotes.py, DDL_NOTAS) tiene la misma
-- sentencia y la ejecuta si la columna aún no existe. Envuelta en comprobación de
-- existencia: hay bases heredadas sin el módulo de cotizaciones y `migrate_db` no
-- captura errores (un ALTER a secas abortaría «Actualizar app» de ese cliente).
-- ============================================================

DO $$
BEGIN
    IF to_regclass('public.cotizaciones') IS NOT NULL THEN
        ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS notas_adicionales TEXT;
    ELSE
        RAISE NOTICE 'cotizaciones no existe en esta base: se omite (cliente sin cotizaciones)';
    END IF;
END $$;
