# Deploy a producción (VPS Linux)

Asume Ubuntu/Debian con Postgres + Nginx ya corriendo (el mismo VPS donde corre CyberShop).

## Prerequisitos en el VPS

- Postgres con `saas_control_plane` accesible (lo usa CyberShop).
- Python 3.11+ con `python3-venv`.
- Nginx instalado.
- `certbot` con plugin nginx (`python3-certbot-nginx`).
- Mismo `KMS_KEY` que CyberShop (lo verás en `/var/www/CyberShop/app/.cybershop.conf`).

## Paso a paso

### 1. Clonar el repo

```bash
ssh -p 2222 root@38.134.148.47

cd /var/www
git clone <tu-repo-github>/CyberShopAdmin.git
cd CyberShopAdmin

# Que www-data sea owner (lo necesita el systemd unit)
chown -R www-data:www-data /var/www/CyberShopAdmin
```

### 2. Crear venv + instalar deps

```bash
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### 3. Configurar `.cybershop.conf`

```bash
cp .cybershop.conf.example .cybershop.conf
nano .cybershop.conf
```

Valores críticos a llenar:

| Variable | Valor |
|---|---|
| `FLASK_SECRET_KEY` | Generar único: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `SESSION_COOKIE_SECURE` | `true` (estamos en HTTPS) |
| `CONTROL_PLANE_DB_PASSWORD` | Misma que usa CyberShop |
| `DB_PASSWORD` | Misma que usa CyberShop (superuser de Postgres) |
| `KMS_KEY` | **DEBE ser idéntica a la de `/var/www/CyberShop/app/.cybershop.conf`** |
| `TENANT_SCHEMA_FILE` | `/var/www/CyberShop/app/migrate_backup_db.sql` |
| `PSQL_BIN` | `/usr/bin/psql` |

```bash
chmod 600 .cybershop.conf
chown www-data:www-data .cybershop.conf
```

### 4. Aplicar migración

```bash
sudo -u www-data venv/bin/python tools/apply_migrations.py
```

Debería imprimir:
```
Encontrados 1 archivo(s):
  - 0003_admin_users.sql

Aplicando 0003_admin_users.sql... OK

[COMPLETADO] Todas las migrations aplicadas.
```

### 5. Crear primer admin user

```bash
sudo -u www-data venv/bin/python tools/seed_admin.py \
    --email tu@email.com \
    --nombre "Tu Nombre"
# Te pide password interactivamente. Min 8 chars.
```

### 6. Instalar systemd unit

```bash
sudo cp deploy/cybershop-admin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cybershop-admin
sudo systemctl start cybershop-admin

# Verificar
sudo systemctl status cybershop-admin
sudo journalctl -u cybershop-admin -f --since "1 minute ago"
```

El proceso debe estar `active (running)` y escuchando en `127.0.0.1:5002`.

```bash
# Test directo (sin nginx)
curl -I http://127.0.0.1:5002/login
# Esperado: HTTP/1.1 200 OK
```

### 7. DNS

En tu proveedor de DNS (Cloudflare, GoDaddy, etc.):

```
Tipo: A
Nombre: admin
Destino: 38.134.148.47
TTL: 3600
```

Verificar:
```bash
dig +short admin.cybershopcol.com
# Esperado: 38.134.148.47
```

### 8. Nginx + TLS

```bash
sudo cp deploy/nginx.admin.conf /etc/nginx/sites-available/admin.cybershopcol.com

# IMPORTANTE: editar IP allow-list con tu IP real
sudo nano /etc/nginx/sites-available/admin.cybershopcol.com
# Buscar las líneas `# allow ...; / deny all;` y descomentar+rellenar.
# Si NO querés allow-list (acceso desde cualquier IP, solo protegido por
# el login del panel), dejá comentadas esas líneas — es válido.

sudo ln -s /etc/nginx/sites-available/admin.cybershopcol.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. TLS con Let's Encrypt

```bash
sudo certbot --nginx -d admin.cybershopcol.com
# Acepta términos, da tu email, elige redirect HTTP→HTTPS (opción 2)
```

### 10. Probar

Browser: https://admin.cybershopcol.com → login → dashboard.

## Mantenimiento

### Actualizar código (deploy de cambios)

```bash
ssh -p 2222 root@38.134.148.47
cd /var/www/CyberShopAdmin
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -r requirements.txt  # solo si requirements.txt cambió
sudo systemctl restart cybershop-admin
sudo journalctl -u cybershop-admin -n 50
```

### Aplicar nueva migración

```bash
sudo -u www-data venv/bin/python tools/apply_migrations.py
sudo systemctl restart cybershop-admin   # si el código nuevo depende del schema
```

### Crear otro admin user

```bash
sudo -u www-data venv/bin/python tools/seed_admin.py --email otro@email.com --nombre Otro
```

### Logs

```bash
# Logs del servicio
sudo journalctl -u cybershop-admin -f

# Logs de nginx
sudo tail -f /var/log/nginx/admin.cybershopcol.com-access.log
sudo tail -f /var/log/nginx/admin.cybershopcol.com-error.log
```

### Backup de admin_users

Aunque `admin_users` vive en `saas_control_plane` (ya respaldado con
backups de Postgres), si querés un dump puntual:

```bash
sudo -u postgres pg_dump -t admin_users saas_control_plane > admin_users.sql
```

## Troubleshooting

### "FLASK_SECRET_KEY no está configurada"

Falta `.cybershop.conf` o no tiene esa variable. Verificar:
```bash
cat /var/www/CyberShopAdmin/.cybershop.conf | grep FLASK_SECRET_KEY
```

### "KMS_KEY no configurada"

Igual que arriba pero con `KMS_KEY`. **DEBE ser idéntica a CyberShop.**
Si la copiás mal, el admin no podrá descifrar las credenciales que cifra
CyberShop (y viceversa) — ningún tenant existente funciona.

### El servicio no levanta — `Permission denied`

`/var/www/CyberShopAdmin` debe ser owned by `www-data`:
```bash
sudo chown -R www-data:www-data /var/www/CyberShopAdmin
```

### Creo un tenant pero psql falla con "could not execute query"

`TENANT_SCHEMA_FILE` apunta a un archivo inexistente. Verificar:
```bash
ls -la /var/www/CyberShop/app/migrate_backup_db.sql
```

Si la ruta es otra, ajustar `TENANT_SCHEMA_FILE` en `.cybershop.conf`.

### Login dice "Email o contraseña inválidos" pero la password es correcta

Probablemente el usuario está `active=FALSE` o nunca se creó.
```bash
sudo -u postgres psql saas_control_plane -c "SELECT id, email, active FROM admin_users;"
```

Si no aparece, correr `seed_admin.py`. Si aparece con `active=false`:
```bash
sudo -u postgres psql saas_control_plane -c "UPDATE admin_users SET active=TRUE WHERE email='tu@email.com';"
```

---

# Entorno multi-cliente (serving de clientes + actualizaciones)

> Esto es lo que convierte al maestro en "desplegar un entorno total":
> levantar la infra que sirve a CADA cliente y actualizar a los existentes
> **sin afectar lo ya creado** (todo aditivo e idempotente).

## A. Config extra del maestro (`.cybershop.conf`)

```ini
# Plantilla de estructura para clientes nuevos (regenerar en el server, ver C)
TENANT_SCHEMA_FILE=/var/www/CyberShopAdmin/schema/tenant_schema.sql
MASTER_DB_NAME=cybershop

# EnvironmentFiles por instancia + dominios + backups
INSTANCE_ENV_DIR=/etc/cybershop
CADDY_SITES_DIR=/etc/caddy/sites
BASE_DOMAIN=cybershopcol.com
APP_DIR=/var/www/CyberShop            # código COMPARTIDO de CyberShop
BACKUP_DIR=/var/backups/cybershop
PORT_MIN=8100
PORT_MAX=8999
```

### Respaldo de todas las bases registradas

El cron de las 03:30 ejecuta `/usr/local/bin/cybershop-backup.sh`. Su fuente
versionable está en `deploy/cybershop-backup.sh`: consulta
`saas_control_plane.tenant_databases` y respalda **cada** base registrada,
incluidas las suspendidas y las de nombre heredado que no siguen el patrón
`cyber_tNNN`. También respalda el propio plano de control. El script anterior
basado solo en el patrón `^cyber_t[0-9]+$` omitía bases con nombre propio.

Antes de instalarlo, usar `bash -n deploy/cybershop-backup.sh` y comparar
`bash deploy/cybershop-backup.sh --list` con el inventario del maestro. Conservar
una copia del script instalado, instalar el nuevo con permisos de root y probar
`/usr/local/bin/cybershop-backup.sh --no-prune`: crea respaldos nuevos sin
borrar los antiguos. Confirmar que hay un `.sql.gz` no vacío por cada base,
que `gzip -t` pasa y que una restauración en un entorno aislado funciona. El
cron normal conserva la rotación de siete días; `--no-prune` es solo para la
prueba controlada. No copiar respaldos de clientes al repositorio ni restaurar
uno sobre la base de otro cliente.

## B. Infra de serving (una sola vez en el servidor)

1. **Código compartido + venv del app** ya en `/var/www/CyberShop` (con `app/env/`).
2. **Generar el schema real** de los clientes nuevos:
   ```bash
   sudo -u www-data venv/bin/python tools/refresh_tenant_schema.py   # -> schema/tenant_schema.sql
   ```
3. **Unit templada por cliente**:
   ```bash
   sudo cp deploy/cybershop@.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo mkdir -p /etc/cybershop                 # EnvironmentFiles
   sudo mkdir -p /var/backups/cybershop
   ```
4. **Caddy** (reverse proxy + TLS de cada cliente). Caddyfile:
   ```
   # Wildcard de subdominios (requiere token DNS del proveedor para DNS-01)
   *.cybershopcol.com {
       tls { dns <proveedor> <token> }
       # el bloque concreto por cliente lo escribe el maestro en /etc/caddy/sites
   }
   import /etc/caddy/sites/*.caddy
   ```
   ```bash
   sudo mkdir -p /etc/caddy/sites && sudo systemctl reload caddy
   ```
   - Subdominios: instantáneos con el wildcard. Dominios propios: Caddy emite el cert al vincularlos (on-demand TLS).
5. **sudoers acotado** para el usuario del maestro (least privilege): `systemctl (start|stop|restart|enable) cybershop@*`, `systemctl reload caddy`, `createdb`/`dropdb`/`pg_dump`/`psql`, y escribir en `/etc/cybershop/*` y `/etc/caddy/sites/*`.

Con esto, **crear un cliente desde el panel** ya levanta su BD + instancia + dominio.

## C. Flujo de ACTUALIZACIÓN (controlado por cliente)

### Ruta actual para este lote: maestro primero, después botón por cliente

Ver `CyberShop/app/docs/IA_ACTUALIZACION_CLIENTES.md` en el repositorio web
(los dos repositorios están separados en GitHub).
El botón **no actualiza este repo**: primero hay que publicar `CyberShopAdmin`
con las migraciones tenant nuevas (`0015` incluida) y reiniciar el maestro.
El código de `CyberShop` es compartido: el primer clic lo integra para todos;
cada clic migra solo la BD del cliente elegido y **recarga** solo su instancia.
No usar el antiguo `git pull` + reinicio masivo como si fuera un despliegue
aislado o equivalente al botón. Tampoco instalará dependencias, env ni units.

La implementación integra código **antes** de migrar la BD seleccionada. Si
falla la migración/recarga, el código global puede quedar actualizado; detener
el rollout y diagnosticar el estado antes de reintentar. Para cambios de
esquema, el código debe tolerar bases aún sin migrar o se requiere un
procedimiento manual de migración previa coordinada.

### Actualizar el maestro
```bash
cd /var/www/CyberShopAdmin && sudo -u www-data git pull
sudo -u www-data venv/bin/python tools/apply_migrations.py      # migraciones del control plane
sudo systemctl restart cybershop-admin
```

### Instancia principal: IA administrada desde el maestro (una sola vez)
La principal (`cybershop.service`) lee su `.cybershop.conf`. Al guardar
Integraciones de la principal, el maestro escribe SOLO los ajustes de IA
(Asistente IA + respaldo Anthropic) en `/etc/cybershop/<slug>.ia.env`. Para que
la principal los cargue:
```bash
sudo install -D -m 644 deploy/cybershop-ia-env.conf \
    /etc/systemd/system/cybershop.service.d/ia-env.conf
sudo systemctl daemon-reload && sudo systemctl restart cybershop
```
Antes de instalarlo, comparar los `AI_BASE_URL`/`AI_MODEL` de ese archivo con los
de `.cybershop.conf`: los del archivo ganan. Pagos, correo y DIAN no se tocan.

### Reglas de oro
- **Migraciones de tenant SOLO aditivas e idempotentes** (`IF NOT EXISTS`). Nunca DROP/ALTER destructivo. Ver `migrations/tenant/README.md`.
- `migrate_tenants.py` es seguro de re-correr: salta lo ya aplicado por cliente.
- Clientes **nuevos** ya traen todo por el dump; se marcan migraciones como aplicadas al crearse.
- Tras tocar el schema del maestro: `refresh_tenant_schema.py` (para los nuevos) **+** una migración de tenant aditiva (para los existentes).

## D. Reverse proxy de clientes con NGINX (default)

`PROXY_BACKEND=nginx`. Al asignar el dominio de un cliente, el maestro escribe
`/etc/nginx/sites-available/<dominio>.conf` (un `server` que hace
`proxy_pass http://127.0.0.1:<puerto>`), lo enlaza a `sites-enabled`, corre
`nginx -t` y `systemctl reload nginx`. Así el dominio queda **cuadrado con el
puerto abierto** de esa instancia.

- **SSL subdominios**: lo más simple es un **cert wildcard** `*.cybershopcol.com`
  (certbot DNS-01 con Cloudflare) y definir `WILDCARD_SSL_CERT/KEY` → los
  subdominios quedan en HTTPS al instante.
- **SSL dominio propio**: `sudo certbot --nginx -d sutienda.com` tras vincularlo.
- **sudoers** del maestro: además de lo anterior, permitir escribir en
  `/etc/nginx/sites-available` y `sites-enabled`, y `nginx -t` + `systemctl reload nginx`.
- El bloque exacto se previsualiza en el panel (pestaña Técnico → "Ver configuración del proxy").

---

## Actualizar clientes a la última versión (despliegue por cliente)

Flujo completo (obligatorio para nuevos desarrollos): ver el repo de la app en
`CyberShop/app/docs/flujo_desarrollo_y_despliegue.md`.

**Resumen operativo** — pestaña **Técnico** de cada tenant:
- **Actualizar app (después del login)**: `git pull` con **GATE de cambios públicos** + migrar BD
  (aditivo) + **recargar** la instancia. Se **bloquea** si el push tocó una ruta pública
  enumerada en `PUBLIC_PATHS`.
- **Deploy completo (incluye público)**: igual, pero también publica el sitio público.

Ni el botón normal ni «Deploy completo» actualizan `CyberShopAdmin`, el POS de
escritorio ni la configuración de entorno de las instancias. El código/estáticos
compartidos pueden afectar al sitio público aun si no se cambió una ruta de
`PUBLIC_PATHS`; los datos y overrides propios siguen fuera del repo.

**Infra:** script root `/usr/local/bin/cybershop-deploy-code.sh` (subcomandos `changes`/`apply`)
+ `/etc/sudoers.d/cybershop-deploy` (www-data, NOPASSWD, solo esos 2 subcomandos). El *gate* vive en
`provisioning_service.py::PUBLIC_PATHS`. `git merge --ff-only` nunca pisa cambios locales → los
hot-fixes hechos por SSH **deben commitearse/pushearse** o el deploy falla avisando. La fuente
de ese script y su sudoers no está versionada en estos repos; comprobarlos en el VPS antes
de considerar operativo el botón.

El ejemplo `deploy/nginx.admin.conf` amplía el tiempo de espera del proxy a
360 segundos porque dos pasos Git más una migración pueden superar los 60
anteriores. Instalar/probar esta configuración en el VPS y recargar NGINX por
el procedimiento de infraestructura; cambiar el archivo del repo no altera
el proxy activo. Un 504 no demuestra rollback: revisar Git, la BD y systemd.
