-- ============================================================
-- 0026: Facturación electrónica — columnas por venta en todas las bases
--
--   <tabla>.facturar_electronicamente  la venta pidió factura electrónica
--   <tabla>.factura_dian_id  (UUID)     documento del portal tributario
--
-- en pedidos, ventas_pos, restaurant_table_orders, cuentas_cobro y cotizaciones.
--
-- Por qué: el schema con que se crean los clientes nuevos solo las traía en
-- pedidos y ventas_pos. Sin ellas, «Mis cotizaciones» y «Mis cuentas de cobro»
-- (que las piden) salían vacías, y la venta facturada no quedaba marcada.
--
-- Bases heredadas donde `factura_dian_id` existe con otro tipo (un número, donde
-- no cabe un UUID): NO se cambia su tipo (regla: solo aditivo); se agrega
-- `factura_dian_uuid` y el código (routes/factura_electronica.py, columna_fe)
-- usa esa.
--
-- Aditiva e idempotente. Envuelta en comprobación de existencia de cada tabla:
-- hay bases sin restaurante o sin cotizaciones y `migrate_db` no captura errores
-- (un ALTER a secas abortaría «Actualizar app» de ese cliente). Ninguna venta
-- queda marcada: todo empieza en FALSE / NULL.
-- ============================================================

DO $$
DECLARE
    t    TEXT;
    tipo TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['pedidos', 'ventas_pos', 'restaurant_table_orders',
                             'cuentas_cobro', 'cotizaciones'] LOOP
        IF to_regclass('public.' || t) IS NULL THEN
            RAISE NOTICE '% no existe en esta base: se omite', t;
            CONTINUE;
        END IF;

        EXECUTE format('ALTER TABLE public.%I ADD COLUMN IF NOT EXISTS '
                       'facturar_electronicamente BOOLEAN DEFAULT FALSE', t);

        SELECT data_type INTO tipo
          FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = t AND column_name = 'factura_dian_id';

        IF tipo IS NULL THEN
            EXECUTE format('ALTER TABLE public.%I ADD COLUMN factura_dian_id UUID', t);
        ELSIF tipo NOT IN ('uuid', 'text', 'character varying') THEN
            RAISE NOTICE '%.factura_dian_id es %: se agrega factura_dian_uuid', t, tipo;
            EXECUTE format('ALTER TABLE public.%I ADD COLUMN IF NOT EXISTS factura_dian_uuid UUID', t);
        END IF;
    END LOOP;
END $$;
