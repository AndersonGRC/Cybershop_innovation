#!/bin/bash
# cybershop-health.sh — Chequeo de salud de la flota CyberShop (SOLO LECTURA).
#
# Revisa: versión desplegada, cada instancia (systemd + /api/v1/health + home),
# el maestro, errores recientes de los crons de cobro, uso de disco y Postgres.
# Imprime un reporte y termina con código != 0 si hay algún problema — apto para
# cron + alerta (p.ej.:  bash cybershop-health.sh || mail -s "CyberShop ALERTA" tú@dominio).
#
# NO modifica nada. Instalar en /usr/local/sbin/ y (opcional) cron cada 5 min.
set -uo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

PROBLEMS=0   # duros → paginan (exit != 0)
WARN=0       # blandos → se reportan, no paginan
ok(){   echo "  ✓ $*"; }
bad(){  echo "  ✗ $*"; PROBLEMS=$((PROBLEMS+1)); }
warn(){ echo "  ⚠ $*"; WARN=$((WARN+1)); }

echo "=== CyberShop · salud de la flota · $(date -u +%FT%TZ) ==="

# 1) Código compartido desplegado
VER=$(grep -oE 'APP_VERSION = "[^"]+"' /var/www/CyberShop/app/config.py 2>/dev/null | cut -d'"' -f2)
HEAD=$(git -C /var/www/CyberShop rev-parse --short HEAD 2>/dev/null || echo '?')
echo "-- código -- APP_VERSION=${VER:-?}  HEAD=$HEAD"

# 2) Instancias web (tenants) + maestro
echo "-- instancias --"
for U in $(systemctl list-units --type=service --state=active --no-legend 'cybershop*' 2>/dev/null | awk '{print $1}'); do
  st=$(systemctl is-active "$U" 2>/dev/null)
  if [ "$U" = "cybershop-admin.service" ]; then
    PID=$(systemctl show "$U" -p MainPID --value 2>/dev/null)
    PORT=$(ss -ltnp 2>/dev/null | grep "pid=$PID," | grep -oE '127.0.0.1:[0-9]+' | head -1 | cut -d: -f2)
    hc=$(curl -s -o /dev/null -w '%{http_code}' --max-time 6 "http://127.0.0.1:${PORT:-0}/" 2>/dev/null || echo 000)
    { [ "$st" = "active" ] && [ "$hc" != "000" ] && [ "${hc:-500}" -lt 500 ]; } \
      && ok "maestro $U (puerto ${PORT:-?}) http=$hc" || bad "maestro $U estado=$st http=$hc"
    continue
  fi
  # slug + puerto
  if [ "$U" = "cybershop.service" ]; then slug="operador"; PORT=5001
  else slug=$(sed -E 's/^cybershop@(.*)\.service$/\1/' <<<"$U"); PORT=$(grep -h '^PORT=' "/etc/cybershop/${slug}.env" 2>/dev/null | cut -d= -f2); fi
  hc=$(curl -s -o /dev/null -w '%{http_code}' --max-time 6 "http://127.0.0.1:${PORT:-0}/api/v1/health" 2>/dev/null || echo 000)
  home=$(curl -s -o /dev/null -w '%{http_code}' --max-time 6 "http://127.0.0.1:${PORT:-0}/" 2>/dev/null || echo 000)
  info="$slug estado=$st puerto=${PORT:-?} health=$hc home=$home"
  if [ "$st" != "active" ]; then bad "$info (inactiva)"
  elif [ "$hc" != "200" ]; then bad "$info (app no responde /api/v1/health)"
  elif [ "$home" != "200" ] && [ "$home" != "302" ]; then warn "$info (home anómalo; app OK vía health)"
  else ok "$info"; fi
done

# 3) Crons de cobro: errores recientes en sus logs
echo "-- crons de cobro --"
for L in /var/log/cybershop-billing.log /var/log/cybershop-morosos.log; do
  [ -f "$L" ] || { echo "  (sin log $L)"; continue; }
  # Solo la ÚLTIMA corrida (desde la última línea con fecha [YYYY-...]) para evitar
  # ruido histórico; una corrida con error es un problema DURO (cron roto).
  ln=$(grep -nE '^\[20[0-9][0-9]-' "$L" 2>/dev/null | tail -1 | cut -d: -f1)
  blk=$([ -n "$ln" ] && tail -n +"$ln" "$L" || tail -n 50 "$L")
  err=$(grep -iE "traceback|exception|\[!\]|falló|failed" <<<"$blk" | head -2)
  [ -n "$err" ] && bad "$(basename "$L") (última corrida): $(tr '\n' '|' <<<"$err")" || ok "$(basename "$L") última corrida limpia"
done

# 4) Disco
echo "-- disco --"
df -hP / /var 2>/dev/null | awk 'NR>1{u=$5+0; s=(u>=90)?"✗":"✓"; print "  "s" "$6" usado "$5} '
df -P / | awk 'NR>1{ if ($5+0>=90) exit 1 }' || bad "disco / >= 90%"

# 5) Postgres
echo "-- postgres --"
sudo -u postgres psql -tAc "SELECT 1" >/dev/null 2>&1 && ok "postgres responde" || bad "postgres NO responde"

echo "=== problemas(P)=$PROBLEMS  warnings(W)=$WARN ==="
# Exit != 0 SOLO por problemas duros (los warnings no paginan).
[ "$PROBLEMS" -eq 0 ]
