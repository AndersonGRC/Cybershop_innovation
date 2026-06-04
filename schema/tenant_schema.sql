--
-- PostgreSQL database dump
--

\restrict Gap02RbxDWSaUsq0n9ZELaKPF71KvAMxndnvWe5Brtc8wRKh11tN9OhcFTOpAlY

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cliente_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente_config (
    clave character varying NOT NULL,
    valor text,
    tipo character varying DEFAULT 'text'::character varying,
    grupo character varying DEFAULT 'general'::character varying,
    descripcion text,
    orden integer DEFAULT 0
);


--
-- Name: config_secciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_secciones (
    clave character varying(100) NOT NULL,
    valor character varying(500) DEFAULT 'true'::character varying NOT NULL,
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
    total_ingresos numeric,
    total_egresos numeric,
    saldo numeric,
    notas text,
    usuario_id integer,
    created_at timestamp without time zone,
    total_retenciones numeric
);


--
-- Name: contabilidad_movimientos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contabilidad_movimientos (
    id integer NOT NULL,
    tipo character varying(10) NOT NULL,
    categoria character varying(60) NOT NULL,
    descripcion text NOT NULL,
    monto numeric NOT NULL,
    fecha date NOT NULL,
    referencia_tipo character varying(30),
    referencia_id integer,
    notas text,
    usuario_id integer,
    auto_generado boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    monto_bruto numeric DEFAULT 0,
    retefuente_pct numeric DEFAULT 0,
    retefuente_monto numeric DEFAULT 0,
    iva_pct numeric DEFAULT 0,
    iva_monto numeric DEFAULT 0,
    reteiva_pct numeric DEFAULT 0,
    reteiva_monto numeric DEFAULT 0,
    reteica_pct numeric DEFAULT 0,
    reteica_monto numeric DEFAULT 0,
    total_retenciones numeric DEFAULT 0
);


--
-- Name: contabilidad_movimientos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contabilidad_movimientos_id_seq
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
    monto_bruto numeric NOT NULL,
    notas text,
    activo boolean,
    created_at timestamp with time zone
);


--
-- Name: cotizaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cotizaciones (
    id integer NOT NULL,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cliente_nombre text NOT NULL,
    cliente_documento text,
    logo_url text,
    total numeric(10,2) DEFAULT 0,
    pdf_path text,
    cliente_direccion text,
    cliente_ciudad text,
    cliente_telefono text,
    cliente_representante text,
    cliente_cargo text,
    cliente_localidad text,
    estado character varying(20)
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
    fecha_actividad timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    usuario_id integer,
    CONSTRAINT crm_actividades_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['llamada'::character varying, 'email'::character varying, 'reunion'::character varying, 'whatsapp'::character varying, 'visita'::character varying, 'nota'::character varying, 'otro'::character varying])::text[])))
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
    email character varying(200),
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
    CONSTRAINT crm_contactos_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['cliente'::character varying, 'proveedor'::character varying, 'lead'::character varying, 'socio'::character varying])::text[])))
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
-- Name: crm_tareas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_tareas (
    id integer NOT NULL,
    contacto_id integer NOT NULL,
    titulo character varying(300) NOT NULL,
    descripcion text,
    prioridad character varying(10) DEFAULT 'media'::character varying NOT NULL,
    estado character varying(20) DEFAULT 'pendiente'::character varying NOT NULL,
    fecha_limite date,
    asignado_a integer,
    creado_por integer,
    completada_en timestamp without time zone,
    CONSTRAINT crm_tareas_estado_check CHECK (((estado)::text = ANY ((ARRAY['pendiente'::character varying, 'completada'::character varying])::text[]))),
    CONSTRAINT crm_tareas_prioridad_check CHECK (((prioridad)::text = ANY ((ARRAY['alta'::character varying, 'media'::character varying, 'baja'::character varying])::text[])))
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
    fecha date DEFAULT CURRENT_DATE NOT NULL,
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
    total numeric(12,2) DEFAULT 0 NOT NULL,
    pdf_path character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    precio_unitario numeric(10,2) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    imagen_url text,
    descuento_porc numeric,
    iva_porc numeric
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
    valor numeric(12,2) DEFAULT 0 NOT NULL
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
    cantidad integer DEFAULT 1 NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    subtotal numeric(12,2) NOT NULL
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
    nombre character varying(50) NOT NULL
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
-- Name: google_oauth_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.google_oauth_tokens (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    access_token text NOT NULL,
    refresh_token text,
    token_expiry timestamp with time zone,
    scope text,
    updated_at timestamp with time zone
);


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
    porcentaje numeric(5,3) NOT NULL
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
    descripcion character varying(255),
    total_debito numeric(15,2),
    total_credito numeric(15,2),
    estado character varying(20) DEFAULT 'generado'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    debito numeric(15,2) DEFAULT 0,
    credito numeric(15,2) DEFAULT 0,
    tercero_nit character varying(20),
    centro_costo character varying(20)
);


--
-- Name: nomina_asientos_detalle_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_asientos_detalle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_asientos_detalle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_asientos_detalle_id_seq OWNED BY public.nomina_asientos_detalle.id;


--
-- Name: nomina_contratistas_pila; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_contratistas_pila (
    id integer NOT NULL,
    periodo_id integer,
    empleado_id integer,
    numero_planilla character varying(50),
    fecha_pago date,
    valor_pagado numeric(12,2),
    archivo_soporte character varying(255),
    verificado boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_contratistas_pila_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_contratistas_pila_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_contratistas_pila_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_contratistas_pila_id_seq OWNED BY public.nomina_contratistas_pila.id;


--
-- Name: nomina_detalle; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_detalle (
    id integer NOT NULL,
    periodo_id integer,
    empleado_id integer,
    dias_trabajados integer,
    sueldo_basico numeric(12,2) DEFAULT 0,
    auxilio_transporte numeric(12,2) DEFAULT 0,
    horas_extras numeric(12,2) DEFAULT 0,
    recargos numeric(12,2) DEFAULT 0,
    comisiones numeric(12,2) DEFAULT 0,
    bonificaciones numeric(12,2) DEFAULT 0,
    incapacidades numeric(12,2) DEFAULT 0,
    licencias numeric(12,2) DEFAULT 0,
    total_devengado numeric(12,2) DEFAULT 0,
    salud_empleado numeric(12,2) DEFAULT 0,
    pension_empleado numeric(12,2) DEFAULT 0,
    fondo_solidaridad numeric(12,2) DEFAULT 0,
    retencion_fuente numeric(12,2) DEFAULT 0,
    prestamos numeric(12,2) DEFAULT 0,
    otras_deducciones numeric(12,2) DEFAULT 0,
    total_deducido numeric(12,2) DEFAULT 0,
    neto_pagar numeric(12,2) DEFAULT 0,
    salud_empleador numeric(12,2) DEFAULT 0,
    pension_empleador numeric(12,2) DEFAULT 0,
    arl numeric(12,2) DEFAULT 0,
    sena numeric(12,2) DEFAULT 0,
    icbf numeric(12,2) DEFAULT 0,
    ccf numeric(12,2) DEFAULT 0,
    cesantias_provision numeric(12,2) DEFAULT 0,
    intereses_provision numeric(12,2) DEFAULT 0,
    prima_provision numeric(12,2) DEFAULT 0,
    vacaciones_provision numeric(12,2) DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    tipo_documento character varying(10) NOT NULL,
    numero_documento character varying(20) NOT NULL,
    nombres character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    email character varying(100),
    telefono character varying(20),
    direccion character varying(200),
    fecha_ingreso date NOT NULL,
    fecha_retiro date,
    tipo_vinculacion character varying(20) NOT NULL,
    cargo character varying(100),
    salario_base numeric(12,2) NOT NULL,
    nivel_arl character varying(10) DEFAULT 'I'::character varying,
    banco character varying(50),
    tipo_cuenta character varying(20),
    numero_cuenta character varying(50),
    eps character varying(100),
    fondo_pension character varying(100),
    fondo_cesantias character varying(100),
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
    motivo_retiro character varying(100),
    dias_liquidacion integer,
    salario_base_liquidacion numeric(12,2),
    cesantias numeric(12,2),
    intereses_cesantias numeric(12,2),
    prima_servicios numeric(12,2),
    vacaciones numeric(12,2),
    indemnizacion numeric(12,2) DEFAULT 0,
    salarios_pendientes numeric(12,2),
    deducciones_pendientes numeric(12,2),
    total_pagar numeric(12,2),
    estado character varying(20) DEFAULT 'borrador'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    tipo_novedad character varying(50) NOT NULL,
    cantidad numeric(10,2) NOT NULL,
    valor_unitario numeric(12,2),
    valor_total numeric(12,2),
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
    ccf numeric(5,2) NOT NULL,
    icbf numeric(5,2) NOT NULL,
    sena numeric(5,2) NOT NULL,
    tope_exoneracion numeric(5,2) DEFAULT 10.00,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_parafiscales_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_parafiscales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_parafiscales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_parafiscales_id_seq OWNED BY public.nomina_parafiscales.id;


--
-- Name: nomina_parametros; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_parametros (
    id integer NOT NULL,
    anio integer NOT NULL,
    salario_minimo numeric(12,2) NOT NULL,
    auxilio_transporte numeric(12,2) NOT NULL,
    uvt numeric(12,2) NOT NULL,
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
    estado character varying(20) DEFAULT 'borrador'::character varying,
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
    cesantias numeric(5,2) NOT NULL,
    intereses_cesantias numeric(5,2) NOT NULL,
    prima numeric(5,2) NOT NULL,
    vacaciones numeric(5,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_prestaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_prestaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_prestaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_prestaciones_id_seq OWNED BY public.nomina_prestaciones.id;


--
-- Name: nomina_retencion_tabla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_retencion_tabla (
    id integer NOT NULL,
    anio integer NOT NULL,
    rango_desde numeric(10,2) NOT NULL,
    rango_hasta numeric(10,2) NOT NULL,
    tarifa_marginal numeric(5,2) NOT NULL,
    uvt_mas numeric(10,2) NOT NULL,
    uvt_base numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: nomina_retencion_tabla_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nomina_retencion_tabla_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nomina_retencion_tabla_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nomina_retencion_tabla_id_seq OWNED BY public.nomina_retencion_tabla.id;


--
-- Name: nomina_seguridad_social; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_seguridad_social (
    id integer NOT NULL,
    anio integer NOT NULL,
    salud_empleado numeric(5,2) NOT NULL,
    salud_empleador numeric(5,2) NOT NULL,
    pension_empleado numeric(5,2) NOT NULL,
    pension_empleador numeric(5,2) NOT NULL,
    solidaridad_base numeric(5,2) DEFAULT 4.00,
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
    fecha timestamp without time zone
);


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
    CONSTRAINT check_estado_envio CHECK (((estado_envio)::text = ANY ((ARRAY['ESPERA_PAGO'::character varying, 'POR_DESPACHAR'::character varying, 'ENVIADO'::character varying, 'ENTREGADO'::character varying, 'CANCELADO'::character varying])::text[]))),
    CONSTRAINT check_estado_pago CHECK (((estado_pago)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'APROBADO'::character varying, 'RECHAZADO'::character varying, 'EXPIRADO'::character varying])::text[]))),
    CONSTRAINT check_tipo_documento CHECK (((cliente_tipo_documento)::text = ANY ((ARRAY['CC'::character varying, 'CE'::character varying, 'NIT'::character varying, 'TI'::character varying, 'PP'::character varying, 'IDC'::character varying])::text[])))
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
-- Name: producto_comentarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.producto_comentarios (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    usuario_id integer,
    autor_nombre character varying(100) NOT NULL,
    calificacion smallint NOT NULL,
    comentario text NOT NULL,
    aprobado boolean,
    fecha_creacion timestamp without time zone
);


--
-- Name: producto_imagenes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.producto_imagenes (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    imagen_url character varying(500) NOT NULL,
    orden integer,
    es_principal boolean
);


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.producto_imagenes_id_seq
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
    tenant_id integer
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
    precio_unitario numeric DEFAULT 0 NOT NULL,
    subtotal numeric DEFAULT 0 NOT NULL,
    estado character varying(20) DEFAULT 'pendiente'::character varying NOT NULL,
    notas text,
    creado_por integer,
    ordered_at timestamp without time zone DEFAULT now() NOT NULL,
    served_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: restaurant_table_consumptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.restaurant_table_consumptions_id_seq
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
    total_acumulado numeric DEFAULT 0 NOT NULL,
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
    cancelled_by integer
);


--
-- Name: restaurant_table_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.restaurant_table_orders_id_seq
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
    pos_x numeric DEFAULT 8 NOT NULL,
    pos_y numeric DEFAULT 10 NOT NULL,
    ancho numeric DEFAULT 16 NOT NULL,
    alto numeric DEFAULT 16 NOT NULL,
    rotacion smallint DEFAULT 0 NOT NULL,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL,
    creado_por integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: restaurant_tables_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.restaurant_tables_id_seq
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
    categoria character varying(60) NOT NULL,
    is_core boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: saas_tenant_modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saas_tenant_modules (
    tenant_id integer NOT NULL,
    module_id integer NOT NULL,
    is_active boolean NOT NULL,
    settings jsonb NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: saas_tenants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saas_tenants (
    id integer NOT NULL,
    slug character varying(80) NOT NULL,
    nombre character varying(180) NOT NULL,
    estado character varying(30) NOT NULL,
    is_default boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


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
    rol_sala character varying(20),
    invitado boolean,
    email_enviado boolean,
    se_unio boolean,
    fecha_union timestamp without time zone,
    created_at timestamp without time zone
);


--
-- Name: salas_video; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.salas_video (
    id integer NOT NULL,
    codigo_sala character varying(64) NOT NULL,
    nombre character varying(200) NOT NULL,
    descripcion text,
    creado_por integer,
    estado character varying(20) NOT NULL,
    fecha_inicio timestamp without time zone,
    fecha_fin timestamp without time zone,
    duracion_real integer,
    max_participantes integer,
    password_sala character varying(100),
    ticket_id integer,
    contacto_crm_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


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
-- Name: ticket_respuestas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ticket_respuestas (
    id integer NOT NULL,
    ticket_id integer NOT NULL,
    usuario_id integer NOT NULL,
    mensaje text NOT NULL,
    es_admin boolean,
    fecha timestamp with time zone
);


--
-- Name: tickets_soporte; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tickets_soporte (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    asunto text NOT NULL,
    mensaje text NOT NULL,
    estado text NOT NULL,
    fecha_creacion timestamp with time zone,
    fecha_actualizado timestamp with time zone
);


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
    telefono character varying(15),
    direccion character varying(255),
    fotografia character varying(255),
    estado character varying(20) DEFAULT 'habilitado'::character varying,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ultima_conexion timestamp without time zone,
    fecha_modificacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    google_sub character varying(255),
    tenant_id integer
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
    metodo_pago character varying(50) DEFAULT 'EFECTIVO'::character varying,
    subtotal numeric(12,2) DEFAULT 0,
    descuento numeric(12,2) DEFAULT 0,
    total numeric(12,2) DEFAULT 0,
    notas text,
    usuario_id integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    factura_dian_id uuid,
    estado character varying(20),
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
-- Name: contabilidad_movimientos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contabilidad_movimientos ALTER COLUMN id SET DEFAULT nextval('public.contabilidad_movimientos_id_seq'::regclass);


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
-- Name: nomina_asientos_detalle id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_detalle ALTER COLUMN id SET DEFAULT nextval('public.nomina_asientos_detalle_id_seq'::regclass);


--
-- Name: nomina_contratistas_pila id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_contratistas_pila ALTER COLUMN id SET DEFAULT nextval('public.nomina_contratistas_pila_id_seq'::regclass);


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
-- Name: nomina_parafiscales id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parafiscales ALTER COLUMN id SET DEFAULT nextval('public.nomina_parafiscales_id_seq'::regclass);


--
-- Name: nomina_parametros id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parametros ALTER COLUMN id SET DEFAULT nextval('public.nomina_parametros_id_seq'::regclass);


--
-- Name: nomina_periodos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_periodos ALTER COLUMN id SET DEFAULT nextval('public.nomina_periodos_id_seq'::regclass);


--
-- Name: nomina_prestaciones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_prestaciones ALTER COLUMN id SET DEFAULT nextval('public.nomina_prestaciones_id_seq'::regclass);


--
-- Name: nomina_retencion_tabla id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_retencion_tabla ALTER COLUMN id SET DEFAULT nextval('public.nomina_retencion_tabla_id_seq'::regclass);


--
-- Name: nomina_seguridad_social id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_seguridad_social ALTER COLUMN id SET DEFAULT nextval('public.nomina_seguridad_social_id_seq'::regclass);


--
-- Name: pedidos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos ALTER COLUMN id SET DEFAULT nextval('public.pedidos_id_seq'::regclass);


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
-- Name: servicios_home id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicios_home ALTER COLUMN id SET DEFAULT nextval('public.servicios_home_id_seq'::regclass);


--
-- Name: slides_home id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slides_home ALTER COLUMN id SET DEFAULT nextval('public.slides_home_id_seq'::regclass);


--
-- Name: software_planes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.software_planes ALTER COLUMN id SET DEFAULT nextval('public.software_planes_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: ventas_pos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ventas_pos ALTER COLUMN id SET DEFAULT nextval('public.ventas_pos_id_seq'::regclass);


--
-- Name: cliente_config cliente_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_config
    ADD CONSTRAINT cliente_config_pkey PRIMARY KEY (clave);


--
-- Name: config_secciones config_secciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_secciones
    ADD CONSTRAINT config_secciones_pkey PRIMARY KEY (clave);


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
-- Name: crm_tareas crm_tareas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT crm_tareas_pkey PRIMARY KEY (id);


--
-- Name: cuentas_cobro cuentas_cobro_consecutivo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuentas_cobro
    ADD CONSTRAINT cuentas_cobro_consecutivo_key UNIQUE (consecutivo);


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
-- Name: inventario_log inventario_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventario_log
    ADD CONSTRAINT inventario_log_pkey PRIMARY KEY (id);


--
-- Name: nomina_arl_niveles nomina_arl_niveles_anio_nivel_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_arl_niveles
    ADD CONSTRAINT nomina_arl_niveles_anio_nivel_key UNIQUE (anio, nivel);


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
-- Name: nomina_parafiscales nomina_parafiscales_anio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parafiscales
    ADD CONSTRAINT nomina_parafiscales_anio_key UNIQUE (anio);


--
-- Name: nomina_parafiscales nomina_parafiscales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parafiscales
    ADD CONSTRAINT nomina_parafiscales_pkey PRIMARY KEY (id);


--
-- Name: nomina_parametros nomina_parametros_anio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_parametros
    ADD CONSTRAINT nomina_parametros_anio_key UNIQUE (anio);


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
-- Name: nomina_prestaciones nomina_prestaciones_anio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_prestaciones
    ADD CONSTRAINT nomina_prestaciones_anio_key UNIQUE (anio);


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
-- Name: nomina_seguridad_social nomina_seguridad_social_anio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_seguridad_social
    ADD CONSTRAINT nomina_seguridad_social_anio_key UNIQUE (anio);


--
-- Name: nomina_seguridad_social nomina_seguridad_social_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_seguridad_social
    ADD CONSTRAINT nomina_seguridad_social_pkey PRIMARY KEY (id);


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
-- Name: servicios_home servicios_home_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicios_home
    ADD CONSTRAINT servicios_home_pkey PRIMARY KEY (id);


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
-- Name: idx_nomina_detalle_empleado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nomina_detalle_empleado ON public.nomina_detalle USING btree (empleado_id);


--
-- Name: idx_nomina_detalle_periodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nomina_detalle_periodo ON public.nomina_detalle USING btree (periodo_id);


--
-- Name: idx_nomina_novedades_periodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nomina_novedades_periodo ON public.nomina_novedades USING btree (periodo_id);


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
-- Name: crm_actividades crm_actividades_contacto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades
    ADD CONSTRAINT crm_actividades_contacto_id_fkey FOREIGN KEY (contacto_id) REFERENCES public.crm_contactos(id) ON DELETE CASCADE;


--
-- Name: crm_actividades crm_actividades_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_actividades
    ADD CONSTRAINT crm_actividades_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_contactos crm_contactos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_contactos
    ADD CONSTRAINT crm_contactos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_tareas crm_tareas_asignado_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT crm_tareas_asignado_a_fkey FOREIGN KEY (asignado_a) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: crm_tareas crm_tareas_contacto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT crm_tareas_contacto_id_fkey FOREIGN KEY (contacto_id) REFERENCES public.crm_contactos(id) ON DELETE CASCADE;


--
-- Name: crm_tareas crm_tareas_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_tareas
    ADD CONSTRAINT crm_tareas_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: detalle_cotizacion detalle_cotizacion_cotizacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cotizacion
    ADD CONSTRAINT detalle_cotizacion_cotizacion_id_fkey FOREIGN KEY (cotizacion_id) REFERENCES public.cotizaciones(id) ON DELETE CASCADE;


--
-- Name: detalle_cuenta_cobro detalle_cuenta_cobro_cuenta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_cuenta_cobro
    ADD CONSTRAINT detalle_cuenta_cobro_cuenta_id_fkey FOREIGN KEY (cuenta_id) REFERENCES public.cuentas_cobro(id) ON DELETE CASCADE;


--
-- Name: detalle_venta_pos detalle_venta_pos_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_venta_pos
    ADD CONSTRAINT detalle_venta_pos_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas_pos(id) ON DELETE CASCADE;


--
-- Name: detalle_pedidos fk_detalle_pedido; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalle_pedidos
    ADD CONSTRAINT fk_detalle_pedido FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


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
-- Name: nomina_asientos_detalle nomina_asientos_detalle_asiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_asientos_detalle
    ADD CONSTRAINT nomina_asientos_detalle_asiento_id_fkey FOREIGN KEY (asiento_id) REFERENCES public.nomina_asientos_contables(id);


--
-- Name: nomina_contratistas_pila nomina_contratistas_pila_empleado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_contratistas_pila
    ADD CONSTRAINT nomina_contratistas_pila_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.nomina_empleados(id);


--
-- Name: nomina_contratistas_pila nomina_contratistas_pila_periodo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_contratistas_pila
    ADD CONSTRAINT nomina_contratistas_pila_periodo_id_fkey FOREIGN KEY (periodo_id) REFERENCES public.nomina_periodos(id);


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
-- Name: productos productos_genero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_genero_id_fkey FOREIGN KEY (genero_id) REFERENCES public.generos(id);


--
-- Name: usuarios usuarios_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.roles(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Gap02RbxDWSaUsq0n9ZELaKPF71KvAMxndnvWe5Brtc8wRKh11tN9OhcFTOpAlY

