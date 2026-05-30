"""Crea un usuario administrador del panel.

Uso interactivo:
    python tools/seed_admin.py --email tu@email.com --nombre "Tu Nombre"

(pide password con getpass para no quedar en historial de shell)

Uso no-interactivo (para scripts):
    python tools/seed_admin.py --email x@y.com --nombre X --password-stdin

Si el email ya existe, no hace nada (mensaje informativo).
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import control_plane_cursor
from auth import hash_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email', required=True, help='Email del admin (case-insensitive)')
    parser.add_argument('--nombre', required=True, help='Nombre legible')
    parser.add_argument('--password-stdin', action='store_true',
                        help='Lee la password de stdin en vez de pedirla interactivamente')
    parser.add_argument('--is-super', action='store_true',
                        help='Marca como super-admin (reservado, hoy no hace diferencia)')
    args = parser.parse_args()

    email = args.email.strip().lower()
    nombre = args.nombre.strip()

    if not email or '@' not in email:
        print('ERROR: email inválido', file=sys.stderr)
        sys.exit(1)

    # Validar que la tabla exista
    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'admin_users'
        """)
        if not cur.fetchone():
            print(
                "ERROR: tabla 'admin_users' no existe en saas_control_plane.\n"
                "Aplicá la migración primero:\n"
                "  python tools/apply_migrations.py",
                file=sys.stderr
            )
            sys.exit(1)

        cur.execute("SELECT id FROM admin_users WHERE email = %s", (email,))
        existing = cur.fetchone()

    if existing:
        print(f"El admin '{email}' ya existe (id={existing['id']}). Sin cambios.")
        return

    # Pedir password
    if args.password_stdin:
        password = sys.stdin.readline().rstrip('\n')
    else:
        password = getpass.getpass('Password: ')
        confirm = getpass.getpass('Confirmar password: ')
        if password != confirm:
            print('ERROR: las passwords no coinciden', file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print('ERROR: password debe tener al menos 8 caracteres', file=sys.stderr)
        sys.exit(1)

    pw_hash = hash_password(password)

    with control_plane_cursor(dict_cursor=True) as cur:
        cur.execute(
            """
            INSERT INTO admin_users (email, contraseña, nombre, is_super, active)
            VALUES (%s, %s, %s, %s, TRUE)
            RETURNING id
            """,
            (email, pw_hash, nombre, args.is_super)
        )
        new_id = cur.fetchone()['id']

    print()
    print('────────────────────────────────────────')
    print(f"  ID:       {new_id}")
    print(f"  Email:    {email}")
    print(f"  Nombre:   {nombre}")
    print(f"  Super:    {args.is_super}")
    print('────────────────────────────────────────')
    print()
    print('Admin creado. Login en http://localhost:5002/login')


if __name__ == '__main__':
    main()
