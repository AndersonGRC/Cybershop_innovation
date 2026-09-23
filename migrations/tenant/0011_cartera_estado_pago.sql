-- ============================================================
-- 0011: Cartera — estado de pago de cotizaciones y cuentas de cobro
--
-- Hasta ahora, al aprobar una cotización o crear una cuenta de cobro el
-- sistema registraba el ingreso en contabilidad, pero no guardaba en
-- ninguna parte si esa plata REALMENTE entró. El dueño necesita marcar
-- lo que ya fue aprobado pero aún no le han desembolsado, y saber
-- cuánto le deben.
--
-- `estado_pago` NULL = "sin dato" (documento anterior a esta migración,
-- o que nadie ha revisado). Es distinto de 'pendiente', que significa
-- "lo revisamos y sigue sin pagarse". Por eso NO se rellena nada: las
-- filas viejas quedan en NULL y el negocio marca solo lo que le importa.
-- Valores: NULL | 'pendiente' | 'pagada'.
--
-- `fecha_vencimiento` es opcional; cuando está vacía, la app calcula la
-- mora a 30 días de la fecha del documento.
--
-- IMPORTANTE: esto NO toca la contabilidad. El movimiento de ingreso se
-- sigue registrando igual que siempre, así que ningún reporte ni cifra
-- histórica cambia para ningún cliente.
--
-- Aditiva e idempotente. Envuelta en comprobaciones de existencia porque
-- hay bases heredadas sin el módulo de cotizaciones o sin el de cuentas
-- de cobro, y `migrate_db` no captura errores: un ALTER a secas sobre una
-- tabla ausente abortaría el botón "Actualizar app" de ese cliente.
-- ============================================================

DO $$
BEGIN
    IF to_regclass('public.cotizaciones') IS NOT NULL THEN
        ALTER TABLE cotizaciones
            ADD COLUMN IF NOT EXISTS estado_pago       VARCHAR(20),
            ADD COLUMN IF NOT EXISTS fecha_pago        DATE,
            ADD COLUMN IF NOT EXISTS fecha_vencimiento DATE,
            ADD COLUMN IF NOT EXISTS nota_pago         VARCHAR(200);
    ELSE
        RAISE NOTICE 'cotizaciones no existe en esta base: se omite (cliente sin cotizaciones)';
    END IF;

    IF to_regclass('public.cuentas_cobro') IS NOT NULL THEN
        ALTER TABLE cuentas_cobro
            ADD COLUMN IF NOT EXISTS estado_pago       VARCHAR(20),
            ADD COLUMN IF NOT EXISTS fecha_pago        DATE,
            ADD COLUMN IF NOT EXISTS fecha_vencimiento DATE,
            ADD COLUMN IF NOT EXISTS nota_pago         VARCHAR(200);
    ELSE
        RAISE NOTICE 'cuentas_cobro no existe en esta base: se omite (cliente sin cuentas de cobro)';
    END IF;
END $$;

-- Índices parciales: las consultas de cartera solo buscan lo NO pagado.
DO $$
BEGIN
    IF to_regclass('public.cotizaciones') IS NOT NULL THEN
        CREATE INDEX IF NOT EXISTS idx_cotizaciones_estado_pago
            ON cotizaciones (estado_pago) WHERE estado_pago IS NOT NULL;
    END IF;
    IF to_regclass('public.cuentas_cobro') IS NOT NULL THEN
        CREATE INDEX IF NOT EXISTS idx_cuentas_cobro_estado_pago
            ON cuentas_cobro (estado_pago) WHERE estado_pago IS NOT NULL;
    END IF;
END $$;
