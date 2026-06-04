"""Genera el schema base de los tenants nuevos a partir de la DB maestra.

Hace `pg_dump --schema-only` de la DB maestra (cybershop) y lo escribe en
`schema/tenant_schema.sql`. Ese archivo es el que `tenant_service.create_tenant`
aplica a cada `cyber_tNNN` nuevo — así cada cliente arranca con la ESTRUCTURA
más reciente del maestro (sin datos).

Correr cada vez que cambie el schema del maestro:
    python tools/refresh_tenant_schema.py
"""

import os
import subprocess
import sys
from pathlib import Path

# Permitir importar config desde la raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import Config  # noqa: E402


def _pg_dump_bin() -> str:
    """Deriva la ruta de pg_dump a partir de PSQL_BIN (mismo directorio)."""
    psql = Config.PSQL_BIN
    p = Path(psql)
    if p.name.lower().startswith('psql'):
        candidate = p.with_name(p.name.lower().replace('psql', 'pg_dump'))
        if candidate.exists():
            return str(candidate)
    # Fallback: confiar en PATH
    return 'pg_dump'


def refresh() -> Path:
    out = Path(Config.TENANT_SCHEMA_FILE)
    out.parent.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        'PGPASSWORD': Config.PG_PASSWORD,
        'PGHOST': Config.PG_HOST,
        'PGPORT': str(Config.PG_PORT),
        'PGUSER': Config.PG_USER,
    }
    cmd = [
        _pg_dump_bin(),
        '--schema-only',
        '--no-owner',
        '--no-privileges',
        '--no-comments',
        '-d', Config.MASTER_DB_NAME,
        '-f', str(out),
    ]
    print(f"pg_dump {Config.MASTER_DB_NAME} (schema-only) -> {out}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print('ERROR pg_dump:\n' + result.stderr, file=sys.stderr)
        sys.exit(1)

    size = out.stat().st_size
    tables = out.read_text(encoding='utf-8', errors='replace').count('CREATE TABLE')
    print(f"OK Schema generado: {size:,} bytes, {tables} tablas.")
    return out


if __name__ == '__main__':
    refresh()
