"""Eliminar tiendas de prueba: cierre del cobro, restos, purga de backups y la
pantalla «Pruebas por limpiar». Sin bases de datos reales (todo simulado)."""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault('FLASK_SECRET_KEY', 'limpieza-test-only-secret')
os.environ.setdefault('SESSION_COOKIE_SECURE', 'false')

import lifecycle_service as lc  # noqa: E402


class CicloDeVidaTests(unittest.TestCase):
    def setUp(self):
        self.tenant = {'id': 42, 'slug': 'prueba-zyx', 'db_name': 'cyber_t042'}
        for objetivo, valor in (
            ('lifecycle_service.tenant_service.get_tenant', self.tenant),
            ('lifecycle_service.backup_db', '/tmp/x.sql'),
        ):
            p = patch(objetivo, return_value=valor)
            p.start()
            self.addCleanup(p.stop)
        for objetivo in ('lifecycle_service._teardown_runtime', 'lifecycle_service.tenant_service.set_estado',
                         'lifecycle_service.prov.set_status', 'lifecycle_service.prov.enable_service',
                         'lifecycle_service.audit_service.registrar', 'lifecycle_service.destroy_database',
                         'lifecycle_service._borrar_restos'):
            p = patch(objetivo)
            setattr(self, objetivo.rsplit('.', 1)[-1], p.start())
            self.addCleanup(p.stop)
        self.billing = MagicMock()
        p = patch('lifecycle_service._billing', return_value=self.billing)
        p.start()
        self.addCleanup(p.stop)

    def test_cancelar_cierra_el_cobro_como_cancelada(self):
        lc.destroy_soft(42)
        self.billing.cerrar_compra_motor.assert_called_once_with(42, 'CANCELADA')
        self.destroy_database.assert_not_called()

    def test_eliminar_cierra_el_cobro_borra_bd_y_restos(self):
        lc.destroy_hard(42)
        self.billing.cerrar_compra_motor.assert_any_call(42, 'ELIMINADA')
        self.destroy_database.assert_called_once_with('cyber_t042')
        self._borrar_restos.assert_called_once_with(42, 'prueba-zyx')

    def test_reactivar_reabre_el_cobro(self):
        with patch('lifecycle_service.prov.IS_LINUX', False):
            lc.reactivate(42)
        self.billing.reabrir_compra_motor.assert_called_once_with(42)

    def test_si_el_motor_falla_la_eliminacion_sigue(self):
        self.billing.cerrar_compra_motor.side_effect = RuntimeError('BD del operador caída')
        lc.destroy_hard(42)
        self.destroy_database.assert_called_once()


class BackupsTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        p = patch.object(lc.Config, 'BACKUP_DIR', self.dir.name)
        p.start()
        self.addCleanup(p.stop)
        viejo = time.time() - 40 * 86400
        self.archivos = {}
        for nombre, edad in (('prueba-zyx-20260801_101010.sql', viejo), ('prueba-zyx-20260930_101010.sql', None),
                             ('prueba-zyx-roma-20260801_101010.sql', viejo), ('pago-ok-20260801_101010.sql', viejo)):
            ruta = Path(self.dir.name) / nombre
            ruta.write_text('-- dump')
            if edad:
                os.utime(ruta, (edad, edad))
            self.archivos[nombre] = ruta

    def _con_cancelados(self, cancelados, sin_pagar):
        cur = MagicMock()
        cur.fetchall.return_value = cancelados
        cm = MagicMock()
        cm.__enter__.return_value = cur
        billing = MagicMock()
        billing.es_prueba_sin_pagar.side_effect = lambda tid: tid in sin_pagar
        return patch('db.control_plane_cursor', return_value=cm), patch('lifecycle_service._billing', return_value=billing)

    def test_patron_exacto_del_backup(self):
        patron = lc._patron_backup('prueba-zyx')
        self.assertTrue(patron.match('prueba-zyx-20260801_101010.sql'))
        self.assertTrue(patron.match('prueba-zyx-20260801_101010.sql.gz'))
        self.assertFalse(patron.match('prueba-zyx-roma-20260801_101010.sql'))

    def test_solo_borra_pruebas_sin_pagar_de_mas_de_30_dias(self):
        p_db, p_billing = self._con_cancelados(
            [{'id': 42, 'slug': 'prueba-zyx'}, {'id': 7, 'slug': 'pago-ok'}], sin_pagar={42})
        with p_db, p_billing, patch('lifecycle_service.audit_service.registrar'):
            archivos, _total = lc.purgar_backups_pruebas()
        self.assertEqual(archivos, 1)
        self.assertFalse(self.archivos['prueba-zyx-20260801_101010.sql'].exists())
        self.assertTrue(self.archivos['prueba-zyx-20260930_101010.sql'].exists(), 'reciente: se conserva')
        self.assertTrue(self.archivos['prueba-zyx-roma-20260801_101010.sql'].exists(), 'otro cliente')
        self.assertTrue(self.archivos['pago-ok-20260801_101010.sql'].exists(), 'cliente que pagó')


class PantallaPruebasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.app = create_app()
        cls.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False, WTF_CSRF_ENABLED=False)

    def setUp(self):
        self.client = self.app.test_client()
        with self.client.session_transaction() as s:
            s['admin_id'] = 1
        p = patch('auth.current_admin', return_value={'id': 1, 'email': 'op@x.com', 'nombre': 'Op'})
        p.start()
        self.addCleanup(p.stop)
        candidatas = [{'tenant_id': 42, 'slug': 'prueba-zyx', 'nombre_negocio': 'Prueba', 'buyer_nombre': 'Ana',
                       'buyer_email': 'a@x.com', 'buyer_telefono': '3001234567', 'dominio': 'p.cybershopcol.com',
                       'proximo_pago': '2026-09-01', 'dias_vencida': 30, 'estado': 'ACTIVADA',
                       'suspendida_por_pago': False, 'estado_cliente': 'activo'}]
        p = patch('routes.pruebas_routes._candidatas', return_value=candidatas)
        p.start()
        self.addCleanup(p.stop)
        p = patch('routes.pruebas_routes.lc.backups_pruebas_vencidos', return_value=[])
        p.start()
        self.addCleanup(p.stop)

    def test_lista(self):
        html = self.client.get('/pruebas/').get_data(as_text=True)
        self.assertIn('Pruebas por limpiar', html)
        self.assertIn('prueba-zyx', html)

    def test_sin_confirmacion_no_elimina(self):
        with patch('routes.pruebas_routes.lc.destroy_hard') as destroy:
            self.client.post('/pruebas/eliminar', data={'tenant_id': ['42'], 'confirmacion': 'si'})
        destroy.assert_not_called()

    def test_solo_elimina_las_que_siguen_siendo_candidatas(self):
        with patch('routes.pruebas_routes.lc.destroy_hard') as destroy:
            self.client.post('/pruebas/eliminar', data={'tenant_id': ['42', '7'], 'confirmacion': 'eliminar'})
        destroy.assert_called_once()
        self.assertEqual(destroy.call_args.args[0], 42)


if __name__ == '__main__':
    unittest.main()
