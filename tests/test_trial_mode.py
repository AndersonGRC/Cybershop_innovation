"""Modo prueba: apaga integraciones externas sin pisar lo configurado y se quita limpio."""

import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('FLASK_SECRET_KEY', 'trial-mode-test-only-secret')

import integrations_service as ints  # noqa: E402
import trial_mode_service as trial  # noqa: E402


class TrialModeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        p = patch.object(ints.Config, 'INSTANCE_ENV_DIR', self.directory.name)
        p.start()
        self.addCleanup(p.stop)
        # Lo que deja la creación del cliente (write_instance_env).
        ints._write_env('prueba-uno', {'PORT': '8150', 'DB_NAME': 'cyber_t150', 'AI_BASE_URL': 'http://ia'})

    def test_aplicar_apaga_las_integraciones_y_conserva_lo_demas(self):
        apagadas = trial.aplicar('prueba-uno')
        env = ints.read_env('prueba-uno')
        self.assertEqual(set(apagadas), set(trial.LLAVES_APAGADAS))
        for llave in trial.LLAVES_APAGADAS:
            self.assertEqual(env[llave], '')
        self.assertEqual(env['PORT'], '8150')
        self.assertEqual(env['DB_NAME'], 'cyber_t150')
        self.assertEqual(env['AI_BASE_URL'], 'http://ia', 'la IA se mantiene (decisión del dueño)')
        self.assertTrue(trial.esta_activo('prueba-uno'))
        self.assertNotIn('MAIL_USERNAME', env, 'el correo se mantiene: sigue heredando lo compartido')

    def test_no_pisa_un_valor_ya_configurado(self):
        ints.set_env_values('prueba-uno', {'PAYU_MERCHANT_ID': '508029'})
        apagadas = trial.aplicar('prueba-uno')
        self.assertNotIn('PAYU_MERCHANT_ID', apagadas)
        self.assertEqual(ints.read_env('prueba-uno')['PAYU_MERCHANT_ID'], '508029')

    def test_quitar_borra_solo_lo_que_sigue_vacio(self):
        trial.aplicar('prueba-uno')
        ints.set_env_values('prueba-uno', {'PAYU_API_KEY': 'llave-propia'})   # el operador le puso la suya
        quitadas = trial.quitar('prueba-uno')
        env = ints.read_env('prueba-uno')
        self.assertNotIn('PAYU_API_KEY', quitadas)
        self.assertEqual(env['PAYU_API_KEY'], 'llave-propia')
        self.assertNotIn('GOOGLE_CLIENT_ID', env)
        self.assertNotIn(trial.MARCA, env)
        self.assertEqual(env['DB_NAME'], 'cyber_t150')
        self.assertFalse(trial.esta_activo('prueba-uno'))

    def test_quitar_sin_modo_prueba_no_hace_nada(self):
        ints.set_env_values('prueba-uno', {'GOOGLE_CLIENT_ID': ''})
        self.assertEqual(trial.quitar('prueba-uno'), [])
        self.assertIn('GOOGLE_CLIENT_ID', ints.read_env('prueba-uno'))


if __name__ == '__main__':
    unittest.main()
