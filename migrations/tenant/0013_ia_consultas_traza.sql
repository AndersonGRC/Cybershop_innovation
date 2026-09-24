-- ============================================================
-- 0013: Trazabilidad de las respuestas del asistente
--
-- `ia_consultas` ya guardaba qué herramientas se usaron, si salió bien y
-- cuánto tardó. Faltaba lo que permite entender POR QUÉ respondió así:
--
--   intencion   qué se entendió que preguntaban (código de la capacidad)
--   via         cómo se resolvió: 'keyword' (palabras clave, sin modelo),
--               'rag' (índice de textos), 'modelo' (lo eligió la IA) o
--               'determinista' (respuesta armada sin redacción)
--   motor       qué máquina la atendió: 'A' servidor · 'B' la buena · 'C' profundo
--   documentos  ids del índice que se citaron, si hubo
--
-- Con esto se puede medir de verdad: cuánto se resuelve sin gastar modelo,
-- qué tanto se usa cada motor y de dónde salió cada respuesta.
--
-- No guarda la respuesta ni las cifras, igual que antes. La pregunta se
-- guarda SOLO cuando nada supo responderla, y se borra a los 90 días.
--
-- Aditiva e idempotente. La app también crea la tabla si falta, así que
-- se comprueba su existencia antes de alterarla.
-- ============================================================

DO $$
BEGIN
    IF to_regclass('public.ia_consultas') IS NOT NULL THEN
        ALTER TABLE ia_consultas
            ADD COLUMN IF NOT EXISTS intencion  VARCHAR(40),
            ADD COLUMN IF NOT EXISTS via        VARCHAR(20),
            ADD COLUMN IF NOT EXISTS motor      VARCHAR(4),
            ADD COLUMN IF NOT EXISTS documentos BIGINT[];
    ELSE
        RAISE NOTICE 'ia_consultas no existe todavía: la crea la app con estas columnas';
    END IF;
END $$;
