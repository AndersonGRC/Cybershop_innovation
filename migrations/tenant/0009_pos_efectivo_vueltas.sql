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
-- ============================================================

ALTER TABLE ventas_pos
    ADD COLUMN IF NOT EXISTS efectivo_recibido NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS cambio            NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS cliente_email     VARCHAR(200),
    ADD COLUMN IF NOT EXISTS cliente_tipo_doc  VARCHAR(10);
