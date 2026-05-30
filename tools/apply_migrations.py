"""Aplica los archivos .sql de migrations/ a saas_control_plane.

Uso:
    python tools/apply_migrations.py
    python tools/apply_migrations.py --dry-run

Es idempotente: los CREATE TABLE usan IF NOT EXISTS.
"""

import argparse
import sys
from pathlib import Path

# Asegurar que el root del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_control_plane_conn


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar qué archivos correría sin ejecutarlos.')
    args = parser.parse_args()

    migrations_dir = Path(__file__).parent.parent / 'migrations'
    if not migrations_dir.is_dir():
        print(f"ERROR: no existe {migrations_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(migrations_dir.glob('*.sql'))
    if not files:
        print(f"No hay archivos .sql en {migrations_dir}")
        return

    print(f"Encontrados {len(files)} archivo(s):")
    for f in files:
        print(f"  - {f.name}")
    print()

    if args.dry_run:
        print("[DRY RUN] No se aplica nada.")
        return

    conn = get_control_plane_conn()
    try:
        for f in files:
            print(f"Aplicando {f.name}...", end=' ', flush=True)
            sql = f.read_text(encoding='utf-8')
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print("OK")
    except Exception as exc:
        conn.rollback()
        print(f"\nERROR aplicando {f.name}: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print("\n[COMPLETADO] Todas las migrations aplicadas.")


if __name__ == '__main__':
    main()
