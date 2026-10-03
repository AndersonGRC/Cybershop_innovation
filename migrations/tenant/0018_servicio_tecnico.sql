-- ============================================================
-- 0018: Servicio Técnico (computadores, celulares, tablets, televisores, UPS…)
--
--   st_equipos       ficha de cada equipo atendido (+ extras por tipo en JSONB)
--   st_cambios       piezas cambiadas (batería, RAM, disco…) con próxima revisión
--   st_ordenes       orden de servicio (recepción → diagnóstico → cotización →
--                    reparación → entrega → garantía); la clave del equipo va cifrada
--   st_eventos       bitácora de la orden y del equipo
--   st_seguimientos  alertas programadas para el cliente y el dueño
--
-- El cliente es un contacto del CRM (crm_contactos): sin llave foránea hacia
-- el CRM para no cambiar cómo borra el CRM.
--
-- Aditiva e idempotente. El código web crea las mismas tablas si esta
-- migración aún no llegó al cliente (services/servicio_tecnico_service.py,
-- DDL); las dos definiciones deben ser idénticas.
-- ============================================================

CREATE TABLE IF NOT EXISTS st_equipos (
    id                    SERIAL       PRIMARY KEY,
    crm_contacto_id       INTEGER      NOT NULL,
    tipo                  VARCHAR(30)  NOT NULL,
    marca                 VARCHAR(80),
    modelo                VARCHAR(120),
    serial                VARCHAR(120),
    imei                  VARCHAR(20),
    color                 VARCHAR(40),
    sistema_operativo     VARCHAR(120),
    procesador            VARCHAR(160),
    ram                   VARCHAR(60),
    almacenamiento        VARCHAR(120),
    pantalla              VARCHAR(80),
    extras                JSONB        NOT NULL DEFAULT '{}'::jsonb,
    info_sistema_original TEXT,
    resumen_ia            TEXT,
    sugerencias_ia        JSONB,
    notas                 TEXT,
    activo                BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_por            INTEGER,
    creado_en             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    actualizado_en        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_equipos_contacto ON st_equipos (crm_contacto_id);
CREATE INDEX IF NOT EXISTS ix_st_equipos_serial ON st_equipos (lower(serial));
CREATE INDEX IF NOT EXISTS ix_st_equipos_imei ON st_equipos (imei);

CREATE TABLE IF NOT EXISTS st_ordenes (
    id                SERIAL        PRIMARY KEY,
    numero            VARCHAR(20)   UNIQUE,
    equipo_id         INTEGER       NOT NULL REFERENCES st_equipos(id),
    crm_contacto_id   INTEGER       NOT NULL,
    estado            VARCHAR(20)   NOT NULL DEFAULT 'recibido',
    falla_reportada   TEXT          NOT NULL,
    estado_fisico     TEXT,
    accesorios        TEXT,
    clave_cifrada     TEXT,
    diagnostico       TEXT,
    prediagnostico_ia TEXT,
    cotizacion_id     INTEGER,
    tecnico_id        INTEGER,
    valor_estimado    NUMERIC(14,2),
    valor_final       NUMERIC(14,2),
    fecha_recibido    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    fecha_promesa     DATE,
    fecha_listo       TIMESTAMPTZ,
    fecha_entregado   TIMESTAMPTZ,
    garantia_dias     INTEGER       NOT NULL DEFAULT 30,
    garantia_hasta    DATE,
    token_publico     VARCHAR(48)   NOT NULL UNIQUE,
    creado_por        INTEGER,
    creado_en         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    actualizado_en    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_ordenes_estado ON st_ordenes (estado);
CREATE INDEX IF NOT EXISTS ix_st_ordenes_equipo ON st_ordenes (equipo_id);
CREATE INDEX IF NOT EXISTS ix_st_ordenes_contacto ON st_ordenes (crm_contacto_id);
CREATE INDEX IF NOT EXISTS ix_st_ordenes_cotizacion ON st_ordenes (cotizacion_id);

CREATE TABLE IF NOT EXISTS st_eventos (
    id          BIGSERIAL    PRIMARY KEY,
    orden_id    INTEGER      REFERENCES st_ordenes(id),
    equipo_id   INTEGER      REFERENCES st_equipos(id),
    tipo        VARCHAR(20)  NOT NULL,
    detalle     TEXT,
    usuario_id  INTEGER,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_eventos_orden ON st_eventos (orden_id, creado_en);
CREATE INDEX IF NOT EXISTS ix_st_eventos_equipo ON st_eventos (equipo_id, creado_en);

CREATE TABLE IF NOT EXISTS st_cambios (
    id                SERIAL       PRIMARY KEY,
    equipo_id         INTEGER      NOT NULL REFERENCES st_equipos(id),
    orden_id          INTEGER      REFERENCES st_ordenes(id),
    componente        VARCHAR(80)  NOT NULL,
    detalle           TEXT,
    fecha             DATE         NOT NULL DEFAULT CURRENT_DATE,
    proxima_revision  DATE,
    creado_por        INTEGER,
    creado_en         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_cambios_equipo ON st_cambios (equipo_id);
CREATE INDEX IF NOT EXISTS ix_st_cambios_revision ON st_cambios (proxima_revision);

CREATE TABLE IF NOT EXISTS st_seguimientos (
    id                SERIAL       PRIMARY KEY,
    orden_id          INTEGER      REFERENCES st_ordenes(id),
    equipo_id         INTEGER      REFERENCES st_equipos(id),
    cambio_id         INTEGER      REFERENCES st_cambios(id),
    cotizacion_id     INTEGER,
    crm_contacto_id   INTEGER,
    tipo              VARCHAR(40)  NOT NULL,
    fecha_programada  DATE         NOT NULL,
    canal             VARCHAR(20),
    estado            VARCHAR(20)  NOT NULL DEFAULT 'pendiente',
    calificacion      SMALLINT,
    comentario        TEXT,
    hecho_por         INTEGER,
    hecho_en          TIMESTAMPTZ,
    creado_en         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_st_seguimientos_pendientes ON st_seguimientos (estado, fecha_programada);
