-- ============================================================
-- 0009: Cobro en efectivo en el POS — monto recibido y vueltas
--
-- Al cobrar en EFECTIVO el cajero digita cuánto dinero le entrega
-- el cliente y el sistema calcula las vueltas. Ambos datos quedan
-- guardados para la tirilla, la reimpresión desde el historial y
-- la auditoría de caja.
--
-- Se dejan NULL-ables a propósito: NULL = "sin dato" (venta que no
-- fue en efectivo, o anterior a esta migración), que es distinto de
-- cambio = 0 ("el cliente pagó con el valor exacto").
--
-- `cliente_email` es para facturación electrónica: la DIAN exige un
-- correo del adquiriente y el POS no lo capturaba, por lo que toda
-- venta marcada para facturar fallaba con 422.
--
-- Aditiva e idempotente.
--
-- Se envuelve en una comprobación de existencia porque no todos los clientes
-- tienen el módulo POS: hay bases heredadas sin la tabla `ventas_pos`, y un
-- ALTER a secas las haría fallar. Como `migrate_db` no captura errores, esa
-- excepción abortaría el botón "Actualizar app" de ese cliente y ni siquiera
-- llegaría a reiniciarse. Si la tabla aparece más adelante, basta con volver a
-- marcar esta migración como pendiente.
-- ============================================================

DO $$
BEGIN
    IF to_regclass('public.ventas_pos') IS NOT NULL THEN
        ALTER TABLE ventas_pos
            ADD COLUMN IF NOT EXISTS efectivo_recibido NUMERIC(14,2),
            ADD COLUMN IF NOT EXISTS cambio            NUMERIC(14,2),
            ADD COLUMN IF NOT EXISTS cliente_email     VARCHAR(200),
            ADD COLUMN IF NOT EXISTS cliente_tipo_doc  VARCHAR(10);
    ELSE
        RAISE NOTICE 'ventas_pos no existe en esta base: se omite la 0009 (cliente sin POS)';
    END IF;
END $$;
