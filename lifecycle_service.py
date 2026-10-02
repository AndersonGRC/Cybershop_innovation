"""Ciclo de vida del cliente: suspender, reactivar, destruir.

- Suspender = bloquear ingreso apagando la instancia (systemctl stop) + estado
  'suspendido' (desactiva keys). NO toca CyberShop/app.
- Destroy soft (default) = backup (pg_dump) + apagar + quitar Caddy + estado
  'cancelado'. CONSERVA la BD (reversible).
- Destroy hard (explícito) = lo anterior + DROP DATABASE + borrar el env.
- En ambos se cierra su compra en el motor de cobro (no más recordatorios ni
  links de pago para una tienda apagada); hard además borra su carpeta de
  personalizaciones y libera su puerto.
- Las copias de respaldo de pruebas gratis eliminadas que nunca pagaron se
  borran a los 30 días (purgar_backups_pruebas).
"""

import datetime
import os
import re
import shutil
import subprocess
from pathlib import Path

import psycopg2.sql as sql

from config import Config
from db import get_postgres_admin_conn
import tenant_service
import provisioning_service as prov
import integrations_service as ints
import audit_service


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


def suspend(tenant_id: int, actor=None):
    t = tenant_service.get_tenant(tenant_id)
    tenant_service.set_estado(tenant_id, 'suspendido')   # desactiva keys
    prov.stop_service(t['slug'])
    prov.set_status(tenant_id, 'stopped')
    audit_service.registrar('suspend', tenant_id, actor=actor, detalle=f"slug={t.get('slug')}")


def reactivate(tenant_id: int, actor=None):
    t = tenant_service.get_tenant(tenant_id)
    tenant_service.set_estado(tenant_id, 'activo')
    prov.enable_service(t['slug'])
    prov.set_status(tenant_id, 'running' if prov.IS_LINUX else 'pending')
    _motor(lambda: _billing().reabrir_compra_motor(tenant_id))
    audit_service.registrar('reactivate', tenant_id, actor=actor, detalle=f"slug={t.get('slug')}")


def _teardown_runtime(tenant_id, slug):
    """Apaga la instancia y quita el bloque Caddy (sin tocar la BD)."""
    prov.stop_service(slug)
    rt = prov.get_runtime(tenant_id)
    if rt and rt.get('subdomain'):
        prov.remove_site(prov.domain_for(rt['subdomain']))
    if rt and rt.get('custom_domain'):
        prov.remove_site(rt['custom_domain'])


def destroy_soft(tenant_id: int, actor=None) -> str:
    """Backup + apagar + quitar Caddy + estado cancelado. CONSERVA la BD."""
    t = tenant_service.get_tenant(tenant_id)
    backup_path = backup_db(t['slug'], t['db_name'])
    _teardown_runtime(tenant_id, t['slug'])
    tenant_service.set_estado(tenant_id, 'cancelado')
    prov.set_status(tenant_id, 'cancelled')
    _motor(lambda: _billing().cerrar_compra_motor(tenant_id, 'CANCELADA'))
    audit_service.registrar('destroy_soft', tenant_id, actor=actor,
                            detalle=f"slug={t.get('slug')} backup={backup_path}")
    return backup_path


def destroy_hard(tenant_id: int, actor=None) -> str:
    """destroy_soft + DROP DATABASE + borrar el env de la instancia."""
    t = tenant_service.get_tenant(tenant_id)
    backup_path = destroy_soft(tenant_id, actor=actor)
    destroy_database(t['db_name'])
    env_file = ints.env_path(t['slug'])
    if env_file.exists():
        env_file.unlink()
    _motor(lambda: _billing().cerrar_compra_motor(tenant_id, 'ELIMINADA'))
    _borrar_restos(tenant_id, t['slug'])
    audit_service.registrar('destroy_hard', tenant_id, actor=actor,
                            detalle=f"slug={t.get('slug')} db={t.get('db_name')} DROP+env borrado")
    return backup_path


# ── Ayudantes de limpieza ──────────────────────────────────────
def _billing():
    import billing_service
    return billing_service


def _motor(accion):
    """El motor de cobro vive en otra BD: si falla, la destrucción ya hecha no
    se revierte; queda registrado en la auditoría para revisarlo a mano."""
    try:
        return accion()
    except Exception as exc:  # noqa: BLE001
        audit_service.registrar('motor_cobro_error', detalle=str(exc)[:300])
        return None


def _borrar_restos(tenant_id, slug):
    """Tras un DROP: carpeta de personalizaciones de la tienda y su puerto.
    El nombre (slug) y la fila del cliente se conservan como historial."""
    raiz = Path(prov.OVERRIDES_ROOT).resolve()
    carpeta = (raiz / slug)
    try:
        if carpeta.exists() and not carpeta.is_symlink() and carpeta.resolve().parent == raiz:
            shutil.rmtree(carpeta)
    except Exception as exc:  # noqa: BLE001
        audit_service.registrar('limpieza_error', tenant_id, detalle=f'overrides: {exc}'[:300])
    try:
        from db import control_plane_cursor
        with control_plane_cursor() as cur:
            cur.execute("UPDATE tenant_runtime SET port = NULL WHERE tenant_id = %s", (tenant_id,))
    except Exception as exc:  # noqa: BLE001
        audit_service.registrar('limpieza_error', tenant_id, detalle=f'puerto: {exc}'[:300])


RETENCION_BACKUPS_PRUEBAS_DIAS = 30


def _patron_backup(slug):
    # Exacto: «tienda-20261001_120000.sql» no confunde a «tienda» con «tienda-roma».
    return re.compile(rf'^{re.escape(slug)}-\d{{8}}_\d{{6}}\.sql(\.gz)?$')


def backups_pruebas_vencidos(dias=RETENCION_BACKUPS_PRUEBAS_DIAS):
    """Copias de respaldo de pruebas gratis ELIMINADAS que nunca pagaron, con más
    de `dias` días. Los respaldos de clientes que pagaron nunca entran aquí."""
    carpeta = Path(Config.BACKUP_DIR)
    if not carpeta.is_dir():
        return []
    from db import control_plane_cursor
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT id, slug FROM tenants WHERE estado = 'cancelado'")
        cancelados = cur.fetchall()
    limite = datetime.datetime.now().timestamp() - dias * 86400
    salida = []
    for t in cancelados:
        if not _billing().es_prueba_sin_pagar(t['id']):
            continue
        patron = _patron_backup(t['slug'])
        for archivo in carpeta.iterdir():
            if archivo.is_file() and patron.match(archivo.name) and archivo.stat().st_mtime < limite:
                salida.append({'tenant_id': t['id'], 'slug': t['slug'], 'ruta': archivo,
                               'bytes': archivo.stat().st_size})
    return salida


def purgar_backups_pruebas(dias=RETENCION_BACKUPS_PRUEBAS_DIAS, actor=None):
    """Borra esas copias. Devuelve (archivos, bytes liberados)."""
    borrados, total = 0, 0
    for b in backups_pruebas_vencidos(dias):
        try:
            b['ruta'].unlink()
            borrados += 1
            total += b['bytes']
            audit_service.registrar('backup_prueba_purgado', b['tenant_id'], actor=actor,
                                    detalle=f"{b['ruta'].name} ({b['bytes']} bytes, >{dias} días)")
        except Exception:  # noqa: BLE001
            continue
    return borrados, total
