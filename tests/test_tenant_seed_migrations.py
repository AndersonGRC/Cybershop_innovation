"""Una migración fallida no puede quedar marcada como aplicada."""

import pytest

import tenant_migrations
import tenant_service


def test_seed_aborta_si_falla_una_migracion(monkeypatch):
    class Conn:
        def close(self):
            pass

    monkeypatch.setattr(tenant_service, 'get_tenant_conn', lambda _db: Conn())
    monkeypatch.setattr(tenant_service.seed_service, 'apply_seed',
                        lambda *_a, **_k: {'admin_email': 'test@example.com'})
    monkeypatch.setattr(tenant_migrations, 'migrate_db',
                        lambda _db: (_ for _ in ()).throw(RuntimeError('migración rota')))
    monkeypatch.setattr(tenant_migrations, 'mark_all_applied',
                        lambda _db: pytest.fail('no debe marcar migraciones fallidas'))

    with pytest.raises(tenant_service.TenantCreationError, match='sin marcarlas como aplicadas'):
        tenant_service._apply_seed('cyber_t999', 'Prueba', 'test@example.com')
