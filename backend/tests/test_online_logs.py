from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from main import app


@app.get('/api/__tests__/explode')
def explode_for_log_test() -> None:
    raise RuntimeError('online log regression marker')


def test_staff_can_read_persisted_exception_logs() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username='log-moderator',
                password='BlackwaterLogs123!',
                display_name='Log Moderator',
                role=ROLE_MODERATOR,
            )

        login = client.post(
            '/api/auth/login',
            json={'username': 'log-moderator', 'password': 'BlackwaterLogs123!'},
        )
        assert login.status_code == 200

        failed = client.get('/api/__tests__/explode')
        assert failed.status_code == 500

        logs = client.get('/api/admin/logs', params={'level': 'ERROR', 'path': '/api/__tests__/explode'})
        assert logs.status_code == 200, logs.text
        rows = logs.json()
        assert rows
        assert rows[0]['status_code'] == 500
        assert 'online log regression marker' in (rows[0]['exception'] or '')
