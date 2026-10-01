"""Modo prueba (prueba gratis de 15 días): integraciones externas apagadas.

Cada instancia hereda el `.cybershop.conf` compartido (las llaves de CyberShop)
y solo sobrescribe lo que tenga en su EnvironmentFile (<slug>.env). La app
carga el .conf sin pisar variables ya definidas, así que una llave VACÍA en el
EnvironmentFile apaga esa integración en esa tienda; la app ya oculta cada
pieza sin credenciales (`integraciones` en app.py).

En una prueba se apagan las conexiones con otras aplicaciones que exigen llaves
que el cliente no tiene (decisión del dueño): pasarela de pagos, inicio con
Google, píxel de Meta, facturación electrónica DIAN y los datos de cobro del
operador. Correo e IA se mantienen (decisión del dueño).

- Nunca pisa un valor que el operador ya haya configurado para ese cliente.
- Al convertir la prueba en plan pagado se quitan SOLO las llaves que siguen
  vacías: la tienda vuelve a heredar lo compartido o lo que se le configure.
- No toca create_tenant ni el seed: se aplica después, sobre una tienda ya creada.
"""

import integrations_service as ints

MARCA = 'CYBERSHOP_MODO_PRUEBA'

LLAVES_APAGADAS = (
    # Pasarela de pagos: los pagos de sus clientes no pueden ir a la cuenta de CyberShop.
    'PAYU_MERCHANT_ID', 'PAYU_ACCOUNT_ID', 'PAYU_API_LOGIN', 'PAYU_API_KEY',
    # Inicio de sesión y calendario con Google (OAuth del operador).
    'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI', 'GOOGLE_LOGIN_REDIRECT_URI',
    # Píxel y API de conversiones de Meta (por defecto, el píxel de CyberShop).
    'META_PIXEL_ID', 'META_CAPI_ACCESS_TOKEN', 'META_CAPI_TEST_EVENT_CODE',
    # Facturación electrónica DIAN (microservicio con credenciales por emisor).
    'DIAN_SERVICE_URL', 'DIAN_API_KEY', 'DIAN_MASTER_KEY', 'DIAN_UI_URL',
    # Datos del emisor de cuentas de cobro (identidad del operador).
    'BILLING_ID', 'BILLING_NOMBRE', 'BILLING_EMAIL', 'BILLING_TELEFONO', 'BILLING_TEXTO_PAGO',
)


def esta_activo(slug: str) -> bool:
    return ints.read_env(slug).get(MARCA) == '1'


def aplicar(slug: str) -> list:
    """Apaga las integraciones en el EnvironmentFile. Devuelve las llaves que
    quedaron vacías por este cambio (las ya configuradas se respetan)."""
    env = ints.read_env(slug)
    apagadas = []
    for llave in LLAVES_APAGADAS:
        if not env.get(llave):
            env[llave] = ''
            apagadas.append(llave)
    env[MARCA] = '1'
    ints._write_env(slug, env)
    return apagadas


def quitar(slug: str) -> list:
    """Fin de la prueba (plan pagado): borra las llaves que siguen vacías y la
    marca. Devuelve las llaves que se quitaron."""
    env = ints.read_env(slug)
    if env.get(MARCA) != '1':
        return []
    quitadas = [llave for llave in LLAVES_APAGADAS if llave in env and env[llave] == '']
    for llave in quitadas:
        env.pop(llave)
    env.pop(MARCA, None)
    ints._write_env(slug, env)
    return quitadas
