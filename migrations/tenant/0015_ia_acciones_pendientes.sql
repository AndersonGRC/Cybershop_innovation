-- Propuestas operativas del Asistente IA: cada tenant tiene su propia tabla.
-- La confirmación y la operación se hacen en una única transacción por BD.
CREATE TABLE IF NOT EXISTS ia_acciones_pendientes (
    id UUID PRIMARY KEY,
    tipo VARCHAR(40) NOT NULL,
    estado VARCHAR(16) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'ejecutada', 'cancelada')),
    usuario_id INTEGER NOT NULL,
    rol_id INTEGER NOT NULL,
    db_nombre VARCHAR(128) NOT NULL,
    payload JSONB,
    resumen TEXT NOT NULL,
    detalles JSONB NOT NULL DEFAULT '{}'::jsonb,
    resultado JSONB,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    vence_en TIMESTAMPTZ NOT NULL,
    decidido_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ia_acciones_usuario_estado
    ON ia_acciones_pendientes (usuario_id, estado, vence_en);
