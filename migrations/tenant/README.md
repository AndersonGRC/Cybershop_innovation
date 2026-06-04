# Migraciones de tenant (aditivas)

Cada `.sql` aquí se aplica a la BD de **cada cliente** con `tools/migrate_tenants.py`.

## Reglas (para NO afectar lo existente)
- **Solo aditivo e idempotente:** `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`.
- **Nunca** `DROP`, `TRUNCATE`, ni `ALTER` destructivo (cambiar tipo/NOT NULL sin default, renombrar).
- Nombrar en orden: `0001_descripcion.sql`, `0002_...`.

## Flujo de actualización
1. Cambiar el código del app (CyberShop) que necesita el cambio de esquema.
2. Escribir aquí la migración aditiva correspondiente.
3. En el servidor: `git pull` (maestro y app) → `python tools/migrate_tenants.py` → reiniciar instancias.

Los clientes **nuevos** ya traen todo por el dump del schema; estas migraciones
los marcan como aplicados automáticamente al crearse (idempotente igual).
