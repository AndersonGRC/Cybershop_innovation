"""Pruebas que no escriben en bases ni ejecutan acciones de infraestructura."""

import os
import re
import unittest


os.environ.setdefault('FLASK_SECRET_KEY', 'csrf-test-only-secret')
os.environ.setdefault('SESSION_COOKIE_SECURE', 'false')


class CsrfProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app

        cls.app = create_app()
        cls.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)

        @cls.app.post('/_test/csrf-valid')
        def csrf_valid_probe():
            return {'ok': True}

        cls.client = cls.app.test_client()

    def test_login_publica_token(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="csrf-token"', response.data)
        self.assertIn(b'name="csrf_token"', response.data)

    def test_login_post_sin_token_es_rechazado(self):
        response = self.client.post('/login', data={'email': 'x', 'password': 'x'})
        self.assertEqual(response.status_code, 400)

    def test_post_con_token_valido_es_aceptado(self):
        page = self.client.get('/login')
        match = re.search(rb'name="csrf-token" content="([^"]+)"', page.data)
        self.assertIsNotNone(match)

        response = self.client.post(
            '/_test/csrf-valid',
            data={'csrf_token': match.group(1).decode('utf-8')},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'ok': True})

    def test_autorizar_ip_post_sin_token_es_rechazado(self):
        response = self.client.post('/autorizar-ip')
        self.assertEqual(response.status_code, 400)

    def test_api_interna_no_depende_de_csrf(self):
        response = self.client.post('/internal/api/v1/tenants/1/suspend', json={})
        self.assertIn(response.status_code, (401, 503))
        self.assertNotEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
