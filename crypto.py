"""Helpers criptográficos. Copia exacta de CyberShop/app/services/crypto_utils.py
para garantizar compatibilidad de los valores cifrados (mismo KMS_KEY)."""

import base64
import hashlib
import secrets

from config import Config


def sha256_hex(value: str) -> str:
    """SHA-256 hex. Usado para hash de api_keys y otros tokens."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _kms_key() -> bytes:
    raw = Config.KMS_KEY
    if not raw:
        raise RuntimeError(
            'KMS_KEY no configurada. Genera con:\n'
            '  python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"\n'
            'IMPORTANTE: usa el MISMO valor que CyberShop para que ambos servicios '
            'puedan descifrar tenant_databases.db_password_enc.'
        )
    return base64.b64decode(raw)


def aes_gcm_encrypt(plaintext: str) -> str:
    """Cifra con AES-256-GCM. Retorna base64(nonce || ciphertext)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    ct = AESGCM(_kms_key()).encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.b64encode(nonce + ct).decode('utf-8')


def aes_gcm_decrypt(ciphertext_b64: str) -> str:
    """Descifra un valor producido por aes_gcm_encrypt."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    data = base64.b64decode(ciphertext_b64)
    nonce, ct = data[:12], data[12:]
    return AESGCM(_kms_key()).decrypt(nonce, ct, None).decode('utf-8')
