"""Aplica las migraciones aditivas (migrations/tenant/*.sql) a las BDs de los
clientes existentes. Seguro de re-correr (idempotente).

Uso:
    python tools/migrate_tenants.py                 # aplica a todos
    python tools/migrate_tenants.py --dry-run       # solo muestra pendientes
    python tools/migrate_tenants.py --tenant <slug> # solo un cliente
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tenant_migrations as tm  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true', help='No aplica, solo lista pendientes.')
    ap.add_argument('--tenant', default=None, help='Slug de un cliente específico.')
    args = ap.parse_args()

    files = [f.name for f in tm._files()]
    print(f"Migraciones de tenant disponibles: {len(files)}")
    for f in files:
        print(f"  - {f}")
    print()

    results = tm.migrate_all(dry_run=args.dry_run, only_slug=args.tenant)
    if not results:
        print("No hay tenants con BD viva (o el slug no existe).")
        return

    verbo = 'pendientes' if args.dry_run else 'aplicadas'
    for slug, applied in results.items():
        if isinstance(applied, str):  # error
            print(f"  [{slug}] {applied}")
        elif applied:
            print(f"  [{slug}] {len(applied)} {verbo}: {', '.join(applied)}")
        else:
            print(f"  [{slug}] al día (nada que aplicar)")

    print("\n[OK] Proceso terminado.")


if __name__ == '__main__':
    main()
