-- ============================================================
-- 0017: Conversación guardada del chat del panel (/admin/ia)
--
-- Cada intercambio del asistente del panel se guarda por usuario para que
-- la conversación siga al volver otro día, en otro navegador o en el
-- celular. Cada usuario solo usa la suya.
--
--   archivada = TRUE   «Nueva conversación»: deja de usarse como contexto
--   más de 30 días     el código la borra (memoria del chat, no un registro
--                      del negocio; la auditoría sigue en ia_consultas)
--
-- Lo de nómina o documentos internos se guarda pero nunca viaja al
-- respaldo en la nube.
--
-- Aditiva e idempotente. El código web crea la misma tabla si esta
-- migración aún no llegó al cliente (services/ia_conversacion.py); las
-- dos definiciones deben ser idénticas.
-- ============================================================

CREATE TABLE IF NOT EXISTS ia_conversacion (
    id          BIGSERIAL    PRIMARY KEY,
    usuario_id  INTEGER      NOT NULL,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    pregunta    VARCHAR(300) NOT NULL,
    respuesta   VARCHAR(2000) NOT NULL,
    herramienta VARCHAR(80),
    archivada   BOOLEAN      NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_ia_conversacion_usuario
    ON ia_conversacion (usuario_id, archivada, creado_en DESC);
