-- ============================================================
-- 0007: Slug automático para productos NUEVOS (SEO)
--
-- 0006 hizo backfill del slug, pero los INSERT (admin web, sync del
-- escritorio, carga por Excel) no lo llenan. Este trigger genera el
-- slug en el propio INSERT (y lo repara en UPDATE si quedó vacío),
-- con el mismo criterio del backfill: nombre → minúsculas sin tildes,
-- guiones, sufijo -id único.
--
-- Aditiva e idempotente.
-- ============================================================

CREATE OR REPLACE FUNCTION productos_touch_fecha() RETURNS trigger AS $$
BEGIN
    NEW.fecha_actualizacion := NOW();
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug := trim(both '-' from
            regexp_replace(
                lower(translate(COALESCE(NEW.nombre, ''),
                    'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')),
                '[^a-z0-9]+', '-', 'g'))
            || '-' || COALESCE(NEW.id, nextval(pg_get_serial_sequence('productos','id')));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- El trigger de UPDATE ya existe (0006) y usa esta misma función.
-- Añadir el de INSERT:
DROP TRIGGER IF EXISTS trg_productos_slug_insert ON productos;
CREATE TRIGGER trg_productos_slug_insert
    BEFORE INSERT ON productos
    FOR EACH ROW EXECUTE FUNCTION productos_touch_fecha();

-- Reparar los que hayan nacido sin slug entre 0006 y este cambio
UPDATE productos SET slug =
    trim(both '-' from
      regexp_replace(
        lower(translate(nombre, 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')),
        '[^a-z0-9]+', '-', 'g'))
    || '-' || id
WHERE slug IS NULL OR slug = '';
