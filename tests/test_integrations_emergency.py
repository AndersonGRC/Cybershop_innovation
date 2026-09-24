"""Pruebas locales del aislamiento y control de gasto de integraciones."""

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault('FLASK_SECRET_KEY', 'integrations-test-only-secret')

import integrations_service as integrations  # noqa: E402


class EmergencyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        config_patch = patch.object(integrations.Config, 'INSTANCE_ENV_DIR', self.directory.name)
        config_patch.start()
        self.addCleanup(config_patch.stop)

    def test_api_key_and_budget_are_independent_per_tenant(self):
        integrations.save_integrations('cliente-a', {
            'AI_NUBE_API_KEY': 'clave-a',
            'AI_NUBE_PRESUPUESTO_USD': '1',
            'AI_NUBE_ESPERA_LOCAL_S': '180',
        })
        integrations.save_integrations('cliente-b', {
            'AI_NUBE_API_KEY': 'clave-b',
            'AI_NUBE_PRESUPUESTO_USD': '0',
        })
        self.assertEqual(integrations.read_env('cliente-a')['AI_NUBE_API_KEY'], 'clave-a')
        self.assertEqual(integrations.read_env('cliente-b')['AI_NUBE_API_KEY'], 'clave-b')
        self.assertEqual(integrations.read_env('cliente-b')['AI_NUBE_PRESUPUESTO_USD'], '0')

        fields = {field['key']: field for group in integrations.get_integrations('cliente-a')
                  for field in group['fields']}
        self.assertEqual(fields['AI_NUBE_API_KEY']['value'], '')
        self.assertEqual(fields['AI_NUBE_API_KEY']['masked'], '••••')
        self.assertNotIn('clave-a', str(fields['AI_NUBE_API_KEY']))

        integrations.save_integrations('cliente-a', {'AI_NUBE_API_KEY_CLEAR': '1'})
        self.assertEqual(integrations.read_env('cliente-a')['AI_NUBE_API_KEY'], '')
        self.assertEqual(integrations.read_env('cliente-b')['AI_NUBE_API_KEY'], 'clave-b')

    def test_default_budget_is_zero_in_admin_form(self):
        fields = {field['key']: field for group in integrations.get_integrations('nuevo')
                  for field in group['fields']}
        self.assertEqual(fields['AI_NUBE_PRESUPUESTO_USD']['value'], '0')
        self.assertEqual(fields['AI_NUBE_FALLOS_LOCAL_MIN']['value'], '3')
        self.assertEqual(fields['AI_NUBE_PARA_PUBLICO']['value'], 'false')

    def test_invalid_budget_or_early_fallback_preserves_file(self):
        integrations.save_integrations('cliente-a', {'AI_NUBE_PRESUPUESTO_USD': '0'})
        original = integrations.env_path('cliente-a').read_bytes()
        for values in (
            {'AI_NUBE_PRESUPUESTO_USD': '6'},
            {'AI_NUBE_ESPERA_LOCAL_S': '1'},
            {'AI_NUBE_FALLOS_LOCAL_MIN': '2'},
            {'AI_NUBE_MAX_TOKENS': '300'},
            {'AI_NUBE_MODEL': 'claude-sonnet-5'},
            {'AI_NUBE_API_KEY': 'secret\nDB_NAME=otro_cliente'},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                integrations.save_integrations('cliente-a', values)
            self.assertEqual(integrations.env_path('cliente-a').read_bytes(), original)

    def test_slug_cannot_escape_instance_directory(self):
        for slug in ('../cliente-b', 'cliente/b', 'C:cliente', ''):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                integrations.env_path(slug)

    @unittest.skipIf(os.name != 'posix', 'El modo POSIX no aplica a Windows')
    def test_env_file_is_private(self):
        integrations.save_integrations('cliente-a', {'AI_NUBE_API_KEY': 'secreto'})
        mode = stat.S_IMODE(Path(integrations.env_path('cliente-a')).stat().st_mode)
        self.assertEqual(mode, 0o600)


if __name__ == '__main__':
    unittest.main()
