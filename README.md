# CyberShopAdmin

Panel de administración SaaS para el ecosistema CyberShop. Permite crear, listar, suspender y rotar credenciales de los tenants (clientes) del SaaS sin necesidad de SSH a producción.

**Servicio independiente.** No es parte de la app CyberShop — corre como un Flask aparte, en su propio puerto y subdominio. Comparte únicamente la BD `saas_control_plane` y el `KMS_KEY` para cifrado de credenciales de tenants.

## Funcionalidad MVP

- Login con email + password.
- Dashboard con stats agregadas (tenants, keys, actividad).
- Listar tenants con buscador.
- Crear tenant nuevo (encapsula `createdb` + schema base + INSERT en control plane + emisión de primera API key).
- Detalle de tenant: ver sus API keys, generar nuevas, rotar, suspender.
- Suspender / reactivar un tenant completo.

## Dev local (Windows)

### Primera vez

```cmd
cd c:\Cybershop\CyberShopAdmin

REM 1. Configurar
copy .cybershop.conf.example .cybershop.conf
notepad .cybershop.conf
REM    Llenar: KMS_KEY (mismo que CyberShop), FLASK_SECRET_KEY (nuevo),
REM    credenciales Postgres locales, ruta PSQL_BIN, ruta TENANT_SCHEMA_FILE.

REM 2. Aplicar migration a tu Postgres local
python tools\apply_migrations.py

REM 3. Crear primer usuario admin
python tools\seed_admin.py --email admin@cybershop.local --nombre Admin

REM 4. Levantar
run.bat
```

Abrir http://localhost:5002 → login → dashboard.

### Cada vez después

```cmd
run.bat
```

## Producción (Linux VPS)

Ver [DEPLOY.md](DEPLOY.md) (se genera tras el primer build local exitoso).

## Stack

- **Backend:** Flask 3 + Jinja2
- **DB:** PostgreSQL (comparte `saas_control_plane` con CyberShop)
- **Frontend:** Server-rendered + [Pico.css](https://picocss.com) CDN + HTMX CDN (sin build step)
- **Auth:** Email/password con werkzeug pbkdf2 + sesión Flask
- **Deploy:** systemd unit + Nginx reverse proxy con IP allow-list

## Arquitectura

```
admin.cybershopcol.com → Flask :5002 → saas_control_plane (Postgres)
                                     → CREATE DATABASE cyber_tNNN
                                     → INSERT en tenants/tenant_databases/sync_api_keys
```

El servicio comparte el `KMS_KEY` con la app CyberShop para poder cifrar la contraseña de Postgres en `tenant_databases.db_password_enc` (formato AES-256-GCM, base64).

## Layout del repo

```
CyberShopAdmin/
├── app.py                  Flask factory + entrypoint
├── config.py               Config class (lee .cybershop.conf)
├── db.py                   Conexión a control plane Postgres
├── crypto.py               sha256_hex + AES-GCM helpers
├── auth.py                 @login_required + helpers de sesión
├── tenant_service.py       Orquesta create_tenant end-to-end
├── api_key_service.py      Generación/rotación de API keys
├── routes/                 Blueprints Flask
├── templates/              Jinja2
├── static/                 CSS
├── migrations/             SQL del control plane
├── tools/                  Scripts CLI (seed_admin, apply_migrations)
└── deploy/                 systemd unit + nginx server block
```
