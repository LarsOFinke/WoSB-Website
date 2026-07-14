from fastapi.testclient import TestClient

from app.core.middleware import should_log_request
from app.core.time import utc_now
from app.modules.admin.models.app_log import AppLog
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


def test_staff_can_combine_threat_date_and_ip_log_filters() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username='security-filter-moderator',
                password='BlackwaterSecurity123!',
                display_name='Security Filter Moderator',
                role=ROLE_MODERATOR,
            )
            now = utc_now()
            db.add_all([
                AppLog(created_at=now, level='INFO', logger='request', message='normal', path='/api/builds', status_code=200, client_ip='10.20.30.40'),
                AppLog(created_at=now, level='INFO', logger='request', message='probe', path='/.git/config', status_code=404, client_ip='198.51.100.88'),
                AppLog(created_at=now, level='ERROR', logger='request', message='probe', path='/.env', status_code=500, client_ip='198.51.100.88'),
            ])
            db.commit()

        login = client.post('/api/auth/login', json={
            'username': 'security-filter-moderator',
            'password': 'BlackwaterSecurity123!',
        })
        assert login.status_code == 200

        day = utc_now().date().isoformat()
        params = {
            'from_date': day,
            'to_date': day,
            'threat_level': 'elevated',
            'client_ip': '198.51.100.88',
        }
        logs = client.get('/api/admin/logs', params=params)
        assert logs.status_code == 200, logs.text
        assert len(logs.json()) == 2
        assert {row['client_ip'] for row in logs.json()} == {'198.51.100.88'}

        summary = client.get('/api/admin/logs/summary', params=params)
        assert summary.status_code == 200, summary.text
        assert summary.json()['total'] == 2

        dashboard = client.get('/api/admin/logs/security-dashboard', params=params)
        assert dashboard.status_code == 200, dashboard.text
        body = dashboard.json()
        assert body['total_requests'] == 2
        assert body['unique_ips'] == 1
        assert body['ips'][0]['client_ip'] == '198.51.100.88'
