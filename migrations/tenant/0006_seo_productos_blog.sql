-- ============================================================
-- 0006: SEO — slugs y fecha de actualización de productos + blog
--
-- (a) productos.slug: URLs semánticas /producto/<id>-<slug> (el id
--     sigue mandando; el slug es decorativo/SEO). Backfill desde el
--     nombre. productos.fecha_actualizacion: lastmod REAL del sitemap.
-- (b) blog_posts: artículos con página propia, schema Article y
--     sitemap. El blog se muestra solo si el tenant activa la sección
--     pública 'mostrar_blog' (default OFF — cada dueño decide).
--
-- Aditiva e idempotente (contrato de tenant_migrations.py).
-- ============================================================

ALTER TABLE productos ADD COLUMN IF NOT EXISTS slug VARCHAR(160);
ALTER TABLE productos ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMPTZ DEFAULT NOW();

-- Backfill de slug: nombre → minúsculas sin tildes, guiones, único por sufijo -id
UPDATE productos SET slug =
    trim(both '-' from
      regexp_replace(
        lower(translate(nombre,
          'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')),
        '[^a-z0-9]+', '-', 'g'))
    || '-' || id
WHERE slug IS NULL OR slug = '';

CREATE INDEX IF NOT EXISTS idx_productos_slug ON productos(slug);

-- Mantener fecha_actualizacion al día en cualquier UPDATE (trigger simple)
CREATE OR REPLACE FUNCTION productos_touch_fecha() RETURNS trigger AS $$
BEGIN
    NEW.fecha_actualizacion := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_productos_touch ON productos;
CREATE TRIGGER trg_productos_touch
    BEFORE UPDATE ON productos
    FOR EACH ROW EXECUTE FUNCTION productos_touch_fecha();

-- Blog
CREATE TABLE IF NOT EXISTS blog_posts (
    id               SERIAL PRIMARY KEY,
    slug             VARCHAR(180) UNIQUE NOT NULL,
    titulo           VARCHAR(200) NOT NULL,
    meta_descripcion VARCHAR(170),
    extracto         VARCHAR(400),
    cuerpo_html      TEXT NOT NULL DEFAULT '',
    imagen           VARCHAR(300),
    keyword_objetivo VARCHAR(120),
    estado           VARCHAR(15) NOT NULL DEFAULT 'borrador',  -- borrador|publicado
    autor            VARCHAR(120),
    fecha_publicado  TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blog_estado ON blog_posts(estado, fecha_publicado DESC);
