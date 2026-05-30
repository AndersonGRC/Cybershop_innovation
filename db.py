"""Acceso a Postgres: control plane + tenant DBs.

Diseñado para reusar exactamente los mismos patrones que
CyberShop/app/services/db_layer.py — así las migraciones y el formato
de credenciales cifradas son 100% compatibles entre ambos servicios.
"""

from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor

from config import Config


# ──────────────────────────────────────────────
# Control plane (saas_control_plane)
# ──────────────────────────────────────────────

def get_control_plane_conn():
    """Conexión directa a saas_control_plane."""
    return psycopg2.connect(
        dbname=Config.CP_DB_NAME,
        host=Config.CP_DB_HOST,
        port=Config.CP_DB_PORT,
        user=Config.CP_DB_USER,
        password=Config.CP_DB_PASSWORD,
    )


@contextmanager
def control_plane_cursor(dict_cursor=True):
    """Context manager con commit/rollback automáticos."""
    conn = get_control_plane_conn()
    factory = DictCursor if dict_cursor else None
    cur = conn.cursor(cursor_factory=factory)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# Tenant DBs (cyber_tNNN)
# ──────────────────────────────────────────────

def get_postgres_admin_conn(autocommit=False):
    """Conexión al servidor Postgres con privilegios para CREATE DATABASE.

    Apunta a la DB 'postgres' (default mantenance DB). Con autocommit=True
    porque CREATE DATABASE no puede ejecutarse dentro de una transacción.
    """
    conn = psycopg2.connect(
        dbname='postgres',
        host=Config.PG_HOST,
        port=Config.PG_PORT,
        user=Config.PG_USER,
        password=Config.PG_PASSWORD,
    )
    if autocommit:
        conn.set_session(autocommit=True)
    return conn


def get_tenant_conn(db_name):
    """Conexión a la DB de un tenant específico."""
    return psycopg2.connect(
        dbname=db_name,
        host=Config.PG_HOST,
        port=Config.PG_PORT,
        user=Config.PG_USER,
        password=Config.PG_PASSWORD,
    )
