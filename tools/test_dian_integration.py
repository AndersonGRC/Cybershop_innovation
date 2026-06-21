"""Prueba local de la integración con FacturacionDIAN sin tocar producción.

Levanta un mock del microservicio (en un puerto efímero), apunta dian_service
a él y ejercita: calcular_dv, provision (escribe env), validate (cadena),
y el caso 409 (NIT duplicado).

Uso: python tools\\test_dian_integration.py
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MASTER = 'master-key-de-prueba'
TENANT_KEY = 'a' * 64
NITS_REGISTRADOS = set()


class MockDian(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencio
        pass

    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            return self._json(200, {'status': 'ok'})
        if self.path.startswith('/api/v1/facturas/') and self.path.endswith('/estado'):
            if self.headers.get('X-API-Key') != TENANT_KEY:
                return self._json(403, {'error': 'API Key inválido'})
            return self._json(404, {'error': 'Factura no encontrada'})
        if self.path == '/api/v1/admin/tenants':
            if self.headers.get('X-Master-Key') != MASTER:
                return self._json(403, {'error': 'master key'})
            return self._json(200, [{'nit': n, 'activo': True} for n in NITS_REGISTRADOS])
        return self._json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path == '/api/v1/admin/tenants':
            if self.headers.get('X-Master-Key') != MASTER:
                return self._json(403, {'error': 'master key'})
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if body['nit'] in NITS_REGISTRADOS:
                return self._json(409, {'error': f"NIT ya registrado: {body['nit']}"})
            NITS_REGISTRADOS.add(body['nit'])
            return self._json(201, {'id': 'uuid-mock-1', 'api_key': TENANT_KEY})
        return self._json(404, {'error': 'not found'})


srv = HTTPServer(('127.0.0.1', 0), MockDian)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

from config import Config
Config.DIAN_SERVICE_URL = f'http://127.0.0.1:{port}/api/v1'
Config.DIAN_MASTER_KEY = MASTER
Config.DIAN_UI_URL = f'http://127.0.0.1:{port}/ui'

import dian_service as ds
import integrations_service as ints

SLUG = '_test_dian_integration'
fallas = []


def check(nombre, cond):
    print(('  OK ' if cond else 'FALLA'), nombre)
    if not cond:
        fallas.append(nombre)


# 1. DV
check('DV de 800197268 es 4', ds.calcular_dv('800197268') == 4)

# 2. Salud del servicio
check('service_alive() contra el mock', ds.service_alive())

# 3. Provision: crea tenant y escribe env
r = ds.provision(SLUG, nombre='Cliente Test', nit='900.373.913',
                 razon_social='Cliente Test SAS', prefijo='FT')
env = ints.read_env(SLUG)
check('provision retorna tenant id', r['tenant_dian_id'] == 'uuid-mock-1')
check('NIT normalizado (sin puntos)', r['nit'] == '900373913')
check('env: DIAN_API_KEY escrita', env.get('DIAN_API_KEY') == TENANT_KEY)
check('env: DIAN_SERVICE_URL escrita', env.get('DIAN_SERVICE_URL') == Config.DIAN_SERVICE_URL)
check('env: DIAN_MASTER_KEY escrita', env.get('DIAN_MASTER_KEY') == MASTER)
check('env: DIAN_UI_URL escrita', env.get('DIAN_UI_URL') == Config.DIAN_UI_URL)

# 4. Preserva claves existentes del env
ints.set_env_values(SLUG, {'PAYU_MERCHANT_ID': '12345'})
ds.provision(SLUG + '_b', nombre='Otro', nit='830053812', razon_social='Otro SAS')
check('set_env_values preserva claves', ints.read_env(SLUG).get('PAYU_MERCHANT_ID') == '12345')

# 5. Validate: toda la cadena OK
checks = ds.validate(SLUG)
check('validate: todas las comprobaciones pasan', all(ok for ok, _ in checks))

# 6. API key inválida detectada
ints.set_env_values(SLUG, {'DIAN_API_KEY': 'b' * 64})
checks = ds.validate(SLUG)
check('validate detecta API key rechazada', any(not ok and 'rechazada' in msg for ok, msg in checks))

# 7. NIT duplicado → DianError con mensaje claro
try:
    ds.provision(SLUG, nombre='Dup', nit='900373913', razon_social='Dup SAS')
    check('409 NIT duplicado lanza DianError', False)
except ds.DianError as exc:
    check('409 NIT duplicado lanza DianError', 'ya está registrado' in str(exc))

# 8. buscar_tenant_por_nit
t = ds.buscar_tenant_por_nit('900373913')
check('buscar_tenant_por_nit encuentra el tenant', t is not None and t['nit'] == '900373913')

# Limpieza de envs de prueba
for s in (SLUG, SLUG + '_b'):
    p = ints.env_path(s)
    if p.exists():
        p.unlink()

srv.shutdown()
print()
print('RESULTADO:', 'TODO OK' if not fallas else f'{len(fallas)} falla(s): {fallas}')
sys.exit(1 if fallas else 0)
