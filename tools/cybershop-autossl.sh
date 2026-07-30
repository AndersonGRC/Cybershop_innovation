#!/bin/bash
# cybershop-autossl.sh — Emite el certificado SSL de los DOMINIOS PROPIOS de los
# tenants automáticamente, en cuanto su DNS ya apunta a este servidor.
#
# Por qué: al crear un cliente con dominio propio, el operador suele configurar
# el DNS DESPUÉS. certbot no puede emitir hasta que el dominio resuelva a este
# servidor. Este script (via timer systemd, cada ~30 min) reintenta y emite en
# cuanto el DNS esté listo. Idempotente y seguro: solo dominios registrados por
# el operador, solo si resuelven aquí, y una sola vez (si ya hay cert, salta).
set -o pipefail

SERVER_IP="38.134.148.47"
EMAIL="cybershop.digitalsales@gmail.com"
LOG="/var/log/cybershop-autossl.log"
NGX_DIRS="/etc/nginx/cybershop-sites /etc/nginx/sites-available"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

# Dominios propios de tenants ACTIVOS (fuente autoritativa: control plane).
domains=$(sudo -u postgres psql -d saas_control_plane -tAc \
  "SELECT tr.custom_domain FROM tenant_runtime tr JOIN tenants t ON t.id = tr.tenant_id
   WHERE tr.custom_domain IS NOT NULL AND tr.custom_domain <> '' AND t.estado = 'activo'" 2>/dev/null)

for d in $domains; do
    # 1) ¿ya tiene certificado? -> nada que hacer
    [ -d "/etc/letsencrypt/live/$d" ] && continue

    # 2) ¿existe un bloque nginx para el dominio? (sin bloque, certbot --nginx no puede)
    found=""
    for dir in $NGX_DIRS; do [ -f "$dir/$d.conf" ] && found=1; done
    [ -z "$found" ] && { log "$d: sin bloque nginx, salto"; continue; }

    # 3) ¿el DNS del dominio ya apunta a ESTE servidor? (evita gastar intentos)
    ips=$(getent ahostsv4 "$d" 2>/dev/null | awk '{print $1}' | sort -u)
    if ! echo "$ips" | grep -qx "$SERVER_IP"; then
        log "$d: DNS aun no apunta a $SERVER_IP (=[$ips]), reintento luego"
        continue
    fi

    # 4) Emitir (una sola vez; si falla, se reintenta al siguiente ciclo)
    log "$d: DNS OK -> emitiendo certificado..."
    if certbot --nginx -d "$d" --non-interactive --agree-tos -m "$EMAIL" --redirect >> "$LOG" 2>&1; then
        log "$d: certificado EMITIDO OK"
    else
        log "$d: FALLO certbot (se reintenta en el proximo ciclo)"
    fi
done
