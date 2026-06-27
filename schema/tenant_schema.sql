--
-- PostgreSQL database dump
--

\restrict kFrxy6ODMimYfeyl6fOB1Bdv6jOWjzWCrbfLY65uFHhvbKsKvKvjbmOcY9EGKiS

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: trg_generos_set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_generos_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: trg_productos_set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_productos_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: trg_usuarios_set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_usuarios_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: backup_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backup_config (
    id integer DEFAULT 1 NOT NULL,
    clave_hash character varying(255),
    actualizado_por integer,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT backup_config_id_check CHECK ((id = 1))
);


--
-- Name: backups_db; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backups_db (
    id integer NOT NULL,
    nombre_archivo character varying(255) NOT NULL,
    nombre_descarga character varying(255) NOT NULL,
    tipo character varying(20) NOT NULL,
    comprimido boolean DEFAULT false NOT NULL,
    tamano_bytes bigint,
    creado_por integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT backups_db_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['full'::character varying, 'schema'::character varying])::text[])))
);


--
-- Name: backups_db_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.backups_db_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: backups_db_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.backups_db_id_seq OWNED BY public.backups_db.id;


--
-- Name: cliente_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente_config (
    clave character varying NOT NULL,
    valor text,
    tipo character varying,
    grupo character varying,
    descripcion text,
    orden integer
);


--
-- Name: config_secciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_secciones (
    clave character varying(100) NOT NULL,
    valor character varying(500) NOT NULL,
    descripcion character varying(300)
);


--
-- Name: contabilidad_cierres; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contabilidad_cierres (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    total_ingresos numeric(14,2) DEFAULT 0,
    total_egresos numeric(14,2) DEFAULT 0,
    saldo numeric(14,2) DEFAULT 0,
    notas text,
    usuario_id integer,
    created_at timestamp without time zone DEFAULT now(),
    total_retenciones numeric(14,2) DEFAULT 0
);


--
-- Name: contabilidad_cierres_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contabilidad_cierres_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contabilidad_cierres_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contabilidad_cierres_id_seq OWNED BY public.contabilidad_cierres.id;


--
-- Name: contabilidad_movimientos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contabilidad_movimientos (
    id integer NOT NULL,
    tipo character varying(10) NOT NULL,
    categoria character varying(60) DEFAULT 'otro'::character varying NOT NULL,
    descripcion text NOT NULL,
    monto numeric(14,2) NOT NULL,
    fecha date DEFAULT CURRENT_DATE NOT NULL,
    referencia_tipo character varying(30),
    referencia_id integer,
    notas text,
    usuario_id integer,
    auto_generado boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    monto_bruto numeric(14,2),
    retefuente_pct numeric(6,3) DEFAULT 0,
    retefuente_monto numeric(14,2) DEFAULT 0,
    iva_pct numeric(6,3) DEFAULT 0,
    iva_monto numeric(14,2) DEFAULT 0,
    reteiva_pct numeric(6,3) DEFAULT 0,
    reteiva_monto numeric(14,2) DEFAULT 0,
    reteica_pct numeric(6,3) DEFAULT 0,
    reteica_monto numeric(14,2) DEFAULT 0,
    total_retenciones numeric(14,2) DEFAULT 0,
    CONSTRAINT contabilidad_movimientos_monto_check CHECK ((monto >= (0)::numeric)),
    CONSTRAINT contabilidad_movimientos_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['ingreso'::character varying, 'egreso'::character varying])::text[])))
);


--
-- Name: contabilidad_movimientos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contabilidad_movimientos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contabilidad_movimientos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contabilidad_movimientos_id_seq OWNED BY public.contabilidad_movimientos.id;


--
-- Name: contabilidad_plantillas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contabilidad_plantillas (
    id integer NOT NULL,
    tipo character varying(10) NOT NULL,
    categoria character varying(50) NOT NULL,
    descripcion character varying(200) NOT NULL,
    monto_bruto numeric(14,2) NOT NULL,
    notas text,
    activo boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT contabilidad_plantillas_monto_bruto_check CHECK ((monto_bruto > (0)::numeric)),
    CONSTRAINT contabilidad_plantillas_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['ingreso'::character varying, 'egreso'::character varying])::text[])))
);


--
-- Name: contabilidad_plantillas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contabilidad_plantillas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contabilidad_plantillas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contabilidad_plantillas_id_seq OWNED BY public.contabilidad_plantillas.id;


--
-- Name: cotizaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cotizaciones (
    id integer NOT NULL,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cliente_nombre text NOT NULL,
    cliente_documento text,
    logo_url text,
    total numeric DEFAULT 0,
    pdf_path text,
    cliente_direccion text DEFAULT ''::text,
    cliente_ciudad text DEFAULT ''::text,
    cliente_telefono text DEFAULT ''::text,
    cliente_representante text DEFAULT ''::text,
    cliente_cargo text DEFAULT ''::text,
    cliente_localidad text DEFAULT ''::text,
    estado character varying(20) DEFAULT 'pendiente'::character varying,
    crm_contacto_id integer
);


--
-- Name: cotizaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cotizaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cotizaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cotizaciones_id_seq OWNED BY public.cotizaciones.id;


--
-- Name: crm_actividades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_actividades (
    id integer NOT NULL,
    contacto_id integer NOT NULL,
    tipo character varying(30) NOT NULL,
    asunto character varying(300) NOT NULL,
    descripcion text,
    fecha_actividad timestamp without time zone NOT NULL,
    usuario_id integer,
    asignado_a integer,
    google_event_id text,
    invitados_emails text
);


--
-- Name: crm_actividades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crm_actividades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crm_actividades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crm_actividades_id_seq OWNED BY public.crm_actividades.id;


--
-- Name: crm_contactos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_contactos (
    id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    nombre character varying(200) NOT NULL,
    empresa character varying(200),
    cargo character varying(100),
    email character varying(255),
    telefono character varying(50),
    whatsapp character varying(50),
    sitio_web character varying(300),
    direccion text,
    ciudad character varying(100),
    usuario_id integer,
    notas text,
    origen character varying(100),
    foto_path text,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tags text[] DEFAULT '{}'::text[]
);


--
-- Name: crm_contactos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crm_contactos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crm_contactos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crm_contactos_id_seq OWNED BY public.crm_contactos.id;


--
-- Name: crm_oportunidades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_oportunidades (
    id integer NOT NULL,
    contacto_id integer NOT NULL,
    titulo character varying(200) NOT NULL,
    descripcion text,
    monto_estimado numeric(14,2) DEFAULT 0,
    probabilidad integer DEFAULT 50,
    etapa character varying(30) DEFAULT 'prospecto'::character varying NOT NULL,
    fuente character varying(60),
    cotizacion_id integer,
    asignado_a integer,
    fecha_cierre_est date,
    fecha_cierre_real date,
    motivo_perdida character varying(160),
    notas text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT crm_oportunidades_etapa_check CHECK (((etapa)::text = ANY ((ARRAY['prospecto'::character varying, 'calificado'::character varying, 'propuesta'::character varying, 'negociacion'::character varying, 'ganada'::character varying, 'perdida'::character varying])::text[]))),
    CONSTRAINT crm_oportunidades_probabilidad_check CHECK (((probabilidad >= 0) AND (probabilidad <= 100)))
);


--
-- Name: crm_oportunidades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crm_oportunidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crm_oportunidades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crm_oportunidades_id_seq OWNED BY public.crm_oportunidades.id;


--
-- Name: crm_tareas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_tareas (
    id integer NOT NULL,
    contacto_id integer NOT NULL,
    titulo character varying(300) NOT NULL,
    descripcion text,
    prioridad character varying(10) NOT NULL,
    estado character varying(20) DEFAULT 'pendiente'::character varying NOT NULL,
    fecha_limite date,
    asignado_a integer,
    creado_por integer,
    completada_en timestamp without time zone,
    recordatorio_diario boolean DEFAULT false,
    snooze_hasta date,
    google_event_id text,
    invitados_emails text
);


--
-- Name: crm_tareas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crm_tareas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crm_tareas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crm_tareas_id_seq OWNED BY public.crm_tareas.id;


--
-- Name: cuentas_cobro; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cuentas_cobro (
    id integer NOT NULL,
    consecutivo character varying(20) NOT NULL,
    fecha date NOT NULL,
    cliente_nombre character varying(255) NOT NULL,
    cliente_nit character varying(50) NOT NULL,
    cliente_direccion character varying(255),
    cliente_telefono character varying(50),
    cliente_ciudad character varying(100),
    contractor_nombre character varying(255) NOT NULL,
    contractor_id character varying(50) NOT NULL,
    contractor_telefono character varying(50),
    contractor_email character varying(255),
    texto_pago text,
    total numeric NOT NULL,
    pdf_path character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    crm_contacto_id integer
);


--
-- Name: cuentas_cobro_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cuentas_cobro_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cuentas_cobro_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cuentas_cobro_id_seq OWNED BY public.cuentas_cobro.id;


--
-- Name: detalle_cotizacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalle_cotizacion (
    id integer NOT NULL,
    cotizacion_id integer,
    descripcion text NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric NOT NULL,
    subtotal numeric NOT NULL,
    imagen_url text,
    descuento_porc numeric DEFAULT 0,
    iva_porc numeric DEFAULT 0
);


--
-- Name: detalle_cotizacion_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalle_cotizacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalle_cotizacion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalle_cotizacion_id_seq OWNED BY public.detalle_cotizacion.id;


--
-- Name: detalle_cuenta_cobro; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalle_cuenta_cobro (
    id integer NOT NULL,
    cuenta_id integer,
    fecha_labor date,
    descripcion text NOT NULL,
    valor numeric NOT NULL
);


--
-- Name: detalle_cuenta_cobro_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalle_cuenta_cobro_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalle_cuenta_cobro_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalle_cuenta_cobro_id_seq OWNED BY public.detalle_cuenta_cobro.id;


--
-- Name: detalle_pedidos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalle_pedidos (
    id integer NOT NULL,
    pedido_id integer,
    producto_nombre character varying(200),
    cantidad integer,
    precio_unitario numeric(12,2),
    subtotal numeric(12,2)
);


--
-- Name: detalle_pedidos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalle_pedidos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalle_pedidos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalle_pedidos_id_seq OWNED BY public.detalle_pedidos.id;


--
-- Name: detalle_venta_pos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalle_venta_pos (
    id integer NOT NULL,
    venta_id integer,
    producto_id integer,
    descripcion character varying(300) NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric NOT NULL,
    subtotal numeric NOT NULL
);


--
-- Name: detalle_venta_pos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalle_venta_pos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalle_venta_pos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalle_venta_pos_id_seq OWNED BY public.detalle_venta_pos.id;


--
-- Name: generos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.generos (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: generos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.generos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: generos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.generos_id_seq OWNED BY public.generos.id;


--
-- Name: google_calendar_watches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.google_calendar_watches (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    channel_id text NOT NULL,
    resource_id text,
    expiry timestamp with time zone
);


--
-- Name: google_calendar_watches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.google_calendar_watches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: google_calendar_watches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.google_calendar_watches_id_seq OWNED BY public.google_calendar_watches.id;


--
-- Name: google_oauth_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.google_oauth_tokens (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    access_token text NOT NULL,
    refresh_token text,
    token_expiry timestamp with time zone,
    scope text,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: google_oauth_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.google_oauth_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: google_oauth_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.google_oauth_tokens_id_seq OWNED BY public.google_oauth_tokens.id;


--
-- Name: inventario_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventario_log (
    id integer NOT NULL,
    producto_id integer,
    tipo character varying(20),
    cantidad integer,
    stock_anterior integer,
    stock_nuevo integer,
    motivo text,
    usuario_id integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: inventario_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventario_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventario_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventario_log_id_seq OWNED BY public.inventario_log.id;


--
-- Name: nomina_arl_niveles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_arl_niveles (
    id integer NOT NULL,
    anio integer NOT NULL,
    nivel character varying(10) NOT NULL,
    porcentaje numeric NOT NULL
);


--
-- Name: nomina_arl_niveles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_arl_niveles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_arl_niveles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_arl_niveles_id_seq OWNED BY public.nomina_arl_niveles.id;


--
-- Name: nomina_asientos_contables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_asientos_contables (
    id integer NOT NULL,
    periodo_id integer,
    liquidacion_id integer,
    fecha date NOT NULL,
    total_debito numeric,
    total_credito numeric,
    estado character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    descripcion character varying(255)
);


--
-- Name: nomina_asientos_contables_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_asientos_contables_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_asientos_contables_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_asientos_contables_id_seq OWNED BY public.nomina_asientos_contables.id;


--
-- Name: nomina_asientos_detalle; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_asientos_detalle (
    id integer NOT NULL,
    asiento_id integer,
    cuenta_contable character varying(20),
    descripcion character varying(100),
    debito numeric,
    credito numeric,
    tercero_nit character varying(20),
    centro_costo character varying(20)
);


--
-- Name: nomina_contratistas_pila; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_contratistas_pila (
    id integer NOT NULL,
    periodo_id integer,
    empleado_id integer,
    numero_planilla character varying(50),
    fecha_pago date,
    valor_pagado numeric,
    archivo_soporte character varying(255),
    verificado boolean,
    created_at timestamp without time zone
);


--
-- Name: nomina_detalle; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_detalle (
    id integer NOT NULL,
    periodo_id integer,
    empleado_id integer,
    total_devengado numeric,
    total_deducido numeric,
    neto_pagar numeric,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    dias_trabajados integer,
    sueldo_basico numeric,
    auxilio_transporte numeric,
    horas_extras numeric,
    recargos numeric,
    comisiones numeric,
    bonificaciones numeric,
    incapacidades numeric,
    licencias numeric,
    salud_empleado numeric,
    pension_empleado numeric,
    fondo_solidaridad numeric,
    retencion_fuente numeric,
    prestamos numeric,
    otras_deducciones numeric,
    salud_empleador numeric,
    pension_empleador numeric,
    arl numeric,
    sena numeric,
    icbf numeric,
    ccf numeric,
    cesantias_provision numeric,
    intereses_provision numeric,
    prima_provision numeric,
    vacaciones_provision numeric
);


--
-- Name: nomina_detalle_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_detalle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_detalle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_detalle_id_seq OWNED BY public.nomina_detalle.id;


--
-- Name: nomina_empleados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_empleados (
    id integer NOT NULL,
    tipo_documento character varying NOT NULL,
    numero_documento character varying NOT NULL,
    nombres character varying NOT NULL,
    apellidos character varying NOT NULL,
    email character varying,
    telefono character varying,
    direccion character varying,
    fecha_ingreso date NOT NULL,
    fecha_retiro date,
    tipo_vinculacion character varying NOT NULL,
    cargo character varying,
    salario_base numeric NOT NULL,
    nivel_arl character varying,
    banco character varying,
    tipo_cuenta character varying,
    numero_cuenta character varying,
    eps character varying,
    fondo_pension character varying,
    fondo_cesantias character varying,
    activo boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_empleados_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_empleados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_empleados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_empleados_id_seq OWNED BY public.nomina_empleados.id;


--
-- Name: nomina_liquidaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_liquidaciones (
    id integer NOT NULL,
    empleado_id integer,
    fecha_retiro date NOT NULL,
    motivo_retiro character varying,
    total_pagar numeric,
    estado character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    dias_liquidacion integer,
    salario_base_liquidacion numeric,
    cesantias numeric,
    intereses_cesantias numeric,
    prima_servicios numeric,
    vacaciones numeric,
    indemnizacion numeric,
    salarios_pendientes numeric,
    deducciones_pendientes numeric
);


--
-- Name: nomina_liquidaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_liquidaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_liquidaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_liquidaciones_id_seq OWNED BY public.nomina_liquidaciones.id;


--
-- Name: nomina_novedades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_novedades (
    id integer NOT NULL,
    periodo_id integer,
    empleado_id integer,
    tipo_novedad character varying NOT NULL,
    cantidad numeric NOT NULL,
    valor_unitario numeric,
    valor_total numeric,
    fecha_novedad date,
    observacion text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_novedades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_novedades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_novedades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_novedades_id_seq OWNED BY public.nomina_novedades.id;


--
-- Name: nomina_parafiscales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_parafiscales (
    id integer NOT NULL,
    anio integer NOT NULL,
    ccf numeric NOT NULL,
    icbf numeric NOT NULL,
    sena numeric NOT NULL,
    tope_exoneracion numeric,
    created_at timestamp without time zone
);


--
-- Name: nomina_parametros; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_parametros (
    id integer NOT NULL,
    anio integer,
    salario_minimo numeric NOT NULL,
    auxilio_transporte numeric NOT NULL,
    uvt numeric NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_parametros_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_parametros_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_parametros_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_parametros_id_seq OWNED BY public.nomina_parametros.id;


--
-- Name: nomina_periodos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_periodos (
    id integer NOT NULL,
    anio integer NOT NULL,
    mes integer NOT NULL,
    numero_periodo integer NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    estado character varying DEFAULT 'Abierto'::character varying,
    observaciones text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_periodos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_periodos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_periodos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_periodos_id_seq OWNED BY public.nomina_periodos.id;


--
-- Name: nomina_prestaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_prestaciones (
    id integer NOT NULL,
    anio integer NOT NULL,
    cesantias numeric NOT NULL,
    intereses_cesantias numeric NOT NULL,
    prima numeric NOT NULL,
    vacaciones numeric NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: nomina_retencion_tabla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_retencion_tabla (
    id integer NOT NULL,
    anio integer NOT NULL,
    rango_desde numeric NOT NULL,
    rango_hasta numeric NOT NULL,
    tarifa_marginal numeric NOT NULL,
    uvt_mas numeric NOT NULL,
    uvt_base numeric NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: nomina_seguridad_social; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_seguridad_social (
    id integer NOT NULL,
    anio integer NOT NULL,
    salud_empleado numeric NOT NULL,
    salud_empleador numeric NOT NULL,
    pension_empleado numeric NOT NULL,
    pension_empleador numeric NOT NULL,
    solidaridad_base numeric,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_seguridad_social_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_seguridad_social_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_seguridad_social_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_seguridad_social_id_seq OWNED BY public.nomina_seguridad_social.id;


--
-- Name: notas_credito_pos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notas_credito_pos (
    id integer NOT NULL,
    numero_nota character varying(30) NOT NULL,
    venta_id integer NOT NULL,
    motivo text NOT NULL,
    total numeric NOT NULL,
    usuario_id integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: notas_credito_pos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notas_credito_pos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notas_credito_pos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notas_credito_pos_id_seq OWNED BY public.notas_credito_pos.id;


--
-- Name: pedidos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pedidos (
    id integer NOT NULL,
    referencia_pedido character varying(100) NOT NULL,
    cliente_nombre character varying(150),
    cliente_email character varying(150),
    cliente_tipo_documento character varying(10),
    cliente_documento character varying(50),
    cliente_telefono character varying(50),
    direccion_envio text,
    ciudad character varying(100),
    estado_pago character varying(20) DEFAULT 'PENDIENTE'::character varying,
    estado_envio character varying(20) DEFAULT 'POR_DESPACHAR'::character varying,
    monto_total numeric(15,2),
    id_transaccion_payu character varying(100),
    metodo_pago character varying(50),
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    factura_dian_id uuid,
    CONSTRAINT check_estado_envio CHECK (((estado_envio)::text = ANY (ARRAY[('ESPERA_PAGO'::character varying)::text, ('POR_DESPACHAR'::character varying)::text, ('ENVIADO'::character varying)::text, ('ENTREGADO'::character varying)::text, ('CANCELADO'::character varying)::text]))),
    CONSTRAINT check_estado_pago CHECK (((estado_pago)::text = ANY (ARRAY[('PENDIENTE'::character varying)::text, ('APROBADO'::character varying)::text, ('RECHAZADO'::character varying)::text, ('EXPIRADO'::character varying)::text]))),
    CONSTRAINT check_tipo_documento CHECK (((cliente_tipo_documento)::text = ANY (ARRAY[('CC'::character varying)::text, ('CE'::character varying)::text, ('NIT'::character varying)::text, ('TI'::character varying)::text, ('PP'::character varying)::text, ('IDC'::character varying)::text])))
);


--
-- Name: pedidos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pedidos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pedidos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pedidos_id_seq OWNED BY public.pedidos.id;


--
-- Name: pos_desktop_inventory_movements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pos_desktop_inventory_movements (
    id bigint NOT NULL,
    client_movement_id character varying(100) NOT NULL,
    product_id integer,
    sku_snapshot character varying(100),
    quantity_delta integer NOT NULL,
    reason character varying(200),
    created_at_local timestamp without time zone,
    received_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: pos_desktop_inventory_movements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pos_desktop_inventory_movements_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pos_desktop_inventory_movements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pos_desktop_inventory_movements_id_seq OWNED BY public.pos_desktop_inventory_movements.id;


--
-- Name: pos_desktop_sale_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pos_desktop_sale_items (
    id bigint NOT NULL,
    sale_id bigint NOT NULL,
    product_id integer,
    sku_snapshot character varying(100),
    name_snapshot character varying(200),
    quantity integer NOT NULL,
    unit_price numeric(12,2) NOT NULL,
    line_total numeric(12,2) NOT NULL
);


--
-- Name: pos_desktop_sale_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pos_desktop_sale_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pos_desktop_sale_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pos_desktop_sale_items_id_seq OWNED BY public.pos_desktop_sale_items.id;


--
-- Name: pos_desktop_sales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pos_desktop_sales (
    id bigint NOT NULL,
    receipt_number character varying(50) NOT NULL,
    total numeric(12,2) DEFAULT 0 NOT NULL,
    created_at_local timestamp without time zone,
    received_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: pos_desktop_sales_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pos_desktop_sales_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pos_desktop_sales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pos_desktop_sales_id_seq OWNED BY public.pos_desktop_sales.id;


--
-- Name: producto_comentarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.producto_comentarios (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    usuario_id integer,
    autor_nombre character varying(100) NOT NULL,
    calificacion smallint NOT NULL,
    comentario text NOT NULL,
    aprobado boolean DEFAULT false,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT producto_comentarios_calificacion_check CHECK (((calificacion >= 1) AND (calificacion <= 5)))
);


--
-- Name: producto_comentarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.producto_comentarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: producto_comentarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.producto_comentarios_id_seq OWNED BY public.producto_comentarios.id;


--
-- Name: producto_imagenes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.producto_imagenes (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    imagen_url character varying(500) NOT NULL,
    orden integer DEFAULT 0,
    es_principal boolean DEFAULT false
);


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.producto_imagenes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.producto_imagenes_id_seq OWNED BY public.producto_imagenes.id;


--
-- Name: productos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.productos (
    id integer NOT NULL,
    imagen character varying(255) NOT NULL,
    nombre character varying(100) NOT NULL,
    precio numeric(10,2) NOT NULL,
    referencia character varying(50) NOT NULL,
    genero_id integer NOT NULL,
    descripcion text,
    stock integer DEFAULT 0,
    tenant_id integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    active boolean DEFAULT true NOT NULL,
    barcode character varying(100)
);


--
-- Name: productos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: productos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.productos_id_seq OWNED BY public.productos.id;


--
-- Name: public_site_blocks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_site_blocks (
    id integer NOT NULL,
    slug character varying NOT NULL,
    block_type character varying DEFAULT 'landing'::character varying NOT NULL,
    title text,
    subtitle text,
    body text,
    extra_body text,
    sort_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: public_site_blocks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.public_site_blocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: public_site_blocks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.public_site_blocks_id_seq OWNED BY public.public_site_blocks.id;


--
-- Name: public_site_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_site_items (
    id integer NOT NULL,
    item_type character varying NOT NULL,
    title text,
    subtitle text,
    description text,
    image_url text,
    cta_label text,
    cta_url text,
    extra_text text,
    sort_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: public_site_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.public_site_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: public_site_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.public_site_items_id_seq OWNED BY public.public_site_items.id;


--
-- Name: public_site_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_site_settings (
    key character varying NOT NULL,
    value text,
    value_type character varying DEFAULT 'text'::character varying NOT NULL,
    group_name character varying DEFAULT 'general'::character varying NOT NULL,
    description text,
    sort_order integer DEFAULT 0 NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: publicaciones_home; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publicaciones_home (
    id integer NOT NULL,
    titulo character varying(200) NOT NULL,
    descripcion text NOT NULL,
    imagen character varying(500),
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: publicaciones_home_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.publicaciones_home_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: publicaciones_home_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.publicaciones_home_id_seq OWNED BY public.publicaciones_home.id;


--
-- Name: restaurant_table_consumptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_table_consumptions (
    id integer NOT NULL,
    tenant_id integer NOT NULL,
    order_id integer NOT NULL,
    table_id integer NOT NULL,
    producto_id integer,
    descripcion character varying(220) NOT NULL,
    cantidad integer DEFAULT 1 NOT NULL,
    precio_unitario numeric(12,2) DEFAULT 0 NOT NULL,
    subtotal numeric(12,2) DEFAULT 0 NOT NULL,
    estado character varying(20) DEFAULT 'pendiente'::character varying NOT NULL,
    notas text,
    creado_por integer,
    ordered_at timestamp without time zone DEFAULT now() NOT NULL,
    served_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_restaurant_table_consumptions_estado CHECK (((estado)::text = ANY ((ARRAY['pendiente'::character varying, 'preparando'::character varying, 'servido'::character varying])::text[])))
);


--
-- Name: restaurant_table_consumptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.restaurant_table_consumptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: restaurant_table_consumptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.restaurant_table_consumptions_id_seq OWNED BY public.restaurant_table_consumptions.id;


--
-- Name: restaurant_table_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_table_orders (
    id integer NOT NULL,
    tenant_id integer NOT NULL,
    table_id integer NOT NULL,
    estado character varying(20) DEFAULT 'abierta'::character varying NOT NULL,
    cliente_nombre character varying(150),
    comensales integer DEFAULT 1 NOT NULL,
    notas text,
    abierta_por integer,
    cerrada_por integer,
    total_acumulado numeric(12,2) DEFAULT 0 NOT NULL,
    pos_sale_id integer,
    opened_at timestamp without time zone DEFAULT now() NOT NULL,
    last_activity_at timestamp without time zone DEFAULT now() NOT NULL,
    closed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    payment_method character varying(30) DEFAULT 'EFECTIVO'::character varying NOT NULL,
    accounting_status character varying(30) DEFAULT 'pendiente'::character varying NOT NULL,
    accounting_income_movement_id integer,
    accounting_reversal_movement_id integer,
    accounting_synced_at timestamp without time zone,
    cancel_reason text,
    cancelled_at timestamp without time zone,
    cancelled_by integer,
    CONSTRAINT chk_restaurant_table_orders_estado CHECK (((estado)::text = ANY ((ARRAY['abierta'::character varying, 'cerrada'::character varying, 'cancelada'::character varying])::text[])))
);


--
-- Name: restaurant_table_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.restaurant_table_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: restaurant_table_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.restaurant_table_orders_id_seq OWNED BY public.restaurant_table_orders.id;


--
-- Name: restaurant_tables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_tables (
    id integer NOT NULL,
    tenant_id integer NOT NULL,
    codigo character varying(30) NOT NULL,
    nombre character varying(120) NOT NULL,
    area character varying(100) DEFAULT 'Salon principal'::character varying NOT NULL,
    capacidad integer DEFAULT 4 NOT NULL,
    forma character varying(20) DEFAULT 'square'::character varying NOT NULL,
    estado character varying(30) DEFAULT 'disponible'::character varying NOT NULL,
    pos_x numeric(5,2) DEFAULT 8 NOT NULL,
    pos_y numeric(5,2) DEFAULT 10 NOT NULL,
    ancho numeric(5,2) DEFAULT 16 NOT NULL,
    alto numeric(5,2) DEFAULT 16 NOT NULL,
    rotacion smallint DEFAULT 0 NOT NULL,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL,
    creado_por integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_restaurant_tables_estado CHECK (((estado)::text = ANY ((ARRAY['disponible'::character varying, 'ocupada'::character varying, 'reservada'::character varying, 'cuenta_solicitada'::character varying])::text[]))),
    CONSTRAINT chk_restaurant_tables_forma CHECK (((forma)::text = ANY ((ARRAY['round'::character varying, 'square'::character varying, 'rectangle'::character varying])::text[])))
);


--
-- Name: restaurant_tables_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.restaurant_tables_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: restaurant_tables_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.restaurant_tables_id_seq OWNED BY public.restaurant_tables.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: saas_modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saas_modules (
    id integer NOT NULL,
    code character varying(80) NOT NULL,
    nombre character varying(140) NOT NULL,
    descripcion text,
    categoria character varying(60) DEFAULT 'general'::character varying NOT NULL,
    is_core boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: saas_modules_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.saas_modules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: saas_modules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.saas_modules_id_seq OWNED BY public.saas_modules.id;


--
-- Name: saas_tenant_modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saas_tenant_modules (
    tenant_id integer NOT NULL,
    module_id integer NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    settings jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: saas_tenants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saas_tenants (
    id integer NOT NULL,
    slug character varying(80) NOT NULL,
    nombre character varying(180) NOT NULL,
    estado character varying(30) DEFAULT 'activo'::character varying NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: saas_tenants_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.saas_tenants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: saas_tenants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.saas_tenants_id_seq OWNED BY public.saas_tenants.id;


--
-- Name: sala_video_participantes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sala_video_participantes (
    id integer NOT NULL,
    sala_id integer NOT NULL,
    usuario_id integer,
    email character varying(200),
    nombre character varying(200),
    token_acceso character varying(128) NOT NULL,
    rol_sala character varying(20) DEFAULT 'participante'::character varying,
    invitado boolean DEFAULT false,
    email_enviado boolean DEFAULT false,
    se_unio boolean DEFAULT false,
    fecha_union timestamp without time zone,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sala_video_participantes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sala_video_participantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sala_video_participantes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sala_video_participantes_id_seq OWNED BY public.sala_video_participantes.id;


--
-- Name: salas_video; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.salas_video (
    id integer NOT NULL,
    codigo_sala character varying(64) NOT NULL,
    nombre character varying(200) NOT NULL,
    descripcion text,
    creado_por integer,
    estado character varying(20) DEFAULT 'programada'::character varying NOT NULL,
    fecha_inicio timestamp without time zone,
    fecha_fin timestamp without time zone,
    duracion_real integer,
    max_participantes integer DEFAULT 10,
    password_sala character varying(100),
    ticket_id integer,
    contacto_crm_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: salas_video_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.salas_video_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: salas_video_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.salas_video_id_seq OWNED BY public.salas_video.id;


--
-- Name: servicios_home; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.servicios_home (
    id integer NOT NULL,
    titulo character varying(200) NOT NULL,
    descripcion text NOT NULL,
    beneficios text,
    imagen character varying(500),
    activo boolean DEFAULT true,
    orden integer DEFAULT 0,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: servicios_home_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.servicios_home_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: servicios_home_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.servicios_home_id_seq OWNED BY public.servicios_home.id;


--
-- Name: share_accesos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.share_accesos (
    id integer NOT NULL,
    carpeta_raiz_id integer,
    archivo_id integer,
    accion character varying(20),
    ip character varying(45),
    user_agent text,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: share_accesos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.share_accesos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: share_accesos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.share_accesos_id_seq OWNED BY public.share_accesos.id;


--
-- Name: share_archivos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.share_archivos (
    id integer NOT NULL,
    carpeta_id integer NOT NULL,
    nombre_original character varying(255) NOT NULL,
    nombre_almacenado character varying(255) NOT NULL,
    tamano_bytes bigint,
    mime_type character varying(120),
    subido_por_admin integer,
    subido_por_cliente character varying(120),
    fecha_subida timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: share_archivos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.share_archivos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: share_archivos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.share_archivos_id_seq OWNED BY public.share_archivos.id;


--
-- Name: share_carpetas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.share_carpetas (
    id integer NOT NULL,
    parent_id integer,
    nombre character varying(200) NOT NULL,
    descripcion text,
    token character varying(64),
    clave_hash character varying(255),
    permitir_subida boolean DEFAULT false,
    fecha_vence timestamp without time zone,
    creado_por integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: share_carpetas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.share_carpetas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: share_carpetas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.share_carpetas_id_seq OWNED BY public.share_carpetas.id;


--
-- Name: slides_home; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.slides_home (
    id integer NOT NULL,
    imagen character varying(500) NOT NULL,
    titulo character varying(200),
    descripcion text,
    orden integer DEFAULT 0,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: slides_home_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.slides_home_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: slides_home_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.slides_home_id_seq OWNED BY public.slides_home.id;


--
-- Name: software_planes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.software_planes (
    id integer NOT NULL,
    plan_key character varying(60) NOT NULL,
    nombre character varying(120) NOT NULL,
    precio numeric(12,2) DEFAULT 0 NOT NULL,
    periodo character varying(20) DEFAULT 'mes'::character varying NOT NULL,
    ideal text,
    incluye text,
    destacado boolean DEFAULT false NOT NULL,
    comprable boolean DEFAULT true NOT NULL,
    tiene_app boolean DEFAULT false NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: software_planes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.software_planes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: software_planes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.software_planes_id_seq OWNED BY public.software_planes.id;


--
-- Name: sync_applied_ops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sync_applied_ops (
    client_op_uuid text NOT NULL,
    remote_id integer,
    applied_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: sync_outbox_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sync_outbox_log (
    id bigint NOT NULL,
    received_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    entity character varying(50) NOT NULL,
    action character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    remote_id bigint,
    error text,
    payload_sample text
);


--
-- Name: sync_outbox_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sync_outbox_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sync_outbox_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sync_outbox_log_id_seq OWNED BY public.sync_outbox_log.id;


--
-- Name: sync_restaurant_applied_ops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sync_restaurant_applied_ops (
    client_op_uuid text NOT NULL,
    remote_id integer,
    applied_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ticket_respuestas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ticket_respuestas (
    id integer NOT NULL,
    ticket_id integer NOT NULL,
    usuario_id integer NOT NULL,
    mensaje text NOT NULL,
    es_admin boolean DEFAULT false,
    fecha timestamp with time zone DEFAULT now()
);


--
-- Name: ticket_respuestas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ticket_respuestas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ticket_respuestas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ticket_respuestas_id_seq OWNED BY public.ticket_respuestas.id;


--
-- Name: tickets_soporte; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tickets_soporte (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    asunto text NOT NULL,
    mensaje text NOT NULL,
    estado text DEFAULT 'abierto'::text NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now(),
    fecha_actualizado timestamp with time zone DEFAULT now()
);


--
-- Name: tickets_soporte_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tickets_soporte_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tickets_soporte_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tickets_soporte_id_seq OWNED BY public.tickets_soporte.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    "contraseña" character varying(255) NOT NULL,
    rol_id integer NOT NULL,
    fecha_nacimiento date,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    telefono character varying(15),
    direccion character varying(255),
    fotografia character varying(255),
    estado character varying(20) DEFAULT 'habilitado'::character varying,
    ultima_conexion timestamp without time zone,
    fecha_modificacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    google_sub character varying(255),
    tenant_id integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: ventas_pos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ventas_pos (
    id integer NOT NULL,
    numero_venta character varying(50) NOT NULL,
    cliente_nombre character varying(200),
    cliente_documento character varying(50),
    cliente_telefono character varying(50),
    metodo_pago character varying(50),
    subtotal numeric,
    descuento numeric DEFAULT 0,
    total numeric,
    notas text,
    usuario_id integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    factura_dian_id uuid,
    estado character varying(20) DEFAULT 'activa'::character varying,
    nota_credito_id integer
);


--
-- Name: ventas_pos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ventas_pos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ventas_pos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ventas_pos_id_seq OWNED BY public.ventas_pos.id;


--
-- Name: backups_db id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backups_db ALTER COLUMN id SET DEFAULT nextval('public.backups_db_id_seq'::regclass);


--
-- Name: contabilidad_cierres id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_cierres ALTER COLUMN id SET DEFAULT nextval('public.contabilidad_cierres_id_seq'::regclass);


--
-- Name: contabilidad_movimientos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_movimientos ALTER COLUMN id SET DEFAULT nextval('public.contabilidad_movimientos_id_seq'::regclass);


--
-- Name: contabilidad_plantillas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_plantillas ALTER COLUMN id SET DEFAULT nextval('public.contabilidad_plantillas_id_seq'::regclass);


--
-- Name: cotizaciones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotizaciones ALTER COLUMN id SET DEFAULT nextval('public.cotizaciones_id_seq'::regclass);


--
-- Name: crm_actividades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades ALTER COLUMN id SET DEFAULT nextval('public.crm_actividades_id_seq'::regclass);


--
-- Name: crm_contactos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_contactos ALTER COLUMN id SET DEFAULT nextval('public.crm_contactos_id_seq'::regclass);


--
-- Name: crm_oportunidades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_oportunidades ALTER COLUMN id SET DEFAULT nextval('public.crm_oportunidades_id_seq'::regclass);


--
-- Name: crm_tareas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas ALTER COLUMN id SET DEFAULT nextval('public.crm_tareas_id_seq'::regclass);


--
-- Name: cuentas_cobro id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuentas_cobro ALTER COLUMN id SET DEFAULT nextval('public.cuentas_cobro_id_seq'::regclass);


--
-- Name: detalle_cotizacion id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cotizacion ALTER COLUMN id SET DEFAULT nextval('public.detalle_cotizacion_id_seq'::regclass);


--
-- Name: detalle_cuenta_cobro id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cuenta_cobro ALTER COLUMN id SET DEFAULT nextval('public.detalle_cuenta_cobro_id_seq'::regclass);


--
-- Name: detalle_pedidos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_pedidos ALTER COLUMN id SET DEFAULT nextval('public.detalle_pedidos_id_seq'::regclass);


--
-- Name: detalle_venta_pos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_venta_pos ALTER COLUMN id SET DEFAULT nextval('public.detalle_venta_pos_id_seq'::regclass);


--
-- Name: generos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generos ALTER COLUMN id SET DEFAULT nextval('public.generos_id_seq'::regclass);


--
-- Name: google_calendar_watches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_calendar_watches ALTER COLUMN id SET DEFAULT nextval('public.google_calendar_watches_id_seq'::regclass);


--
-- Name: google_oauth_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_oauth_tokens ALTER COLUMN id SET DEFAULT nextval('public.google_oauth_tokens_id_seq'::regclass);


--
-- Name: inventario_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventario_log ALTER COLUMN id SET DEFAULT nextval('public.inventario_log_id_seq'::regclass);


--
-- Name: nomina_arl_niveles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_arl_niveles ALTER COLUMN id SET DEFAULT nextval('public.nomina_arl_niveles_id_seq'::regclass);


--
-- Name: nomina_asientos_contables id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_contables ALTER COLUMN id SET DEFAULT nextval('public.nomina_asientos_contables_id_seq'::regclass);


--
-- Name: nomina_detalle id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_detalle ALTER COLUMN id SET DEFAULT nextval('public.nomina_detalle_id_seq'::regclass);


--
-- Name: nomina_empleados id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_empleados ALTER COLUMN id SET DEFAULT nextval('public.nomina_empleados_id_seq'::regclass);


--
-- Name: nomina_liquidaciones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_liquidaciones ALTER COLUMN id SET DEFAULT nextval('public.nomina_liquidaciones_id_seq'::regclass);


--
-- Name: nomina_novedades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_novedades ALTER COLUMN id SET DEFAULT nextval('public.nomina_novedades_id_seq'::regclass);


--
-- Name: nomina_parametros id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parametros ALTER COLUMN id SET DEFAULT nextval('public.nomina_parametros_id_seq'::regclass);


--
-- Name: nomina_periodos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_periodos ALTER COLUMN id SET DEFAULT nextval('public.nomina_periodos_id_seq'::regclass);


--
-- Name: nomina_seguridad_social id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_seguridad_social ALTER COLUMN id SET DEFAULT nextval('public.nomina_seguridad_social_id_seq'::regclass);


--
-- Name: notas_credito_pos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_credito_pos ALTER COLUMN id SET DEFAULT nextval('public.notas_credito_pos_id_seq'::regclass);


--
-- Name: pedidos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos ALTER COLUMN id SET DEFAULT nextval('public.pedidos_id_seq'::regclass);


--
-- Name: pos_desktop_inventory_movements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_inventory_movements ALTER COLUMN id SET DEFAULT nextval('public.pos_desktop_inventory_movements_id_seq'::regclass);


--
-- Name: pos_desktop_sale_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sale_items ALTER COLUMN id SET DEFAULT nextval('public.pos_desktop_sale_items_id_seq'::regclass);


--
-- Name: pos_desktop_sales id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sales ALTER COLUMN id SET DEFAULT nextval('public.pos_desktop_sales_id_seq'::regclass);


--
-- Name: producto_comentarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_comentarios ALTER COLUMN id SET DEFAULT nextval('public.producto_comentarios_id_seq'::regclass);


--
-- Name: producto_imagenes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_imagenes ALTER COLUMN id SET DEFAULT nextval('public.producto_imagenes_id_seq'::regclass);


--
-- Name: productos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos ALTER COLUMN id SET DEFAULT nextval('public.productos_id_seq'::regclass);


--
-- Name: public_site_blocks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_site_blocks ALTER COLUMN id SET DEFAULT nextval('public.public_site_blocks_id_seq'::regclass);


--
-- Name: public_site_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_site_items ALTER COLUMN id SET DEFAULT nextval('public.public_site_items_id_seq'::regclass);


--
-- Name: publicaciones_home id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publicaciones_home ALTER COLUMN id SET DEFAULT nextval('public.publicaciones_home_id_seq'::regclass);


--
-- Name: restaurant_table_consumptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions ALTER COLUMN id SET DEFAULT nextval('public.restaurant_table_consumptions_id_seq'::regclass);


--
-- Name: restaurant_table_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders ALTER COLUMN id SET DEFAULT nextval('public.restaurant_table_orders_id_seq'::regclass);


--
-- Name: restaurant_tables id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_tables ALTER COLUMN id SET DEFAULT nextval('public.restaurant_tables_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: saas_modules id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_modules ALTER COLUMN id SET DEFAULT nextval('public.saas_modules_id_seq'::regclass);


--
-- Name: saas_tenants id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_tenants ALTER COLUMN id SET DEFAULT nextval('public.saas_tenants_id_seq'::regclass);


--
-- Name: sala_video_participantes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sala_video_participantes ALTER COLUMN id SET DEFAULT nextval('public.sala_video_participantes_id_seq'::regclass);


--
-- Name: salas_video id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas_video ALTER COLUMN id SET DEFAULT nextval('public.salas_video_id_seq'::regclass);


--
-- Name: servicios_home id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicios_home ALTER COLUMN id SET DEFAULT nextval('public.servicios_home_id_seq'::regclass);


--
-- Name: share_accesos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_accesos ALTER COLUMN id SET DEFAULT nextval('public.share_accesos_id_seq'::regclass);


--
-- Name: share_archivos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_archivos ALTER COLUMN id SET DEFAULT nextval('public.share_archivos_id_seq'::regclass);


--
-- Name: share_carpetas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_carpetas ALTER COLUMN id SET DEFAULT nextval('public.share_carpetas_id_seq'::regclass);


--
-- Name: slides_home id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slides_home ALTER COLUMN id SET DEFAULT nextval('public.slides_home_id_seq'::regclass);


--
-- Name: software_planes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.software_planes ALTER COLUMN id SET DEFAULT nextval('public.software_planes_id_seq'::regclass);


--
-- Name: sync_outbox_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_outbox_log ALTER COLUMN id SET DEFAULT nextval('public.sync_outbox_log_id_seq'::regclass);


--
-- Name: ticket_respuestas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ticket_respuestas ALTER COLUMN id SET DEFAULT nextval('public.ticket_respuestas_id_seq'::regclass);


--
-- Name: tickets_soporte id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets_soporte ALTER COLUMN id SET DEFAULT nextval('public.tickets_soporte_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: ventas_pos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ventas_pos ALTER COLUMN id SET DEFAULT nextval('public.ventas_pos_id_seq'::regclass);


--
-- Name: backup_config backup_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_config
    ADD CONSTRAINT backup_config_pkey PRIMARY KEY (id);


--
-- Name: backups_db backups_db_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backups_db
    ADD CONSTRAINT backups_db_pkey PRIMARY KEY (id);


--
-- Name: config_secciones config_secciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_secciones
    ADD CONSTRAINT config_secciones_pkey PRIMARY KEY (clave);


--
-- Name: contabilidad_cierres contabilidad_cierres_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_cierres
    ADD CONSTRAINT contabilidad_cierres_pkey PRIMARY KEY (id);


--
-- Name: contabilidad_movimientos contabilidad_movimientos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_movimientos
    ADD CONSTRAINT contabilidad_movimientos_pkey PRIMARY KEY (id);


--
-- Name: contabilidad_plantillas contabilidad_plantillas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_plantillas
    ADD CONSTRAINT contabilidad_plantillas_pkey PRIMARY KEY (id);


--
-- Name: cotizaciones cotizaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotizaciones
    ADD CONSTRAINT cotizaciones_pkey PRIMARY KEY (id);


--
-- Name: crm_actividades crm_actividades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades
    ADD CONSTRAINT crm_actividades_pkey PRIMARY KEY (id);


--
-- Name: crm_contactos crm_contactos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_contactos
    ADD CONSTRAINT crm_contactos_pkey PRIMARY KEY (id);


--
-- Name: crm_oportunidades crm_oportunidades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_oportunidades
    ADD CONSTRAINT crm_oportunidades_pkey PRIMARY KEY (id);


--
-- Name: crm_tareas crm_tareas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT crm_tareas_pkey PRIMARY KEY (id);


--
-- Name: cuentas_cobro cuentas_cobro_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuentas_cobro
    ADD CONSTRAINT cuentas_cobro_pkey PRIMARY KEY (id);


--
-- Name: detalle_cotizacion detalle_cotizacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cotizacion
    ADD CONSTRAINT detalle_cotizacion_pkey PRIMARY KEY (id);


--
-- Name: detalle_cuenta_cobro detalle_cuenta_cobro_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cuenta_cobro
    ADD CONSTRAINT detalle_cuenta_cobro_pkey PRIMARY KEY (id);


--
-- Name: detalle_pedidos detalle_pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_pedidos
    ADD CONSTRAINT detalle_pedidos_pkey PRIMARY KEY (id);


--
-- Name: detalle_venta_pos detalle_venta_pos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_venta_pos
    ADD CONSTRAINT detalle_venta_pos_pkey PRIMARY KEY (id);


--
-- Name: generos generos_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generos
    ADD CONSTRAINT generos_nombre_key UNIQUE (nombre);


--
-- Name: generos generos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generos
    ADD CONSTRAINT generos_pkey PRIMARY KEY (id);


--
-- Name: google_calendar_watches google_calendar_watches_channel_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_calendar_watches
    ADD CONSTRAINT google_calendar_watches_channel_id_key UNIQUE (channel_id);


--
-- Name: google_calendar_watches google_calendar_watches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_calendar_watches
    ADD CONSTRAINT google_calendar_watches_pkey PRIMARY KEY (id);


--
-- Name: google_oauth_tokens google_oauth_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_oauth_tokens
    ADD CONSTRAINT google_oauth_tokens_pkey PRIMARY KEY (id);


--
-- Name: google_oauth_tokens google_oauth_tokens_usuario_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_oauth_tokens
    ADD CONSTRAINT google_oauth_tokens_usuario_id_key UNIQUE (usuario_id);


--
-- Name: inventario_log inventario_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventario_log
    ADD CONSTRAINT inventario_log_pkey PRIMARY KEY (id);


--
-- Name: nomina_arl_niveles nomina_arl_niveles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_arl_niveles
    ADD CONSTRAINT nomina_arl_niveles_pkey PRIMARY KEY (id);


--
-- Name: nomina_asientos_contables nomina_asientos_contables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_contables
    ADD CONSTRAINT nomina_asientos_contables_pkey PRIMARY KEY (id);


--
-- Name: nomina_asientos_detalle nomina_asientos_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_detalle
    ADD CONSTRAINT nomina_asientos_detalle_pkey PRIMARY KEY (id);


--
-- Name: nomina_contratistas_pila nomina_contratistas_pila_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_contratistas_pila
    ADD CONSTRAINT nomina_contratistas_pila_pkey PRIMARY KEY (id);


--
-- Name: nomina_detalle nomina_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_detalle
    ADD CONSTRAINT nomina_detalle_pkey PRIMARY KEY (id);


--
-- Name: nomina_empleados nomina_empleados_numero_documento_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_empleados
    ADD CONSTRAINT nomina_empleados_numero_documento_key UNIQUE (numero_documento);


--
-- Name: nomina_empleados nomina_empleados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_empleados
    ADD CONSTRAINT nomina_empleados_pkey PRIMARY KEY (id);


--
-- Name: nomina_liquidaciones nomina_liquidaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_liquidaciones
    ADD CONSTRAINT nomina_liquidaciones_pkey PRIMARY KEY (id);


--
-- Name: nomina_novedades nomina_novedades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_novedades
    ADD CONSTRAINT nomina_novedades_pkey PRIMARY KEY (id);


--
-- Name: nomina_parafiscales nomina_parafiscales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parafiscales
    ADD CONSTRAINT nomina_parafiscales_pkey PRIMARY KEY (id);


--
-- Name: nomina_parametros nomina_parametros_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parametros
    ADD CONSTRAINT nomina_parametros_pkey PRIMARY KEY (id);


--
-- Name: nomina_periodos nomina_periodos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_periodos
    ADD CONSTRAINT nomina_periodos_pkey PRIMARY KEY (id);


--
-- Name: nomina_prestaciones nomina_prestaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_prestaciones
    ADD CONSTRAINT nomina_prestaciones_pkey PRIMARY KEY (id);


--
-- Name: nomina_retencion_tabla nomina_retencion_tabla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_retencion_tabla
    ADD CONSTRAINT nomina_retencion_tabla_pkey PRIMARY KEY (id);


--
-- Name: nomina_seguridad_social nomina_seguridad_social_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_seguridad_social
    ADD CONSTRAINT nomina_seguridad_social_pkey PRIMARY KEY (id);


--
-- Name: notas_credito_pos notas_credito_pos_numero_nota_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_credito_pos
    ADD CONSTRAINT notas_credito_pos_numero_nota_key UNIQUE (numero_nota);


--
-- Name: notas_credito_pos notas_credito_pos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_credito_pos
    ADD CONSTRAINT notas_credito_pos_pkey PRIMARY KEY (id);


--
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id);


--
-- Name: pedidos pedidos_referencia_pedido_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_referencia_pedido_key UNIQUE (referencia_pedido);


--
-- Name: pos_desktop_inventory_movements pos_desktop_inventory_movements_client_movement_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_inventory_movements
    ADD CONSTRAINT pos_desktop_inventory_movements_client_movement_id_key UNIQUE (client_movement_id);


--
-- Name: pos_desktop_inventory_movements pos_desktop_inventory_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_inventory_movements
    ADD CONSTRAINT pos_desktop_inventory_movements_pkey PRIMARY KEY (id);


--
-- Name: pos_desktop_sale_items pos_desktop_sale_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sale_items
    ADD CONSTRAINT pos_desktop_sale_items_pkey PRIMARY KEY (id);


--
-- Name: pos_desktop_sales pos_desktop_sales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sales
    ADD CONSTRAINT pos_desktop_sales_pkey PRIMARY KEY (id);


--
-- Name: pos_desktop_sales pos_desktop_sales_receipt_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sales
    ADD CONSTRAINT pos_desktop_sales_receipt_number_key UNIQUE (receipt_number);


--
-- Name: producto_comentarios producto_comentarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_comentarios
    ADD CONSTRAINT producto_comentarios_pkey PRIMARY KEY (id);


--
-- Name: producto_imagenes producto_imagenes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_pkey PRIMARY KEY (id);


--
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id);


--
-- Name: productos productos_referencia_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_referencia_key UNIQUE (referencia);


--
-- Name: public_site_blocks public_site_blocks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_site_blocks
    ADD CONSTRAINT public_site_blocks_pkey PRIMARY KEY (id);


--
-- Name: public_site_blocks public_site_blocks_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_site_blocks
    ADD CONSTRAINT public_site_blocks_slug_key UNIQUE (slug);


--
-- Name: public_site_items public_site_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_site_items
    ADD CONSTRAINT public_site_items_pkey PRIMARY KEY (id);


--
-- Name: public_site_settings public_site_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_site_settings
    ADD CONSTRAINT public_site_settings_pkey PRIMARY KEY (key);


--
-- Name: publicaciones_home publicaciones_home_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publicaciones_home
    ADD CONSTRAINT publicaciones_home_pkey PRIMARY KEY (id);


--
-- Name: restaurant_table_consumptions restaurant_table_consumptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions
    ADD CONSTRAINT restaurant_table_consumptions_pkey PRIMARY KEY (id);


--
-- Name: restaurant_table_orders restaurant_table_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders
    ADD CONSTRAINT restaurant_table_orders_pkey PRIMARY KEY (id);


--
-- Name: restaurant_tables restaurant_tables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_tables
    ADD CONSTRAINT restaurant_tables_pkey PRIMARY KEY (id);


--
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: saas_modules saas_modules_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_modules
    ADD CONSTRAINT saas_modules_code_key UNIQUE (code);


--
-- Name: saas_modules saas_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_modules
    ADD CONSTRAINT saas_modules_pkey PRIMARY KEY (id);


--
-- Name: saas_tenant_modules saas_tenant_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_tenant_modules
    ADD CONSTRAINT saas_tenant_modules_pkey PRIMARY KEY (tenant_id, module_id);


--
-- Name: saas_tenants saas_tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_tenants
    ADD CONSTRAINT saas_tenants_pkey PRIMARY KEY (id);


--
-- Name: saas_tenants saas_tenants_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_tenants
    ADD CONSTRAINT saas_tenants_slug_key UNIQUE (slug);


--
-- Name: sala_video_participantes sala_video_participantes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sala_video_participantes
    ADD CONSTRAINT sala_video_participantes_pkey PRIMARY KEY (id);


--
-- Name: sala_video_participantes sala_video_participantes_token_acceso_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sala_video_participantes
    ADD CONSTRAINT sala_video_participantes_token_acceso_key UNIQUE (token_acceso);


--
-- Name: salas_video salas_video_codigo_sala_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas_video
    ADD CONSTRAINT salas_video_codigo_sala_key UNIQUE (codigo_sala);


--
-- Name: salas_video salas_video_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas_video
    ADD CONSTRAINT salas_video_pkey PRIMARY KEY (id);


--
-- Name: servicios_home servicios_home_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicios_home
    ADD CONSTRAINT servicios_home_pkey PRIMARY KEY (id);


--
-- Name: share_accesos share_accesos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_accesos
    ADD CONSTRAINT share_accesos_pkey PRIMARY KEY (id);


--
-- Name: share_archivos share_archivos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_archivos
    ADD CONSTRAINT share_archivos_pkey PRIMARY KEY (id);


--
-- Name: share_carpetas share_carpetas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_carpetas
    ADD CONSTRAINT share_carpetas_pkey PRIMARY KEY (id);


--
-- Name: share_carpetas share_carpetas_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_carpetas
    ADD CONSTRAINT share_carpetas_token_key UNIQUE (token);


--
-- Name: slides_home slides_home_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slides_home
    ADD CONSTRAINT slides_home_pkey PRIMARY KEY (id);


--
-- Name: software_planes software_planes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.software_planes
    ADD CONSTRAINT software_planes_pkey PRIMARY KEY (id);


--
-- Name: software_planes software_planes_plan_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.software_planes
    ADD CONSTRAINT software_planes_plan_key_key UNIQUE (plan_key);


--
-- Name: sync_applied_ops sync_applied_ops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_applied_ops
    ADD CONSTRAINT sync_applied_ops_pkey PRIMARY KEY (client_op_uuid);


--
-- Name: sync_outbox_log sync_outbox_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_outbox_log
    ADD CONSTRAINT sync_outbox_log_pkey PRIMARY KEY (id);


--
-- Name: sync_restaurant_applied_ops sync_restaurant_applied_ops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_restaurant_applied_ops
    ADD CONSTRAINT sync_restaurant_applied_ops_pkey PRIMARY KEY (client_op_uuid);


--
-- Name: ticket_respuestas ticket_respuestas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ticket_respuestas
    ADD CONSTRAINT ticket_respuestas_pkey PRIMARY KEY (id);


--
-- Name: tickets_soporte tickets_soporte_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets_soporte
    ADD CONSTRAINT tickets_soporte_pkey PRIMARY KEY (id);


--
-- Name: restaurant_tables uq_restaurant_tables_codigo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_tables
    ADD CONSTRAINT uq_restaurant_tables_codigo UNIQUE (tenant_id, codigo);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: ventas_pos ventas_pos_numero_venta_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ventas_pos
    ADD CONSTRAINT ventas_pos_numero_venta_key UNIQUE (numero_venta);


--
-- Name: ventas_pos ventas_pos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ventas_pos
    ADD CONSTRAINT ventas_pos_pkey PRIMARY KEY (id);


--
-- Name: idx_backups_db_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_backups_db_fecha ON public.backups_db USING btree (fecha_creacion DESC);


--
-- Name: idx_contab_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contab_fecha ON public.contabilidad_movimientos USING btree (fecha);


--
-- Name: idx_contab_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contab_tipo ON public.contabilidad_movimientos USING btree (tipo);


--
-- Name: idx_cotizaciones_crm_contacto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cotizaciones_crm_contacto ON public.cotizaciones USING btree (crm_contacto_id);


--
-- Name: idx_crm_contactos_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crm_contactos_tags ON public.crm_contactos USING gin (tags);


--
-- Name: idx_cuentas_cobro_crm_contacto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cuentas_cobro_crm_contacto ON public.cuentas_cobro USING btree (crm_contacto_id);


--
-- Name: idx_nc_pos_venta_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nc_pos_venta_id ON public.notas_credito_pos USING btree (venta_id);


--
-- Name: idx_oport_asignado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oport_asignado ON public.crm_oportunidades USING btree (asignado_a);


--
-- Name: idx_oport_contacto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oport_contacto ON public.crm_oportunidades USING btree (contacto_id);


--
-- Name: idx_oport_cotizacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oport_cotizacion ON public.crm_oportunidades USING btree (cotizacion_id);


--
-- Name: idx_oport_etapa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oport_etapa ON public.crm_oportunidades USING btree (etapa);


--
-- Name: idx_pc_producto_aprobado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pc_producto_aprobado ON public.producto_comentarios USING btree (producto_id, aprobado);


--
-- Name: idx_plantillas_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plantillas_activo ON public.contabilidad_plantillas USING btree (activo);


--
-- Name: idx_pos_desktop_inv_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pos_desktop_inv_product_id ON public.pos_desktop_inventory_movements USING btree (product_id);


--
-- Name: idx_pos_desktop_sale_items_sale_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pos_desktop_sale_items_sale_id ON public.pos_desktop_sale_items USING btree (sale_id);


--
-- Name: idx_productos_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_productos_active ON public.productos USING btree (active);


--
-- Name: idx_productos_barcode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_productos_barcode ON public.productos USING btree (barcode);


--
-- Name: idx_productos_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_productos_tenant_id ON public.productos USING btree (tenant_id);


--
-- Name: idx_public_site_blocks_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_public_site_blocks_type ON public.public_site_blocks USING btree (block_type, sort_order);


--
-- Name: idx_public_site_items_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_public_site_items_type ON public.public_site_items USING btree (item_type, sort_order, is_active);


--
-- Name: idx_public_site_settings_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_public_site_settings_group ON public.public_site_settings USING btree (group_name, sort_order);


--
-- Name: idx_restaurant_consumptions_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurant_consumptions_order ON public.restaurant_table_consumptions USING btree (order_id, estado, ordered_at);


--
-- Name: idx_restaurant_consumptions_tenant_table; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurant_consumptions_tenant_table ON public.restaurant_table_consumptions USING btree (tenant_id, table_id, estado);


--
-- Name: idx_restaurant_orders_tenant_table; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurant_orders_tenant_table ON public.restaurant_table_orders USING btree (tenant_id, table_id, estado);


--
-- Name: idx_restaurant_tables_tenant_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restaurant_tables_tenant_area ON public.restaurant_tables USING btree (tenant_id, area, nombre);


--
-- Name: idx_sala_part_sala; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sala_part_sala ON public.sala_video_participantes USING btree (sala_id);


--
-- Name: idx_sala_part_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sala_part_token ON public.sala_video_participantes USING btree (token_acceso);


--
-- Name: idx_salas_video_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salas_video_codigo ON public.salas_video USING btree (codigo_sala);


--
-- Name: idx_salas_video_creado_por; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salas_video_creado_por ON public.salas_video USING btree (creado_por);


--
-- Name: idx_salas_video_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salas_video_estado ON public.salas_video USING btree (estado);


--
-- Name: idx_share_accesos_raiz; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_share_accesos_raiz ON public.share_accesos USING btree (carpeta_raiz_id);


--
-- Name: idx_share_archivos_carpeta; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_share_archivos_carpeta ON public.share_archivos USING btree (carpeta_id);


--
-- Name: idx_share_carpetas_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_share_carpetas_parent ON public.share_carpetas USING btree (parent_id);


--
-- Name: idx_share_carpetas_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_share_carpetas_token ON public.share_carpetas USING btree (token);


--
-- Name: idx_sync_outbox_log_received; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sync_outbox_log_received ON public.sync_outbox_log USING btree (received_at DESC);


--
-- Name: idx_usuarios_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuarios_tenant_id ON public.usuarios USING btree (tenant_id);


--
-- Name: uq_restaurant_open_order; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_restaurant_open_order ON public.restaurant_table_orders USING btree (tenant_id, table_id) WHERE ((estado)::text = 'abierta'::text);


--
-- Name: usuarios_google_sub_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX usuarios_google_sub_key ON public.usuarios USING btree (google_sub) WHERE (google_sub IS NOT NULL);


--
-- Name: generos generos_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER generos_set_updated_at BEFORE UPDATE ON public.generos FOR EACH ROW EXECUTE FUNCTION public.trg_generos_set_updated_at();


--
-- Name: productos productos_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER productos_set_updated_at BEFORE UPDATE ON public.productos FOR EACH ROW EXECUTE FUNCTION public.trg_productos_set_updated_at();


--
-- Name: usuarios usuarios_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER usuarios_set_updated_at BEFORE UPDATE ON public.usuarios FOR EACH ROW EXECUTE FUNCTION public.trg_usuarios_set_updated_at();


--
-- Name: backup_config backup_config_actualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_config
    ADD CONSTRAINT backup_config_actualizado_por_fkey FOREIGN KEY (actualizado_por) REFERENCES public.usuarios(id);


--
-- Name: backups_db backups_db_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backups_db
    ADD CONSTRAINT backups_db_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);


--
-- Name: contabilidad_cierres contabilidad_cierres_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_cierres
    ADD CONSTRAINT contabilidad_cierres_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: contabilidad_movimientos contabilidad_movimientos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_movimientos
    ADD CONSTRAINT contabilidad_movimientos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: cotizaciones cotizaciones_crm_contacto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotizaciones
    ADD CONSTRAINT cotizaciones_crm_contacto_id_fkey FOREIGN KEY (crm_contacto_id) REFERENCES public.crm_contactos(id) ON DELETE SET NULL;


--
-- Name: crm_actividades crm_actividades_asignado_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades
    ADD CONSTRAINT crm_actividades_asignado_a_fkey FOREIGN KEY (asignado_a) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_oportunidades crm_oportunidades_asignado_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_oportunidades
    ADD CONSTRAINT crm_oportunidades_asignado_a_fkey FOREIGN KEY (asignado_a) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_oportunidades crm_oportunidades_contacto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_oportunidades
    ADD CONSTRAINT crm_oportunidades_contacto_id_fkey FOREIGN KEY (contacto_id) REFERENCES public.crm_contactos(id) ON DELETE CASCADE;


--
-- Name: crm_oportunidades crm_oportunidades_cotizacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_oportunidades
    ADD CONSTRAINT crm_oportunidades_cotizacion_id_fkey FOREIGN KEY (cotizacion_id) REFERENCES public.cotizaciones(id) ON DELETE SET NULL;


--
-- Name: cuentas_cobro cuentas_cobro_crm_contacto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuentas_cobro
    ADD CONSTRAINT cuentas_cobro_crm_contacto_id_fkey FOREIGN KEY (crm_contacto_id) REFERENCES public.crm_contactos(id) ON DELETE SET NULL;


--
-- Name: detalle_cotizacion detalle_cotizacion_cotizacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cotizacion
    ADD CONSTRAINT detalle_cotizacion_cotizacion_id_fkey FOREIGN KEY (cotizacion_id) REFERENCES public.cotizaciones(id);


--
-- Name: detalle_cuenta_cobro detalle_cuenta_cobro_cuenta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cuenta_cobro
    ADD CONSTRAINT detalle_cuenta_cobro_cuenta_id_fkey FOREIGN KEY (cuenta_id) REFERENCES public.cuentas_cobro(id);


--
-- Name: detalle_venta_pos detalle_venta_pos_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_venta_pos
    ADD CONSTRAINT detalle_venta_pos_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: detalle_venta_pos detalle_venta_pos_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_venta_pos
    ADD CONSTRAINT detalle_venta_pos_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas_pos(id);


--
-- Name: crm_actividades fk_crm_actividades_contacto; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades
    ADD CONSTRAINT fk_crm_actividades_contacto FOREIGN KEY (contacto_id) REFERENCES public.crm_contactos(id) ON DELETE CASCADE;


--
-- Name: crm_actividades fk_crm_actividades_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades
    ADD CONSTRAINT fk_crm_actividades_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_contactos fk_crm_contactos_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_contactos
    ADD CONSTRAINT fk_crm_contactos_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_tareas fk_crm_tareas_asignado; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT fk_crm_tareas_asignado FOREIGN KEY (asignado_a) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_tareas fk_crm_tareas_contacto; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT fk_crm_tareas_contacto FOREIGN KEY (contacto_id) REFERENCES public.crm_contactos(id) ON DELETE CASCADE;


--
-- Name: crm_tareas fk_crm_tareas_creado; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT fk_crm_tareas_creado FOREIGN KEY (creado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: detalle_pedidos fk_detalle_pedido; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_pedidos
    ADD CONSTRAINT fk_detalle_pedido FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


--
-- Name: productos fk_productos_generos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT fk_productos_generos FOREIGN KEY (genero_id) REFERENCES public.generos(id);


--
-- Name: usuarios fk_usuarios_roles; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuarios_roles FOREIGN KEY (rol_id) REFERENCES public.roles(id);


--
-- Name: google_calendar_watches google_calendar_watches_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_calendar_watches
    ADD CONSTRAINT google_calendar_watches_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: google_oauth_tokens google_oauth_tokens_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.google_oauth_tokens
    ADD CONSTRAINT google_oauth_tokens_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: inventario_log inventario_log_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventario_log
    ADD CONSTRAINT inventario_log_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: inventario_log inventario_log_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventario_log
    ADD CONSTRAINT inventario_log_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: nomina_asientos_contables nomina_asientos_contables_liquidacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_contables
    ADD CONSTRAINT nomina_asientos_contables_liquidacion_id_fkey FOREIGN KEY (liquidacion_id) REFERENCES public.nomina_liquidaciones(id);


--
-- Name: nomina_asientos_contables nomina_asientos_contables_periodo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_contables
    ADD CONSTRAINT nomina_asientos_contables_periodo_id_fkey FOREIGN KEY (periodo_id) REFERENCES public.nomina_periodos(id);


--
-- Name: nomina_detalle nomina_detalle_empleado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_detalle
    ADD CONSTRAINT nomina_detalle_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.nomina_empleados(id);


--
-- Name: nomina_detalle nomina_detalle_periodo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_detalle
    ADD CONSTRAINT nomina_detalle_periodo_id_fkey FOREIGN KEY (periodo_id) REFERENCES public.nomina_periodos(id);


--
-- Name: nomina_liquidaciones nomina_liquidaciones_empleado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_liquidaciones
    ADD CONSTRAINT nomina_liquidaciones_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.nomina_empleados(id);


--
-- Name: nomina_novedades nomina_novedades_empleado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_novedades
    ADD CONSTRAINT nomina_novedades_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.nomina_empleados(id);


--
-- Name: nomina_novedades nomina_novedades_periodo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_novedades
    ADD CONSTRAINT nomina_novedades_periodo_id_fkey FOREIGN KEY (periodo_id) REFERENCES public.nomina_periodos(id);


--
-- Name: notas_credito_pos notas_credito_pos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_credito_pos
    ADD CONSTRAINT notas_credito_pos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: notas_credito_pos notas_credito_pos_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_credito_pos
    ADD CONSTRAINT notas_credito_pos_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas_pos(id);


--
-- Name: pos_desktop_inventory_movements pos_desktop_inventory_movements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_inventory_movements
    ADD CONSTRAINT pos_desktop_inventory_movements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.productos(id) ON DELETE SET NULL;


--
-- Name: pos_desktop_sale_items pos_desktop_sale_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sale_items
    ADD CONSTRAINT pos_desktop_sale_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.productos(id) ON DELETE SET NULL;


--
-- Name: pos_desktop_sale_items pos_desktop_sale_items_sale_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pos_desktop_sale_items
    ADD CONSTRAINT pos_desktop_sale_items_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES public.pos_desktop_sales(id) ON DELETE CASCADE;


--
-- Name: producto_comentarios producto_comentarios_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_comentarios
    ADD CONSTRAINT producto_comentarios_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- Name: producto_comentarios producto_comentarios_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_comentarios
    ADD CONSTRAINT producto_comentarios_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: producto_imagenes producto_imagenes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- Name: productos productos_genero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_genero_id_fkey FOREIGN KEY (genero_id) REFERENCES public.generos(id);


--
-- Name: productos productos_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.saas_tenants(id);


--
-- Name: restaurant_table_consumptions restaurant_table_consumptions_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions
    ADD CONSTRAINT restaurant_table_consumptions_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);


--
-- Name: restaurant_table_consumptions restaurant_table_consumptions_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions
    ADD CONSTRAINT restaurant_table_consumptions_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.restaurant_table_orders(id) ON DELETE CASCADE;


--
-- Name: restaurant_table_consumptions restaurant_table_consumptions_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions
    ADD CONSTRAINT restaurant_table_consumptions_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE SET NULL;


--
-- Name: restaurant_table_consumptions restaurant_table_consumptions_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions
    ADD CONSTRAINT restaurant_table_consumptions_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.restaurant_tables(id) ON DELETE CASCADE;


--
-- Name: restaurant_table_consumptions restaurant_table_consumptions_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_consumptions
    ADD CONSTRAINT restaurant_table_consumptions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.saas_tenants(id) ON DELETE CASCADE;


--
-- Name: restaurant_table_orders restaurant_table_orders_abierta_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders
    ADD CONSTRAINT restaurant_table_orders_abierta_por_fkey FOREIGN KEY (abierta_por) REFERENCES public.usuarios(id);


--
-- Name: restaurant_table_orders restaurant_table_orders_cancelled_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders
    ADD CONSTRAINT restaurant_table_orders_cancelled_by_fkey FOREIGN KEY (cancelled_by) REFERENCES public.usuarios(id);


--
-- Name: restaurant_table_orders restaurant_table_orders_cerrada_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders
    ADD CONSTRAINT restaurant_table_orders_cerrada_por_fkey FOREIGN KEY (cerrada_por) REFERENCES public.usuarios(id);


--
-- Name: restaurant_table_orders restaurant_table_orders_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders
    ADD CONSTRAINT restaurant_table_orders_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.restaurant_tables(id) ON DELETE CASCADE;


--
-- Name: restaurant_table_orders restaurant_table_orders_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_table_orders
    ADD CONSTRAINT restaurant_table_orders_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.saas_tenants(id) ON DELETE CASCADE;


--
-- Name: restaurant_tables restaurant_tables_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_tables
    ADD CONSTRAINT restaurant_tables_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);


--
-- Name: restaurant_tables restaurant_tables_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_tables
    ADD CONSTRAINT restaurant_tables_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.saas_tenants(id) ON DELETE CASCADE;


--
-- Name: saas_tenant_modules saas_tenant_modules_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_tenant_modules
    ADD CONSTRAINT saas_tenant_modules_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.saas_modules(id) ON DELETE CASCADE;


--
-- Name: saas_tenant_modules saas_tenant_modules_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_tenant_modules
    ADD CONSTRAINT saas_tenant_modules_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.saas_tenants(id) ON DELETE CASCADE;


--
-- Name: sala_video_participantes sala_video_participantes_sala_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sala_video_participantes
    ADD CONSTRAINT sala_video_participantes_sala_id_fkey FOREIGN KEY (sala_id) REFERENCES public.salas_video(id) ON DELETE CASCADE;


--
-- Name: share_accesos share_accesos_archivo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_accesos
    ADD CONSTRAINT share_accesos_archivo_id_fkey FOREIGN KEY (archivo_id) REFERENCES public.share_archivos(id) ON DELETE SET NULL;


--
-- Name: share_accesos share_accesos_carpeta_raiz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_accesos
    ADD CONSTRAINT share_accesos_carpeta_raiz_id_fkey FOREIGN KEY (carpeta_raiz_id) REFERENCES public.share_carpetas(id) ON DELETE CASCADE;


--
-- Name: share_archivos share_archivos_carpeta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_archivos
    ADD CONSTRAINT share_archivos_carpeta_id_fkey FOREIGN KEY (carpeta_id) REFERENCES public.share_carpetas(id) ON DELETE CASCADE;


--
-- Name: share_archivos share_archivos_subido_por_admin_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_archivos
    ADD CONSTRAINT share_archivos_subido_por_admin_fkey FOREIGN KEY (subido_por_admin) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: share_carpetas share_carpetas_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_carpetas
    ADD CONSTRAINT share_carpetas_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: share_carpetas share_carpetas_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.share_carpetas
    ADD CONSTRAINT share_carpetas_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.share_carpetas(id) ON DELETE CASCADE;


--
-- Name: ticket_respuestas ticket_respuestas_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ticket_respuestas
    ADD CONSTRAINT ticket_respuestas_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets_soporte(id) ON DELETE CASCADE;


--
-- Name: ticket_respuestas ticket_respuestas_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ticket_respuestas
    ADD CONSTRAINT ticket_respuestas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: tickets_soporte tickets_soporte_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets_soporte
    ADD CONSTRAINT tickets_soporte_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: usuarios usuarios_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.roles(id);


--
-- Name: usuarios usuarios_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.saas_tenants(id);


--
-- Name: ventas_pos ventas_pos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ventas_pos
    ADD CONSTRAINT ventas_pos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- PostgreSQL database dump complete
--

\unrestrict kFrxy6ODMimYfeyl6fOB1Bdv6jOWjzWCrbfLY65uFHhvbKsKvKvjbmOcY9EGKiS

