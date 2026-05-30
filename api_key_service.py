"""Operaciones sobre sync_api_keys: emitir, listar, rotar, suspender.

Algoritmos copiados de CyberShop/app/tools/crear_sync_key.py para
preservar el mismo formato de api_key + client_code.
"""

import secrets

from crypto import sha256_hex
from db import control_plane_cursor


KEY_PREFIX = 'cyb_live_'
CLIENT_CODE_PREFIX = 'CYB'

# Alfabeto sin 0/O/1/I/L para evitar ambigüedad cuando el cliente lo tipea.
_CLIENT_CODE_ALPHABET = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'


def generate_api_key() -> str:
    """Devuelve 'cyb_live_<32 chars alfanuméricos>'."""
    raw = secrets.token_urlsafe(24).replace('-', '').replace('_', '')[:32]
    return KEY_PREFIX + raw


def generate_client_code() -> str:
    """Código corto memorable 'CYB-XXXXXXXX'."""
    chunk = ''.join(secrets.choice(_CLIENT_CODE_ALPHABET) for _ in range(8))
    return f'{CLIENT_CODE_PREFIX}-{chunk}'


def issue_key(tenant_id: int, label: str = '') -> dict:
    """Crea una API key nueva para un tenant.

    Returns: {'id', 'api_key', 'client_code', 'key_prefix'}
    ⚠️ api_key se devuelve UNA VEZ — solo el hash queda persistido.
    """
    last_exc = None
    for _ in range(5):
        api_key = generate_api_key()
        client_code = generate_client_code()
        try:
            with control_plane_cursor(dict_cursor=True) as cur:
                cur.execute(
                    """
                    INSERT INTO sync_api_keys
                        (tenant_id, key_hash, key_prefix, client_code, label, active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (
                        tenant_id,
                        sha256_hex(api_key),
                        api_key[:12],
                        client_code,
                        (label or '').strip() or None,
                    ),
                )
                row = cur.fetchone()
            return {
                'id':          row['id'],
                'api_key':     api_key,
                'client_code': client_code,
                'key_prefix':  api_key[:12],
            }
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).lower()
            if 'unique' in msg or 'duplicate' in msg:
                last_exc = exc
                continue
            raise

    raise RuntimeError(
        f'No se pudo generar un client_code único tras 5 intentos: {last_exc}'
    )


def list_keys(tenant_id: int) -> list:
    """Lista todas las keys de un tenant ordenadas por fecha desc."""
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            """
            SELECT id, key_prefix, client_code, label, active,
                   created_at, last_used_at
            FROM sync_api_keys
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            """,
            (tenant_id,)
        )
        return cur.fetchall()


def set_active(key_id: int, active: bool):
    """Activa o desactiva una key."""
    with control_plane_cursor() as cur:
        cur.execute(
            "UPDATE sync_api_keys SET active = %s WHERE id = %s",
            (active, key_id)
        )


def rotate(key_id: int) -> dict:
    """Desactiva la key vieja y crea una nueva para el mismo tenant.

    Returns el resultado de issue_key().
    """
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT tenant_id, label FROM sync_api_keys WHERE id = %s",
            (key_id,)
        )
        old = cur.fetchone()
        if not old:
            raise ValueError(f'Key {key_id} no existe')
        cur.execute(
            "UPDATE sync_api_keys SET active = FALSE WHERE id = %s",
            (key_id,)
        )

    label = (old['label'] or '') + ' (rotada)'
    return issue_key(old['tenant_id'], label=label.strip())
