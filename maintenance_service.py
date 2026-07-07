"""
maintenance_service.py — Respaldo on-demand y salud de la instancia del cliente.

Para el panel fADMIN: permite respaldar+descargar la BD de un cliente y ver su
estado de salud (proceso systemd + app/BD vía /api/v1/health) sin entrar al
servidor. No amplía privilegios: pg_dump conecta con password (sin sudo) y la
salud es una consulta HTTP local + `systemctl is-active` (no privilegiado).
"""
import gzip
import json
import os
import shutil
import urllib.request

import lifecycle_service
import tenant_service
import provisioning_service as prov


def backup_now(tenant_id):
    """pg_dump comprimido (.sql.gz) de la BD del cliente. Devuelve la ruta."""
    t = tenant_service.get_tenant(tenant_id)
    if not t or not t.get('db_name'):
        raise RuntimeError('El cliente no tiene base de datos asignada.')
    sql_path = lifecycle_service.backup_db(t['slug'], t['db_name'])   # /var/backups/cybershop/<slug>-<ts>.sql
    gz_path = sql_path + '.gz'
    try:
        with open(sql_path, 'rb') as fi, gzip.open(gz_path, 'wb') as fo:
            shutil.copyfileobj(fi, fo)
    finally:
        try:
            os.remove(sql_path)   # dejamos solo el comprimido
        except OSError:
            pass
    return gz_path


def tenant_health(tenant_id, timeout=1.2):
    """Salud combinada: proceso (systemd) + app/BD (HTTP /api/v1/health).

    Devuelve dict robusto (nunca lanza): {service_active, http_ok, status, db,
    redis, detail}. Si el HTTP no responde o la API no está habilitada, http_ok
    queda en False pero service_active sigue reflejando el proceso.
    """
    result = {'service_active': False, 'http_ok': False, 'status': None,
              'db': None, 'redis': None, 'detail': None}
    t = tenant_service.get_tenant(tenant_id)
    if not t:
        return result
    try:
        result['service_active'] = bool(prov.service_is_active(t['slug']))
    except Exception:
        pass
    try:
        rt = prov.get_runtime(tenant_id) or {}
        port = rt.get('port')
        if port:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/health', timeout=timeout) as r:
                data = json.loads(r.read().decode('utf-8'))
                result['status'] = data.get('status')
                result['db'] = data.get('db')
                result['redis'] = data.get('redis')
                result['http_ok'] = data.get('status') in ('ok', 'degraded')
        else:
            result['detail'] = 'sin puerto asignado'
    except Exception as e:
        result['detail'] = str(e)[:80]
    return result
