-- ============================================================
-- 0010: Registro de consultas del Asistente IA
--
-- Una fila por pregunta al chat del negocio: qué herramientas de datos
-- usó, si respondió bien y cuánto tardó. No guarda respuestas ni cifras.
--
-- Sirve para tres cosas:
--  1. Medir el asistente (tiempos, errores, qué se consulta más).
--  2. Saber qué preguntan los clientes y la IA aún no sabe responder
--     (`pregunta_sin_herramienta`, que la app vacía a los 90 días).
--  3. Auditar consultas de información sensible (p. ej. nómina): quién
--     consultó y sobre quién (`sensible`, `objetivo`). Por eso las filas
--     no se borran.
--
-- La app también crea la tabla si falta (CREATE TABLE IF NOT EXISTS),
-- así el chat no depende de que esta migración ya se haya aplicado.
--
-- Aditiva e idempotente. No toca tablas existentes.
-- ============================================================

CREATE TABLE IF NOT EXISTS ia_consultas (
    id BIGSERIAL PRIMARY KEY,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_id INTEGER,
    rol_id INTEGER,
    canal VARCHAR(20) NOT NULL DEFAULT 'web',
    herramientas TEXT[] NOT NULL DEFAULT '{}',
    ok BOOLEAN NOT NULL DEFAULT TRUE,
    error VARCHAR(300),
    ms INTEGER,
    sensible VARCHAR(40),
    objetivo VARCHAR(120),
    pregunta_sin_herramienta VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS idx_ia_consultas_creado_en ON ia_consultas (creado_en);
