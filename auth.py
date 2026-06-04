"""Autenticación de admin users."""

import hmac
import time
from functools import wraps

from flask import session, redirect, url_for, request, flash, g
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db import control_plane_cursor


SESSION_KEY = 'admin_id'

# Rate limiting simple del PIN (por IP, en memoria). El allow-list de IP del
# proxy es la barrera real en producción; esto frena fuerza bruta básica.
_PIN_MAX_FAILS = 5
_PIN_LOCK_SECONDS = 600  # 10 min
_pin_fails = {}  # ip -> [fails, lock_until_ts]


def pin_locked(ip: str) -> int:
    """Segundos restantes de bloqueo para esa IP (0 si no está bloqueada)."""
    rec = _pin_fails.get(ip)
    if rec and rec[1] > time.time():
        return int(rec[1] - time.time())
    return 0


def _pin_record_fail(ip: str):
    rec = _pin_fails.get(ip, [0, 0])
    rec[0] += 1
    if rec[0] >= _PIN_MAX_FAILS:
        rec[1] = time.time() + _PIN_LOCK_SECONDS
        rec[0] = 0
    _pin_fails[ip] = rec


def _pin_clear(ip: str):
    _pin_fails.pop(ip, None)


def pin_enabled() -> bool:
    return bool((Config.MASTER_PIN or '').strip())


def authenticate_pin(pin: str):
    """Valida el PIN contra Config.MASTER_PIN (comparación constante) y devuelve
    el admin super (o el primero activo). None si no coincide o no hay PIN."""
    configured = (Config.MASTER_PIN or '').strip()
    if not configured:
        return None
    if not pin or not hmac.compare_digest(str(pin).strip(), configured):
        return None
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT id, email, nombre, is_super FROM admin_users "
            "WHERE active = TRUE ORDER BY is_super DESC, id ASC LIMIT 1"
        )
        return cur.fetchone()


def login_required(fn):
    """Bloquea acceso a rutas no logueadas. Redirige a /login con `next` set."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get(SESSION_KEY):
            flash('Inicia sesión para continuar.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def current_admin():
    """Carga datos del admin de la sesión. Cachea en g para evitar query repetida."""
    if hasattr(g, '_current_admin'):
        return g._current_admin

    aid = session.get(SESSION_KEY)
    if not aid:
        g._current_admin = None
        return None

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT id, email, nombre, is_super FROM admin_users "
            "WHERE id=%s AND active=TRUE",
            (aid,)
        )
        admin = cur.fetchone()
    g._current_admin = admin
    return admin


def authenticate(email: str, password: str):
    """Valida credenciales contra admin_users.

    Returns admin dict si ok, None si no.
    Actualiza last_login_at en éxito.
    """
    if not email or not password:
        return None

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            "SELECT id, email, contraseña, nombre, is_super "
            "FROM admin_users WHERE email=%s AND active=TRUE",
            (email.strip().lower(),)
        )
        user = cur.fetchone()

        if not user or not check_password_hash(user['contraseña'], password):
            return None

        cur.execute(
            "UPDATE admin_users SET last_login_at = NOW() WHERE id = %s",
            (user['id'],)
        )

    return {
        'id':       user['id'],
        'email':    user['email'],
        'nombre':   user['nombre'],
        'is_super': user['is_super'],
    }


def login(admin_id: int):
    """Establece la sesión del admin."""
    session.clear()
    session[SESSION_KEY] = admin_id
    session.permanent = True


def logout():
    """Cierra sesión."""
    session.clear()


def hash_password(plain: str) -> str:
    """Hash de password con werkzeug (pbkdf2 sha256). Mismo formato que CyberShop."""
    return generate_password_hash(plain)
