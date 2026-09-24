# Migraciones de tenant (aditivas)

Cada `.sql` aquí se aplica a la BD de **cada cliente** mediante el botón
«Actualizar app»/«Solo migrar BD» (una base) o `tools/migrate_tenants.py`
(procedimiento masivo coordinado).

## Reglas (para NO afectar lo existente)
- **Solo aditivo e idempotente:** `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`.
- **Nunca** `DROP`, `TRUNCATE`, ni `ALTER` destructivo (cambiar tipo/NOT NULL sin default, renombrar).
- Nombrar en orden: `0001_descripcion.sql`, `0002_...`.

## Flujo de actualización
1. Cambiar el código del app (CyberShop) que necesita el cambio de esquema.
2. Escribir aquí la migración aditiva correspondiente.
3. Publicar **primero este repo maestro**, para que el botón encuentre los SQL
   nuevos. Luego publicar el código web en `origin/master` y usar «Actualizar
   app» por cliente: integra código global, aplica las migraciones pendientes
   de **esa BD** y recarga **esa instancia**. Si se requiere migrar todas las
   bases antes de integrar el código, usar un procedimiento manual coordinado
   con `tools/migrate_tenants.py`; no confundirlo con el botón individual.

El botón no revierte el código global si una migración falla. Véase
`CyberShop/app/docs/IA_ACTUALIZACION_CLIENTES.md` en el repositorio web para
los prerrequisitos, el canario y la verificación por cliente.

Los clientes **nuevos** ya traen todo por el dump del schema; estas migraciones
los marcan como aplicados automáticamente al crearse (idempotente igual).
