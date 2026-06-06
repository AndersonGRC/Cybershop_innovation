"""Reverse proxy por cliente: cuadra el DOMINIO con el PUERTO abierto.

Cada cliente corre en `127.0.0.1:<puerto>`. Este módulo genera el bloque del
reverse proxy (nginx por defecto, o Caddy) que enruta el dominio del cliente a
ese puerto, lo escribe, valida y recarga el proxy. En Windows (dev) solo
devuelve el bloque para previsualizar (no escribe ni recarga).

SEGURIDAD: el dominio se valida estrictamente antes de escribirlo en la config
del proxy (evita inyección en el archivo de nginx).
"""

import os
import re
import subprocess
from pathlib import Path

from config import Config


IS_LINUX = (os.name == 'posix')
# En el servidor el maestro corre como www-data: systemctl/nginx van con sudo
# (reglas NOPASSWD acotadas en /etc/sudoers.d/cybershop-admin).
SUDO = ['sudo'] if IS_LINUX else []

_SUBDOMAIN_RE = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$')
_DOMAIN_RE = re.compile(r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$')


class DomainError(ValueError):
    """Dominio/subdominio inválido."""


def validate_subdomain(sub: str) -> str:
    sub = (sub or '').strip().lower()
    if not _SUBDOMAIN_RE.match(sub):
        raise DomainError("Subdominio inválido: usa minúsculas, números y guiones (ej. 'mi-tienda').")
    return sub


def validate_domain(dom: str) -> str:
    dom = (dom or '').strip().lower().rstrip('.')
    if not _DOMAIN_RE.match(dom):
        raise DomainError(f"Dominio inválido: '{dom}'. Usa algo como 'sutienda.com'.")
    return dom


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


# ── nginx ──────────────────────────────────────────────────────
def _nginx_proxy_location(port: int) -> str:
    return (
        "    location / {\n"
        f"        proxy_pass http://127.0.0.1:{port};\n"
        "        proxy_set_header Host $host;\n"
        "        proxy_set_header X-Real-IP $remote_addr;\n"
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        "        proxy_set_header X-Forwarded-Proto $scheme;\n"
        "        proxy_redirect off;\n"
        "        proxy_read_timeout 120s;\n"
        "    }\n"
    )


def nginx_block(domain: str, port: int, use_wildcard: bool = False) -> str:
    """Bloque server de nginx que enruta `domain` -> 127.0.0.1:`port`."""
    cert, key = Config.WILDCARD_SSL_CERT, Config.WILDCARD_SSL_KEY
    loc = _nginx_proxy_location(port)
    if use_wildcard and cert and key:
        return (
            f"# {domain} -> 127.0.0.1:{port}  (CyberShop, generado por el maestro)\n"
            "server {\n    listen 80;\n"
            f"    server_name {domain};\n"
            "    location /.well-known/acme-challenge/ { root /var/www/html; }\n"
            "    location / { return 301 https://$server_name$request_uri; }\n}\n"
            "server {\n    listen 443 ssl http2;\n"
            f"    server_name {domain};\n"
            f"    ssl_certificate {cert};\n    ssl_certificate_key {key};\n"
            f"{loc}"
            "    client_max_body_size 25M;\n}\n"
        )
    # HTTP (TLS se agrega con certbot por dominio, o luego)
    return (
        f"# {domain} -> 127.0.0.1:{port}  (CyberShop, generado por el maestro)\n"
        "server {\n    listen 80;\n"
        f"    server_name {domain};\n"
        "    location /.well-known/acme-challenge/ { root /var/www/html; }\n"
        f"{loc}"
        "    client_max_body_size 25M;\n}\n"
    )


def _write_nginx(domain: str, port: int, use_wildcard: bool) -> str:
    block = nginx_block(domain, port, use_wildcard)
    if not IS_LINUX:
        return block
    avail = Path(Config.NGINX_SITES_AVAILABLE) / f"{domain}.conf"
    avail.parent.mkdir(parents=True, exist_ok=True)
    avail.write_text(block, encoding='utf-8')
    # Modelo sites-available/sites-enabled: symlink solo si son carpetas distintas.
    # Si AVAILABLE == ENABLED (carpeta de include dedicada), no hay symlink.
    if Path(Config.NGINX_SITES_AVAILABLE).resolve() != Path(Config.NGINX_SITES_ENABLED).resolve():
        enabled = Path(Config.NGINX_SITES_ENABLED) / f"{domain}.conf"
        if not enabled.exists():
            try:
                enabled.symlink_to(avail)
            except Exception:
                pass
    test = _run(SUDO + ['nginx', '-t'])
    if test.returncode == 0:
        _run(SUDO + ['systemctl', 'reload', 'nginx'])
    return block


def _remove_nginx(domain: str):
    if not IS_LINUX:
        return
    for d in {Config.NGINX_SITES_AVAILABLE, Config.NGINX_SITES_ENABLED}:
        f = Path(d) / f"{domain}.conf"
        if f.exists() or f.is_symlink():
            try:
                f.unlink()
            except Exception:
                pass
    _run(SUDO + ['systemctl', 'reload', 'nginx'])


# ── caddy ──────────────────────────────────────────────────────
def caddy_block(domain: str, port: int) -> str:
    return (f"# {domain} -> 127.0.0.1:{port}\n"
            f"{domain} {{\n    reverse_proxy 127.0.0.1:{port}\n}}\n")


def _write_caddy(domain: str, port: int) -> str:
    block = caddy_block(domain, port)
    if not IS_LINUX:
        return block
    sites = Path(Config.CADDY_SITES_DIR)
    sites.mkdir(parents=True, exist_ok=True)
    (sites / f"{domain}.caddy").write_text(block, encoding='utf-8')
    _run(['systemctl', 'reload', 'caddy'])
    return block


def _remove_caddy(domain: str):
    if not IS_LINUX:
        return
    f = Path(Config.CADDY_SITES_DIR) / f"{domain}.caddy"
    if f.exists():
        try:
            f.unlink()
        except Exception:
            pass
    _run(['systemctl', 'reload', 'caddy'])


# ── Dispatcher (según PROXY_BACKEND) ───────────────────────────
def write_site(domain: str, port: int, is_subdomain: bool = True) -> str:
    if Config.PROXY_BACKEND == 'caddy':
        return _write_caddy(domain, port)
    return _write_nginx(domain, port, use_wildcard=is_subdomain)


def remove_site(domain: str):
    if Config.PROXY_BACKEND == 'caddy':
        return _remove_caddy(domain)
    return _remove_nginx(domain)


def preview_block(domain: str, port: int, is_subdomain: bool = True) -> str:
    """Bloque de config SIN escribir (para mostrar en la UI)."""
    if Config.PROXY_BACKEND == 'caddy':
        return caddy_block(domain, port)
    return nginx_block(domain, port, use_wildcard=is_subdomain)
