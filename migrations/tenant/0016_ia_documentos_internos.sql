-- ============================================================
-- 0016: Documentos internos del asistente (índice privado)
--
-- Procedimientos, políticas y manuales que escribe el dueño en
-- /admin/ia/documentos. SOLO los lee el asistente del panel, según el rol:
--
--   visibilidad = 'administracion'  dueño y superadministrador
--   visibilidad = 'equipo'          todo el que usa el asistente del panel
--
-- Nunca son públicos: el indexador los copia a ia_documentos (0012) con
-- canal_publico = FALSE, y el chat del sitio solo busca filas públicas.
-- Tampoco se envían al respaldo en la nube.
--
-- Archivar no borra: activo = FALSE los saca de las respuestas.
--
-- Aditiva e idempotente. El código web crea la misma tabla si esta
-- migración aún no llegó al cliente (services/ia_rag/internos.py); las
-- dos definiciones deben ser idénticas.
-- ============================================================

CREATE TABLE IF NOT EXISTS ia_documentos_internos (
    id              SERIAL PRIMARY KEY,
    titulo          VARCHAR(200) NOT NULL,
    texto           TEXT         NOT NULL,
    visibilidad     VARCHAR(20)  NOT NULL DEFAULT 'administracion',
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_por      INTEGER,
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    actualizado_por INTEGER,
    actualizado_en  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
