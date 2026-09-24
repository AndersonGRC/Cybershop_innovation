"""Regresiones del control maestro; no acceden a bases de datos."""

import os
import unittest
from unittest.mock import patch


os.environ.setdefault('FLASK_SECRET_KEY', 'admin-control-test-only-secret')
os.environ.setdefault('SESSION_COOKIE_SECURE', 'false')


class AdminControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.app = create_app()
        cls.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)

    def test_inactive_admin_session_cannot_access_tenants(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session['admin_id'] = 7
        with patch('auth.current_admin', return_value=None):
            response = client.get('/tenants/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])
        with client.session_transaction() as session:
            self.assertNotIn('admin_id', session)

    def test_internal_create_persists_requested_plan_once(self):
        from routes.internal_api import create_tenant_internal
        created = {'tenant_id': 15, 'plan': 'ultra', 'warnings': []}
        with self.app.test_request_context(
            '/internal/api/v1/tenants/create', method='POST',
            json={'slug': 'cliente-a', 'nombre': 'Cliente A',
                  'email': 'admin@example.test', 'plan': 'ultra'},
        ):
            with patch('tenant_service.create_tenant', return_value=created) as create:
                response, status = create_tenant_internal.__wrapped__()
        self.assertEqual(status, 201)
        self.assertEqual(response.json['modulos_plan'], 'ultra')
        self.assertEqual(create.call_args.kwargs['plan'], 'ultra')


if __name__ == '__main__':
    unittest.main()
