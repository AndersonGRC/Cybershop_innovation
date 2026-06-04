# Plan — CyberShop Master (web service de administración multi-cliente)

> Plan aprobado. Fuente de verdad para la implementación. **Etapa 1 = solo `CyberShopAdmin/` + control plane; CERO cambios en `CyberShop/app/`** hasta validar pruebas.

## Context

Web service maestro ("CyberShop Master") para administrar muchos clientes del SaaS: crear, activar, suspender (deshabilitar ingreso) y destruir clientes, y asignar **módulos por plan**. Cada cliente tiene **BD y datos aislados**; la **config de cuenta (plan, módulos, estado, dominio) la administra el maestro**. El sitio público de cada cliente es **personalizable (colores)**; el **/admin es siempre el mismo código** (solo cambian datos por ser otra BD).

**REGLAS DEL USUARIO (mandatorias):**
1. **Guardar este plan en un `.md` del repo ANTES de iniciar** (este archivo).
2. **NO borrar ni modificar NADA de `CyberShop/app/`** hasta que la administración esté **probada en el nuevo web service**. Toda la Etapa 1 vive en `CyberShopAdmin/` + control plane.
3. **Reusar lo que ya existe**; no tocar archivos que no corresponden (no romper funcionalidades).
4. **Espejar el módulo `/admin` pero a nivel multi-cliente** (el maestro administra la config de cada cliente conectándose a su BD con las tablas que el app ya usa).
5. La **depuración** de CyberShop (quitarle lo de administración SaaS, bloqueo en login in-app, módulos desde control plane) es una **Etapa 2 posterior**, solo después de pruebas.

**Lo que YA existe (reusar, no reinventar):**
- `CyberShopAdmin/` (Flask independiente, :5002, `admin.cybershopcol.com`): `tenant_service.create_tenant()` (CREATE DATABASE + schema + control plane + 1ª API key), `set_estado`, `api_key_service`, UI list/new/detail/created, `db.py`/`crypto.py`/`auth.py`, `deploy/`, `tools/`. Git local (1 commit; **confirmar/añadir remoto GitHub** y push).
- Control plane (`saas_control_plane`): `tenants(estado, plan)`, `tenant_databases(creds AES-GCM)`, `usuarios_globales`, `sync_api_keys`.
- Web app (NO tocar en Etapa 1): `tenant_features.py` ya **lee** módulos desde la BD del tenant (`saas_tenant_modules` / `cliente_config`), `public_site_service` (config/colores/secciones), `sync_api_keys`. `/admin/configuracion-cliente`, `/admin/sitio-publico`, `/admin/sync-keys` como referencia de UI.
- Infra: **Caddy** (reverse proxy + TLS auto), gunicorn systemd. Prod en `/var/www/CyberShop`.

**Gaps:** `TENANT_SCHEMA_FILE` = stub 1.3 KB (no es el schema real); tenant nuevo sin seed (sin admin → no entra; sin colores → home roto); el maestro no asigna módulos ni administra config por cliente; no hay destroy/DROP ni provisión de instancia/puerto/dominio.

---

# ETAPA 1 — Todo en CyberShopAdmin + control plane (sin tocar CyberShop/app)

> Paso 0: escribir este plan en `CyberShopAdmin/docs/PLAN_MASTER.md`. ✅ (este archivo)

## 1A. Schema template real + seed (cimiento)
- `CyberShopAdmin/tools/refresh_tenant_schema.py` (nuevo): `pg_dump --schema-only --no-owner --no-privileges cybershop > schema/tenant_schema.sql`. Apuntar `TENANT_SCHEMA_FILE` a él (config). Re-correr cuando cambie el schema del maestro.
- `CyberShopAdmin/schema/tenant_seed.sql` parametrizado (psycopg2 params): `roles` (7), 1 `usuarios` admin (rol propietario=2, email del form, **password temporal** generado), `cliente_config` colores de marca por defecto (azules reales, **no blanco**) + `empresa_nombre`, `config_secciones` on, `public_site_settings` mínimo, opcional 1 género+producto muestra.
- `tenant_service.create_tenant`: corregir `_apply_schema` (usar dump real) + nuevo `_apply_seed(db_name, {nombre, admin_email, admin_password, colores})`; devolver credenciales admin (mostrar 1 vez junto a la api_key).
- **Archivos (solo CyberShopAdmin):** `tools/refresh_tenant_schema.py`, `schema/tenant_seed.sql`, `tenant_service.py`, `config.py`.

## 1B. Administración de cada cliente desde el maestro (espejo de /admin, multi-cliente)
El maestro se conecta a la **BD del tenant** (creds en `tenant_databases`, descifradas con `crypto.py`) y reusa las MISMAS tablas que el app ya consume — **sin tocar el código del app**.
- `CyberShopAdmin/tenant_db.py` (nuevo): helper `tenant_cursor(tenant_id)` que abre conexión a `cyber_tNNN` (patrón de `db.py`).
- **Config/colores/empresa:** leer/escribir `cliente_config` del cliente (espejo de `/admin/configuracion-cliente`).
- **Secciones públicas:** leer/escribir `config_secciones` / `public_site_settings` (espejo de `/admin/sitio-publico#sections`).
- **Módulos por cliente:** escribir en `saas_tenant_modules` + `cliente_config` del tenant con el MISMO patrón que `tenant_features.set_tenant_module_state` (que el app ya lee). Así los módulos surten efecto **sin modificar CyberShop**. Plan→módulos: tabla de defaults en el maestro aplicada a esas tablas del tenant.
- **Sync keys:** ya existe (`api_key_service`).
- **Archivos (solo CyberShopAdmin):** `tenant_db.py`, `client_config_service.py`, `module_service.py`, rutas en `routes/tenant_routes.py`, templates (pestañas en `tenant_detail.html`: Config, Secciones, Módulos, Keys).

## 1B-bis. Integraciones / credenciales de API por cliente (visual, no-invasivo)
El operador de CyberShopAdmin (persona técnica) administra **visualmente** las credenciales de integración de cada cliente. El app **ya lee** estas credenciales desde variables de entorno, así que el maestro las gestiona **escribiendo el `EnvironmentFile` por instancia** (`/etc/cybershop/<slug>.env`) y reiniciando la instancia — **sin tocar `CyberShop/app/`**.
- **Pasarela de pagos PayU/PSE:** `PAYU_MERCHANT_ID`, `PAYU_ACCOUNT_ID`, `PAYU_API_KEY`, `PAYU_ENV` (sandbox/prod).
- **Google OAuth / Login:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GOOGLE_LOGIN_REDIRECT_URI`.
- **Email/SMTP (Gmail):** `MAIL_*` (server, port, username, password, default sender).
- **reCAPTCHA:** `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY`.
- **Meta Pixel/CAPI:** pixel id + token (si aplica).
- **Facturación DIAN:** `BILLING_*` / endpoint del microservicio.
- **Otras conexiones** que el app requiera por env.
- **UX:** pestaña "Integraciones" en `tenant_detail` con grupos colapsables; secretos **enmascarados** (mostrar solo prefijo), guardar solo los campos cambiados; al guardar → reescribe el env del cliente y `systemctl restart cybershop@<slug>`. Validadores básicos (URLs, env sandbox/prod).
- **Archivos (solo CyberShopAdmin):** `integrations_service.py` (lee/escribe el env por instancia, catálogo de campos con flag `secret`), rutas + template. En LOCAL se escribe un `.env` por tenant en una carpeta de pruebas; en prod es `/etc/cybershop/<slug>.env` (compartido con 1C).
- **Etapa 2 (futuro):** mover estas credenciales a almacenamiento **cifrado en el control plane** leído por el app (requiere tocar `CyberShop/app/config.py` → diferido).

## 1C. Aprovisionamiento de instancia + dominio (por cliente, mismo server, puerto distinto)
- Control plane: `tenant_runtime(tenant_id PK, port UNIQUE, subdomain, custom_domain, instance_status)` (migración `0003_runtime.sql`).
- `CyberShopAdmin/provisioning_service.py` (nuevo): `allocate_port()` (rango 8100–8999, verificado), `write_env_file()` → `/etc/cybershop/<slug>.env` (PORT, DB_NAME, DEFAULT_TENANT_*), `enable_service()` → unit templada `cybershop@<slug>` que corre el **código compartido** de `/var/www/CyberShop`, `write_caddy_site()`/Admin API + reload. Subdominio = wildcard `*.cybershopcol.com`; dominio propio = on-demand TLS.
- `deploy/cybershop@.service` (templada, `EnvironmentFile=/etc/cybershop/%i.env`, `--bind 127.0.0.1:${PORT}`).
- `create_tenant` orquesta: DB → schema → seed → control plane (tenants/tenant_databases/tenant_runtime) → módulos default del plan → provisionar instancia → provisionar dominio → API key.

## 1D. Ciclo de vida + destroy
- **Suspender (deshabilitar ingreso) sin tocar CyberShop:** `systemctl stop cybershop@<slug>` (el sitio del cliente cae → nadie entra) + `set_estado('suspendido')` (desactiva keys). Reactivar = start + estado activo.
- **Destroy soft (default):** `estado=cancelado` + `pg_dump` backup a `/var/backups/cybershop/<slug>-<ts>.sql.gz` + stop service + quitar bloque Caddy (conserva BD).
- **Destroy hard (explícito, type-to-confirm):** lo anterior + `DROP DATABASE` + borrar env/unit. Opción del software cuando el admin lo decida.

## 1E. Repo + deploy del maestro
- Confirmar/añadir remoto GitHub de `CyberShopAdmin` y push.
- Deploy en `admin.cybershopcol.com` (`deploy/cybershop-admin.service` + Caddy con IP allow-list). Maestro con **sudo acotado** (systemctl `cybershop@*`, caddy reload/Admin API, createdb/dropdb/pg_dump/psql, escribir `/etc/cybershop/*.env` y `/etc/caddy/sites/*`).

## Verificación Etapa 1 (sin tocar CyberShop/app)
1. `refresh_tenant_schema.py` genera el dump completo. Crear cliente `demo-uno` → BD creada y **seedeada**, instancia arriba en su puerto, Caddy sirviendo `demo-uno.cybershopcol.com` con TLS.
2. Entrar a `demo-uno.cybershopcol.com/admin` con el admin seedeado → funciona; home público renderiza con colores; el cliente cambia colores.
3. Desde el maestro: cambiar colores/secciones del cliente → se reflejan en su sitio. Plan=`basico` → en el admin del cliente solo se ven los módulos del plan (porque el app ya lee `saas_tenant_modules`).
4. Suspender → `systemctl stop` → el sitio no permite entrar; reactivar → vuelve.
5. Destroy soft → backup + BD conservada. Hard destroy en uno descartable → BD eliminada.

---

# ETAPA 2 — Depuración e integración en CyberShop (DESPUÉS de probar Etapa 1)

> Solo cuando la administración esté validada en el maestro. Aquí sí se toca `CyberShop/app/`, con cuidado.
- **Centralizar módulos en control plane** (`plan_modules` + `tenant_modules`) y que `tenant_features.py` los lea desde ahí (migrar desde el modelo tenant-DB de Etapa 1).
- **Bloqueo de ingreso in-app**: login/`before_request` consulta `estado` del control plane y muestra "cuenta suspendida" (en vez de solo apagar la instancia).
- **Depurar `/admin`**: mover/retirar de CyberShop lo que sea administración SaaS cross-tenant (p.ej. gestión de sync-keys, `saas_modules_admin`) para que viva solo en el maestro; el `/admin` del cliente conserva solo la administración de SUS datos.
- **Evolución a escala**: de instancia-por-puerto a instancia compartida con routing por dominio (el control plane ya lo soporta; cambian resolver + proxy).

---

## Riesgos / decisiones
- **No invasivo (Etapa 1):** ningún archivo de `CyberShop/app/` se modifica; el maestro escribe en las tablas del tenant que el app YA consume. Suspensión = apagar la instancia.
- **Privilegios del maestro:** sudo acotado (least privilege) para systemctl/caddy/createdb/dropdb/pg_dump/escribir archivos.
- **Drift de schema:** re-correr `refresh_tenant_schema` y aplicar migraciones a tenants existentes (`migrate_all_tenants.py`) cuando cambie el maestro.
- **Código compartido, N instancias:** un `git pull` en `/var/www/CyberShop` + `systemctl restart cybershop@*` actualiza todas.
- **Branding** en la BD del cliente (lo administra el cliente y el maestro); **plan/módulos/estado/dominio** en control plane (solo el maestro).
- **Archivos a crear (Etapa 1, todos en CyberShopAdmin):** `docs/PLAN_MASTER.md`, `tools/refresh_tenant_schema.py`, `schema/tenant_seed.sql`, `tenant_db.py`, `client_config_service.py`, `module_service.py`, `provisioning_service.py`, `deploy/cybershop@.service`, migración `0003_runtime.sql`; editar `tenant_service.py`, `config.py`, `routes/tenant_routes.py`, templates. **Cero cambios en `CyberShop/app/`.**
