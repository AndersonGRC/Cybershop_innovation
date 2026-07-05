-- ============================================================
-- 0001: Roles y Permisos configurables por el Propietario
--
-- (a) Extiende `roles` para soportar roles personalizados creados
--     por el dueño (es_sistema=FALSE, base_rol_id = rol que copia).
-- (b) Crea `rol_permisos`: OVERRIDES de la matriz de permisos.
--     Tabla VACÍA = "usar los recomendados" (grupos de security.py).
--     Solo se guardan excepciones; "Restaurar recomendado" = DELETE.
--
-- Aditiva e idempotente (contrato de tenant_migrations.py).
-- ============================================================

ALTER TABLE roles ADD COLUMN IF NOT EXISTS es_sistema  BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE roles ADD COLUMN IF NOT EXISTS base_rol_id INTEGER REFERENCES roles(id);
ALTER TABLE roles ADD COLUMN IF NOT EXISTS descripcion VARCHAR(200);
ALTER TABLE roles ADD COLUMN IF NOT EXISTS activo      BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE roles ADD COLUMN IF NOT EXISTS creado_en   TIMESTAMPTZ DEFAULT NOW();

-- Alinear la secuencia de roles.id: los 7 roles semilla pudieron insertarse
-- con id explícito y dejar la secuencia atrás (los INSERT nuevos fallarían).
SELECT setval(pg_get_serial_sequence('roles','id'),
              GREATEST((SELECT COALESCE(MAX(id), 1) FROM roles), 7));

CREATE TABLE IF NOT EXISTS rol_permisos (
    rol_id     INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    modulo     VARCHAR(50) NOT NULL,          -- module_code de tenant_features
    ver        BOOLEAN NOT NULL DEFAULT FALSE,
    operar     BOOLEAN NOT NULL DEFAULT FALSE,
    eliminar   BOOLEAN NOT NULL DEFAULT FALSE,
    updated_by INTEGER,                        -- usuarios.id (auditoría)
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (rol_id, modulo)
);
CREATE INDEX IF NOT EXISTS idx_rol_permisos_rol ON rol_permisos(rol_id);

COMMENT ON TABLE rol_permisos IS
  'Overrides de permisos por rol y módulo. Vacía = usar recomendados del código (security.py). Jerarquía normalizada al guardar: eliminar⇒operar⇒ver.';
