"""Suspende tenants con +60 días de mora (auto_suspender=TRUE). Para el cron diario.

Uso:
    python tools/revisar_morosos.py            # ejecuta
    python tools/revisar_morosos.py --dry-run  # solo lista, no suspende
"""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import billing_service


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pendientes = billing_service.morosos()
    if not pendientes:
        print(f"[{ts}] Sin morosos elegibles (+{billing_service.MORA_DIAS_SUSPENSION}d).")
        return

    print(f"[{ts}] Morosos elegibles: {len(pendientes)}")
    for m in pendientes:
        print(f"  - tenant {m['id']} ({m['slug']}) vencido {m['dias_mora']}d (desde {m['proxima_fecha']})")

    if args.dry_run:
        print(f"[{ts}] [DRY RUN] no se suspende nada.")
        return

    suspendidos = billing_service.revisar_y_suspender(por='cron')
    print(f"[{ts}] Suspendidos: {len(suspendidos)} -> "
          + ", ".join(f"{m['slug']}(#{m['id']})" for m in suspendidos))


if __name__ == '__main__':
    main()
