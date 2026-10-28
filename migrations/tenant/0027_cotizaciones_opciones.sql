-- ============================================================
-- 0027: Cotizaciones — opciones (alternativas que el cliente elige)
--
--   detalle_cotizacion.opcion      nombre de la opción a la que pertenece el
--                                  ítem (ej.: «Opción 1 — Intel»). NULL = ítem
--                                  común, que va en cualquier opción. Cada
--                                  opción sale en el PDF con su propio total y
--                                  las opciones NO se suman entre sí.
--   cotizaciones.opcion_elegida    la opción que aceptó el cliente, que se
--                                  elige al aprobar: a contabilidad va su total
--                                  y la factura electrónica lleva lo común y
--                                  esa opción.
--
-- Las cotizaciones existentes quedan en NULL: todo sigue sumando como antes.
-- Aditiva e idempotente. El código (routes/quotes.py, DDL_OPCIONES) tiene las
-- mismas sentencias y las ejecuta si faltan. Envuelta en comprobación de
-- existencia: hay bases heredadas sin el módulo de cotizaciones y `migrate_db`
-- no captura errores (un ALTER a secas abortaría «Actualizar app» de ese cliente).
-- ============================================================

DO $$
BEGIN
    IF to_regclass('public.detalle_cotizacion') IS NOT NULL THEN
        ALTER TABLE detalle_cotizacion ADD COLUMN IF NOT EXISTS opcion VARCHAR(80);
    ELSE
        RAISE NOTICE 'detalle_cotizacion no existe en esta base: se omite (cliente sin cotizaciones)';
    END IF;
    IF to_regclass('public.cotizaciones') IS NOT NULL THEN
        ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS opcion_elegida VARCHAR(80);
    ELSE
        RAISE NOTICE 'cotizaciones no existe en esta base: se omite (cliente sin cotizaciones)';
    END IF;
END $$;
