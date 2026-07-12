from fastapi.testclient import TestClient

from app.core.middleware import should_log_request
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

        failed = client.get('/api/__tests__/explode', headers={'X-Forwarded-For': '203.0.113.42'})
        assert failed.status_code == 500

        logs = client.get('/api/admin/logs', params={'level': 'ERROR', 'path': '/api/__tests__/explode', 'client_ip': '203.0.113.42'})
        assert logs.status_code == 200, logs.text
        rows = logs.json()
        assert rows
        assert rows[0]['status_code'] == 500
        assert 'online log regression marker' in (rows[0]['exception'] or '')

        unmatched = client.get('/api/admin/logs', params={'client_ip': '198.51.100.9'})
        assert unmatched.status_code == 200
        assert unmatched.json() == []

        summary = client.get('/api/admin/logs/summary', params={'client_ip': '203.0.113.42'})
        assert summary.status_code == 200, summary.text
        body = summary.json()
        assert body['total'] >= 1
        assert body['errors'] >= 1
        assert body['recent_status']['5xx'] >= 1


def test_successful_health_probes_are_not_actionable_request_logs() -> None:
    assert should_log_request('/api/health', 200) is False
    assert should_log_request('/api/health/ready', 200) is False
    assert should_log_request('/api/health/ready', 503) is True
    assert should_log_request('/api/builds', 200) is True
