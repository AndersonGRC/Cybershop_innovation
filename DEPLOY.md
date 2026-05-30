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
