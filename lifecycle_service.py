"""Ciclo de vida del cliente: suspender, reactivar, destruir.

- Suspender = bloquear ingreso apagando la instancia (systemctl stop) + estado
  'suspendido' (desactiva keys). NO toca CyberShop/app.
- Destroy soft (default) = backup (pg_dump) + apagar + quitar Caddy + estado
  'cancelado'. CONSERVA la BD (reversible).
- Destroy hard (explícito) = lo anterior + DROP DATABASE + borrar el env.
"""

import datetime
import os
import subprocess
from pathlib import Path

import psycopg2.sql as sql

from config import Config
from db import get_postgres_admin_conn
import tenant_service
import provisioning_service as prov
import integrations_service as ints


def _pg_dump_bin() -> str:
    p = Path(Config.PSQL_BIN)
    if p.name.lower().startswith('psql'):
        cand = p.with_name(p.name.lower().replace('psql', 'pg_dump'))
        if cand.exists():
            return str(cand)
    return 'pg_dump'


def backup_db(slug: str, db_name: str) -> str:
    """pg_dump de la BD del cliente a BACKUP_DIR/<slug>-<ts>.sql. Devuelve la ruta."""
    out_dir = Path(Config.BACKUP_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out = out_dir / f"{slug}-{ts}.sql"
    env = {
        **os.environ,
        'PGPASSWORD': Config.PG_PASSWORD, 'PGHOST': Config.PG_HOST,
        'PGPORT': str(Config.PG_PORT), 'PGUSER': Config.PG_USER,
    }
    res = subprocess.run([_pg_dump_bin(), '-d', db_name, '-f', str(out)],
                         env=env, capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        raise RuntimeError(f"pg_dump falló: {res.stderr}")
    return str(out)


def destroy_database(db_name: str):
    """Termina conexiones y DROP DATABASE (irreversible)."""
    conn = get_postgres_admin_conn(autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (db_name,),
            )
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
    finally:
        conn.close()


def suspend(tenant_id: int):
    t = tenant_service.get_tenant(tenant_id)
    tenant_service.set_estado(tenant_id, 'suspendido')   # desactiva keys
    prov.stop_service(t['slug'])
    prov.set_status(tenant_id, 'stopped')


def reactivate(tenant_id: int):
    t = tenant_service.get_tenant(tenant_id)
    tenant_service.set_estado(tenant_id, 'activo')
    prov.enable_service(t['slug'])
    prov.set_status(tenant_id, 'running' if prov.IS_LINUX else 'pending')


def _teardown_runtime(tenant_id, slug):
    """Apaga la instancia y quita el bloque Caddy (sin tocar la BD)."""
    prov.stop_service(slug)
    rt = prov.get_runtime(tenant_id)
    if rt and rt.get('subdomain'):
        prov.remove_site(prov.domain_for(rt['subdomain']))
    if rt and rt.get('custom_domain'):
        prov.remove_site(rt['custom_domain'])


def destroy_soft(tenant_id: int) -> str:
    """Backup + apagar + quitar Caddy + estado cancelado. CONSERVA la BD."""
    t = tenant_service.get_tenant(tenant_id)
    backup_path = backup_db(t['slug'], t['db_name'])
    _teardown_runtime(tenant_id, t['slug'])
    tenant_service.set_estado(tenant_id, 'cancelado')
    prov.set_status(tenant_id, 'cancelled')
    return backup_path


def destroy_hard(tenant_id: int) -> str:
    """destroy_soft + DROP DATABASE + borrar el env de la instancia."""
    t = tenant_service.get_tenant(tenant_id)
    backup_path = destroy_soft(tenant_id)
    destroy_database(t['db_name'])
    env_file = ints.env_path(t['slug'])
    if env_file.exists():
        env_file.unlink()
    return backup_path
