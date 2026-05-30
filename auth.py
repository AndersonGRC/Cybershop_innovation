"""Autenticación de admin users."""

from functools import wraps

from flask import session, redirect, url_for, request, flash, g
from werkzeug.security import check_password_hash, generate_password_hash

from db import control_plane_cursor


SESSION_KEY = 'admin_id'


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
