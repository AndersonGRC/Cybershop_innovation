-- ============================================================
-- 0014: Consumo del respaldo de IA en la nube
--
-- El asistente trabaja con el equipo de IA del dueño. Si ese equipo lleva
-- varios minutos sin responder, entra un respaldo en la nube que SÍ se
-- cobra por token. Esta tabla es el contador de ese gasto, por mes:
--
--   llamadas        cuántas veces se usó el respaldo
--   tokens_*        consumo real reportado por la API
--   costo_usd       estimado con los precios configurados
--   aviso_enviado   si ya se avisó por correo que empezó el cobro
--
-- Sirve para tres cosas: frenar en seco al llegar al tope mensual, avisar
-- la primera vez que se usa en el mes, y poder mirar después cuánto se
-- gastó y por qué.
--
-- Una fila por mes y por cliente (cada uno en su propia base). Aditiva e
-- idempotente; la app también la crea si falta.
-- ============================================================

CREATE TABLE IF NOT EXISTS ia_uso_nube (
    periodo         VARCHAR(7) PRIMARY KEY,      -- AAAA-MM
    llamadas        INTEGER NOT NULL DEFAULT 0,
    tokens_entrada  BIGINT  NOT NULL DEFAULT 0,
    tokens_salida   BIGINT  NOT NULL DEFAULT 0,
    costo_usd       NUMERIC(10,4) NOT NULL DEFAULT 0,
    aviso_enviado   BOOLEAN NOT NULL DEFAULT FALSE,
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
