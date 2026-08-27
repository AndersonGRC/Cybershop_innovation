#!/var/www/CyberShop/app/env/bin/python
"""Corre cybershop-health.sh y alerta por email (Gmail del operador) SOLO cuando
aparece un problema DURO NUEVO respecto a la última alerta (alert-on-change), para
no paginar cada 10 min por un problema ya conocido. Un problema persistente se
re-notifica pasadas REALERT_H horas. Pensado para cron.

Read-only salvo (a) el email de alerta y (b) el archivo de estado.
Los warnings (p.ej. demo con home 503) NO paginan."""
import os
import subprocess
import sys
import time

HEALTH = "/usr/local/sbin/cybershop-health.sh"
STATE = "/var/lib/cybershop/health_alert_state"   # líneas "✗ ..." de la última alerta
TS = "/var/lib/cybershop/health_alert_ts"          # epoch de la última alerta
REALERT_H = 12                                      # re-notifica un problema persistente cada 12h
APP_DIR = "/var/www/CyberShop/app"


def _bad_lines(report):
    return sorted(l.strip() for l in report.splitlines() if l.strip().startswith("✗"))


def _load(path):
    try:
        return open(path).read()
    except Exception:
        return ""


def _save(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)


def main():
    try:
        r = subprocess.run(["bash", HEALTH], capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        print(f"no se pudo ejecutar {HEALTH}: {e}")
        return
    report = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
    print(report)

    current = _bad_lines(report)
    if not current:
        _save(STATE, "")           # todo bien: limpia el estado
        return

    last = [l for l in _load(STATE).splitlines() if l.strip()]
    nuevos = [x for x in current if x not in last]
    try:
        last_ts = int(_load(TS).strip())
    except Exception:
        last_ts = 0
    persistente_reenvio = (time.time() - last_ts) > REALERT_H * 3600

    if not nuevos and not persistente_reenvio:
        _save(STATE, "\n".join(current))   # refresca estado (p.ej. si algo se resolvió)
        print("(sin problemas nuevos; no re-notifico)")
        return

    # Hay problema nuevo (o persistente > REALERT_H): alertar.
    sys.path.insert(0, APP_DIR)
    os.chdir(APP_DIR)
    try:
        from app import app
        with app.app_context():
            from config import Config
            from helpers_gmail import enviar_email_gmail
            dest = Config.MAIL_USERNAME
            enviar_email_gmail(dest, "⚠️ CyberShop — problema de salud detectado", report)
        _save(STATE, "\n".join(current))
        _save(TS, str(int(time.time())))
        print(f"(alerta enviada a {dest})")
    except Exception as e:  # noqa: BLE001
        print(f"(no se pudo enviar la alerta por email: {e})")


if __name__ == "__main__":
    main()
