from fastapi.testclient import TestClient

from app.core.middleware import should_log_request
from app.core.time import utc_now
from app.modules.admin.models.app_log import AppLog
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from main import app


@app.get('/api/__tests__/explode')
def explode_for_log_test() -> None:
    raise RuntimeError('online log regression marker')


def test_admin_can_read_persisted_exception_logs() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username='log-admin',
                password='BlackwaterLogs123!',
                display_name='Log Admin',
                role=ROLE_ADMIN,
            )

        login = client.post(
            '/api/auth/login',
            json={'username': 'log-admin', 'password': 'BlackwaterLogs123!'},
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


def test_admin_can_combine_threat_date_and_ip_log_filters() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username='security-filter-admin',
                password='BlackwaterSecurity123!',
                display_name='Security Filter Admin',
                role=ROLE_ADMIN,
            )
            now = utc_now()
            db.add_all([
                AppLog(created_at=now, level='INFO', logger='request', message='normal', path='/api/builds', status_code=200, client_ip='10.20.30.40'),
                AppLog(created_at=now, level='INFO', logger='request', message='probe', path='/.git/config', status_code=404, client_ip='198.51.100.88'),
                AppLog(created_at=now, level='ERROR', logger='request', message='probe', path='/.env', status_code=500, client_ip='198.51.100.88'),
            ])
            db.commit()

        login = client.post('/api/auth/login', json={
            'username': 'security-filter-admin',
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


def test_moderator_cannot_read_privacy_sensitive_logs() -> None:
    username = 'privacy-log-moderator'
    password = 'BlackwaterPrivacyLogs123!'
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name='Privacy Log Moderator',
                role=ROLE_MODERATOR,
            )
        login = client.post('/api/auth/login', json={'username': username, 'password': password})
        assert login.status_code == 200
        assert client.get('/api/admin/logs').status_code == 403
        assert client.get('/api/admin/logs/summary').status_code == 403
        assert client.get('/api/admin/logs/security-dashboard').status_code == 403
        assert client.delete('/api/admin/logs', params={'confirm': 'true'}).status_code == 403
        assert client.delete('/api/admin/logs/1').status_code == 403


def test_active_ip_blocks_are_hidden_from_logs_unless_explicitly_included() -> None:
    username = 'blocked-log-admin'
    password = 'BlackwaterBlockedLogs123!'
    blocked_ip = '203.0.113.211'
    path = '/api/__tests__/blocked-log-noise'
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name='Blocked Log Admin',
                role=ROLE_ADMIN,
            )
            db.add(AppLog(
                created_at=utc_now(),
                level='INFO',
                logger='request',
                message='blocked request noise',
                path=path,
                status_code=403,
                client_ip=blocked_ip,
            ))
            db.commit()

        login = client.post('/api/auth/login', json={'username': username, 'password': password})
        assert login.status_code == 200
        created = client.post('/api/admin/ip-blocks', json={
            'ip_address': blocked_ip,
            'reason': 'Repeated blocked request noise',
        })
        assert created.status_code == 201, created.text

        hidden = client.get('/api/admin/logs', params={'path': path})
        assert hidden.status_code == 200, hidden.text
        assert hidden.json() == []

        hidden_summary = client.get('/api/admin/logs/summary', params={'path': path})
        assert hidden_summary.status_code == 200
        assert hidden_summary.json()['total'] == 0

        visible = client.get('/api/admin/logs', params={'path': path, 'include_blocked': 'true'})
        assert visible.status_code == 200, visible.text
        assert len(visible.json()) == 1
        assert visible.json()[0]['client_ip'] == blocked_ip

        visible_summary = client.get('/api/admin/logs/summary', params={
            'path': path,
            'include_blocked': 'true',
        })
        assert visible_summary.status_code == 200
        assert visible_summary.json()['total'] == 1

        dashboard_hidden = client.get('/api/admin/logs/security-dashboard', params={
            'client_ip': blocked_ip,
        })
        assert dashboard_hidden.status_code == 200
        assert dashboard_hidden.json()['total_requests'] == 0

        dashboard_visible = client.get('/api/admin/logs/security-dashboard', params={
            'client_ip': blocked_ip,
            'include_blocked': 'true',
        })
        assert dashboard_visible.status_code == 200
        assert dashboard_visible.json()['total_requests'] == 1


def test_admin_can_delete_single_and_filtered_system_logs() -> None:
    username = 'delete-log-admin'
    password = 'BlackwaterDeleteLogs123!'
    visible_path = '/api/__tests__/delete-visible-logs'
    blocked_path = '/api/__tests__/delete-blocked-logs'
    blocked_ip = '198.51.100.212'
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name='Delete Log Admin',
                role=ROLE_ADMIN,
            )
            single = AppLog(
                created_at=utc_now(),
                level='WARNING',
                logger='request',
                message='single delete marker',
                path='/api/__tests__/delete-one-log',
                status_code=429,
                client_ip='198.51.100.210',
            )
            db.add(single)
            db.add_all([
                AppLog(created_at=utc_now(), level='INFO', logger='request', message='visible 1', path=visible_path, status_code=200, client_ip='198.51.100.211'),
                AppLog(created_at=utc_now(), level='ERROR', logger='request', message='visible 2', path=visible_path, status_code=500, client_ip='198.51.100.211'),
                AppLog(created_at=utc_now(), level='INFO', logger='request', message='blocked', path=blocked_path, status_code=403, client_ip=blocked_ip),
            ])
            db.commit()
            db.refresh(single)
            single_id = single.id

        login = client.post('/api/auth/login', json={'username': username, 'password': password})
        assert login.status_code == 200
        created = client.post('/api/admin/ip-blocks', json={
            'ip_address': blocked_ip,
            'reason': 'Deletion scope regression',
        })
        assert created.status_code == 201, created.text

        deleted_one = client.delete(f'/api/admin/logs/{single_id}')
        assert deleted_one.status_code == 204, deleted_one.text
        assert client.delete(f'/api/admin/logs/{single_id}').status_code == 404

        missing_confirmation = client.delete('/api/admin/logs', params={'path': visible_path})
        assert missing_confirmation.status_code == 400

        deleted_visible = client.delete('/api/admin/logs', params={
            'path': visible_path,
            'confirm': 'true',
        })
        assert deleted_visible.status_code == 200, deleted_visible.text
        assert deleted_visible.json()['deleted_count'] == 2
        assert client.get('/api/admin/logs', params={
            'path': visible_path,
            'include_blocked': 'true',
        }).json() == []

        blocked_still_exists = client.get('/api/admin/logs', params={
            'path': blocked_path,
            'include_blocked': 'true',
        })
        assert len(blocked_still_exists.json()) == 1

        deleted_blocked = client.delete('/api/admin/logs', params={
            'path': blocked_path,
            'include_blocked': 'true',
            'confirm': 'true',
        })
        assert deleted_blocked.status_code == 200, deleted_blocked.text
        assert deleted_blocked.json()['deleted_count'] == 1


        audit_rows = client.get('/api/admin/audit-logs', params={'entity_type': 'app_log'})
        assert audit_rows.status_code == 200, audit_rows.text
        assert len(audit_rows.json()) == 3
        assert {row['action'] for row in audit_rows.json()} == {'delete'}


def test_successful_log_management_requests_do_not_pollute_system_logs() -> None:
    assert should_log_request('/api/admin/logs', 200) is False
    assert should_log_request('/api/admin/logs/summary', 200) is False
    assert should_log_request('/api/admin/logs/security-dashboard', 200) is False
    assert should_log_request('/api/admin/logs/123', 204) is False
    assert should_log_request('/api/admin/logs', 500) is True
