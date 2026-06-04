"""Rutas de login/logout."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from urllib.parse import urlparse

import auth


bp = Blueprint('auth', __name__)


def _safe_next(next_url):
    if not next_url or urlparse(next_url).netloc:
        return url_for('dashboard.index')
    return next_url


@bp.route('/login', methods=['GET', 'POST'])
def login():
    ip = request.remote_addr or 'unknown'
    use_pin = auth.pin_enabled()

    if request.method == 'POST':
        next_url = request.form.get('next') or request.args.get('next')
        if use_pin:
            if auth.pin_locked(ip):
                flash(f'Demasiados intentos. Espera ~{auth.pin_locked(ip) // 60 + 1} min.', 'warning')
            else:
                user = auth.authenticate_pin(request.form.get('pin', ''))
                if user:
                    auth._pin_clear(ip)
                    auth.login(user['id'])
                    return redirect(_safe_next(next_url))
                auth._pin_record_fail(ip)
                flash('PIN incorrecto.', 'error')
        else:
            user = auth.authenticate(request.form.get('email', ''), request.form.get('password', ''))
            if user:
                auth.login(user['id'])
                flash(f"Bienvenido, {user['nombre']}.", 'success')
                return redirect(_safe_next(next_url))
            flash('Email o contraseña inválidos.', 'error')

    return render_template(
        'login.html',
        next=request.args.get('next', ''),
        use_pin=use_pin,
        locked=auth.pin_locked(ip),
    )


@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    auth.logout()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))
