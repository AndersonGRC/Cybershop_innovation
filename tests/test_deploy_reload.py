"""Pruebas unitarias del reload graceful; no ejecutan systemd ni usan BD."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('FLASK_SECRET_KEY', 'reload-test-only-secret')

import provisioning_service as prov


class GracefulReloadTests(unittest.TestCase):
    def test_reload_en_dev_es_noop(self):
        with patch.object(prov, 'IS_LINUX', False), patch.object(prov, '_run') as run:
            self.assertEqual(prov.reload_service('demo'), 'skipped (no-linux)')
            run.assert_not_called()

    def test_reload_usa_systemctl_y_unidad_del_tenant(self):
        result = SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch.object(prov, 'IS_LINUX', True), patch.object(prov, '_run', return_value=result) as run:
            self.assertEqual(prov.reload_service('demo'), 'reloaded')

        command = run.call_args.args[0]
        self.assertEqual(command[-3:], [prov.SYSTEMCTL, 'reload', 'cybershop@demo'])

    def test_reload_usa_unidad_primaria(self):
        result = SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch.object(prov.Config, 'PRIMARY_TENANT_SLUG', 'operador'), \
                patch.object(prov, 'IS_LINUX', True), \
                patch.object(prov, '_run', return_value=result) as run:
            prov.reload_service('operador')

        self.assertEqual(run.call_args.args[0][-1], 'cybershop')

    def test_reload_propaga_fallo_de_systemd(self):
        result = SimpleNamespace(returncode=1, stdout='', stderr='unit failed')
        with patch.object(prov, 'IS_LINUX', True), patch.object(prov, '_run', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'unit failed'):
                prov.reload_service('demo')


if __name__ == '__main__':
    unittest.main()
