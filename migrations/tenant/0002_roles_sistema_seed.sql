-- ============================================================
-- 0002: Homologación de roles del sistema en toda BD de tenant
--
-- Inspección real (jul-2026): a `cybershop` le faltaban los roles
-- 4 (Empleado) y 5 (Contador); a `achirasdemitierra` le faltaban
-- 4-7. Sin esas filas, la página Roles y Permisos no puede
-- configurarlos y el sync de usuarios del desktop (que resuelve el
-- rol por NOMBRE) falla al crear ese tipo de usuario.
--
-- Inserta SOLO los faltantes por id (no renombra existentes).
-- Corre después de 0001 (columnas es_sistema/base_rol_id/activo ya
-- existen con defaults correctos para estas filas).
-- Aditiva e idempotente.
-- ============================================================

INSERT INTO roles (id, nombre)
SELECT v.id, v.nombre FROM (VALUES
    (1, 'admin'), (2, 'usuario'), (3, 'cliente'),
    (4, 'Empleado'), (5, 'Contador'), (6, 'Mesero'), (7, 'Cajero')
) AS v(id, nombre)
WHERE NOT EXISTS (SELECT 1 FROM roles r WHERE r.id = v.id);

SELECT setval(pg_get_serial_sequence('roles','id'),
              GREATEST((SELECT COALESCE(MAX(id), 1) FROM roles), 7));
