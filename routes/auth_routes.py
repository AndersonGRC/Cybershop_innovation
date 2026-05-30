"""Rutas de login/logout."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from urllib.parse import urlparse

import auth


bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user = auth.authenticate(email, password)
        if user:
            auth.login(user['id'])
            flash(f"Bienvenido, {user['nombre']}.", 'success')
            next_url = request.form.get('next') or request.args.get('next') or url_for('dashboard.index')
            # Solo permitir redirect a paths relativos (anti open-redirect)
            if urlparse(next_url).netloc:
                next_url = url_for('dashboard.index')
            return redirect(next_url)
        flash('Email o contraseña inválidos.', 'error')

    return render_template(
        'login.html',
        next=request.args.get('next', ''),
    )


@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    auth.logout()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))
