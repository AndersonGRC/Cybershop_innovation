-- ============================================================
-- 0008: Respuesta del negocio a las reseñas de producto
--
-- El dueño/staff puede responder cada reseña (con ayuda de la IA,
-- botón "✦ Sugerir respuesta" en Moderación de reseñas). La
-- respuesta se muestra en la página pública del producto bajo el
-- comentario ("Respuesta de {empresa}") — contenido fresco (SEO)
-- y confianza para el comprador.
--
-- Aditiva e idempotente.
-- ============================================================

ALTER TABLE producto_comentarios
    ADD COLUMN IF NOT EXISTS respuesta TEXT,
    ADD COLUMN IF NOT EXISTS respuesta_fecha TIMESTAMPTZ;
