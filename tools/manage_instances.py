"""Gestión en bloque de las instancias de clientes (Linux/prod).

Uso:
    python tools/manage_instances.py status     # estado de cada cybershop@<slug>
    python tools/manage_instances.py restart     # reinicia TODAS las instancias
    python tools/manage_instances.py restart --tenant <slug>

Tras un `git pull` del código compartido, `restart` aplica la actualización a
todos los clientes a la vez (mismo código, una instancia por cliente).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import control_plane_cursor  # noqa: E402

IS_LINUX = (os.name == 'posix')


def _slugs(only=None):
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT t.slug FROM tenants t
            JOIN tenant_runtime r ON r.tenant_id = t.id
            WHERE t.estado <> 'cancelado'
            ORDER BY t.slug
        """)
        slugs = [r['slug'] for r in cur.fetchall()]
    return [s for s in slugs if (not only or s == only)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['status', 'restart', 'stop', 'start'])
    ap.add_argument('--tenant', default=None)
    args = ap.parse_args()

    if not IS_LINUX:
        print("Solo aplica en el servidor Linux (systemd). En dev no hay instancias.")
        return

    slugs = _slugs(args.tenant)
    if not slugs:
        print("No hay instancias (tenant_runtime) que coincidan.")
        return

    for slug in slugs:
        unit = f"cybershop@{slug}"
        if args.action == 'status':
            r = subprocess.run(['systemctl', 'is-active', unit], capture_output=True, text=True)
            print(f"  {unit}: {r.stdout.strip() or r.stderr.strip()}")
        else:
            subprocess.run(['systemctl', args.action, unit])
            print(f"  {unit}: {args.action} OK")


if __name__ == '__main__':
    main()
