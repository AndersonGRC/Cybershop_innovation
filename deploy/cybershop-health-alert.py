#!/var/www/CyberShop/app/env/bin/python
"""Corre cybershop-health.sh; si hay PROBLEMAS DUROS (exit != 0) alerta por email
(Gmail del operador) con throttle de 1 hora. Pensado para cron.

Read-only salvo por (a) el email de alerta y (b) el archivo de estado del throttle.
Los warnings (p.ej. demo con home 503) NO paginan."""
import os
import subprocess
import sys
import time

HEALTH = "/usr/local/sbin/cybershop-health.sh"
STATE = "/var/lib/cybershop/health_last_alert"
THROTTLE = 3600  # como máximo 1 alerta por hora
APP_DIR = "/var/www/CyberShop/app"


def main():
    try:
        r = subprocess.run(["bash", HEALTH], capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        print(f"no se pudo ejecutar {HEALTH}: {e}")
        return
    report = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
    print(report)
    if r.returncode == 0:
        return  # sin problemas duros

    now = int(time.time())
    last = 0
    try:
        last = int(open(STATE).read().strip())
    except Exception:
        pass
    if now - last < THROTTLE:
        print("(throttle: alerta enviada hace <1h, no reenvío)")
        return

    sys.path.insert(0, APP_DIR)
    os.chdir(APP_DIR)
    try:
        from app import app
        with app.app_context():
            from config import Config
            from helpers_gmail import enviar_email_gmail
            dest = Config.MAIL_USERNAME
            enviar_email_gmail(dest, "⚠️ CyberShop — problema de salud detectado", report)
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        open(STATE, "w").write(str(now))
        print(f"(alerta enviada a {dest})")
    except Exception as e:  # noqa: BLE001
        print(f"(no se pudo enviar la alerta por email: {e})")


if __name__ == "__main__":
    main()
