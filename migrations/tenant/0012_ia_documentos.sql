-- ============================================================
-- 0012: Índice de textos del asistente (RAG)
--
-- El asistente responde los HECHOS con consultas fijas (precio, stock,
-- horario). Pero las preguntas de prosa —«¿hacen domicilios?», «¿cuánto
-- se demora el envío?», «¿quiénes son ustedes?»— no se resuelven con SQL:
-- hay que buscarlas en los textos que cada negocio escribió.
--
-- Esta tabla es ese índice, por cliente: productos, servicios, preguntas
-- frecuentes, páginas y blog, en un formato único y buscable.
--
--   canal_publico  El chat del sitio SOLO ve las filas marcadas aquí.
--                  Es la línea que separa lo que el público puede leer
--                  de lo interno.
--   tsv            Texto ya preparado para buscar (to_tsvector español).
--                  Lo escribe el indexador; no es columna generada porque
--                  unaccent() no es IMMUTABLE.
--
-- Es un índice, no una fuente: se puede borrar y reconstruir entero desde
-- las tablas reales. Por eso no guarda nada que no esté ya en otra parte.
--
-- Aditiva e idempotente. Las extensiones se intentan y, si el usuario de
-- la base no tiene permiso para crearlas, se sigue sin ellas: la búsqueda
-- funciona igual, solo menos fina con las tildes. Van dentro de un bloque
-- con EXCEPTION a propósito — `migrate_db` no captura errores, y un
-- CREATE EXTENSION fallido dejaría al cliente sin poder actualizarse.
-- ============================================================

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS unaccent;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'unaccent no se pudo instalar (%): se busca sin normalizar tildes', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pg_trgm no se pudo instalar (%): sin búsqueda por parecido', SQLERRM;
END $$;

CREATE TABLE IF NOT EXISTS ia_documentos (
    id             BIGSERIAL PRIMARY KEY,
    fuente         VARCHAR(30)  NOT NULL,     -- producto | servicio | faq | pagina | publicacion | blog
    fuente_id      VARCHAR(60)  NOT NULL,     -- id o slug en su tabla de origen
    titulo         VARCHAR(300) NOT NULL,
    texto          TEXT         NOT NULL DEFAULT '',
    url            VARCHAR(400),
    canal_publico  BOOLEAN      NOT NULL DEFAULT FALSE,
    actualizado_en TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    tsv            tsvector
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ia_documentos_fuente
    ON ia_documentos (fuente, fuente_id);
CREATE INDEX IF NOT EXISTS idx_ia_documentos_tsv
    ON ia_documentos USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_ia_documentos_publico
    ON ia_documentos (canal_publico) WHERE canal_publico;

-- Búsqueda por parecido (tolera errores de escritura) — solo si pg_trgm quedó.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
        CREATE INDEX IF NOT EXISTS idx_ia_documentos_titulo_trgm
            ON ia_documentos USING GIN (titulo gin_trgm_ops);
    END IF;
END $$;
