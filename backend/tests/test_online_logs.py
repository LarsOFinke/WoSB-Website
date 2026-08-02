from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.middleware import security_context_for_request, should_log_request
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.security_event import (
    SECURITY_SIGNAL_LOGIN_FAILURE,
    SECURITY_SIGNAL_RECONNAISSANCE,
    SecuritySignalBucket,
)
from main import app


@app.get('/api/__tests__/explode')
def explode_for_log_test() -> None:
    raise RuntimeError('operational failure must not become an IP-ban event')


def _create_user(username: str, password: str, role: str) -> None:
    with SessionLocal() as db:
        create_user(
            db,
            username=username,
            password=password,
            display_name=username,
            role=role,
        )


def test_only_ban_relevant_signals_are_persisted_without_request_metadata() -> None:
    username = 'security-event-admin'
    password = 'BlackwaterSignals123!'
    with TestClient(app, raise_server_exceptions=False) as client:
        _create_user(username, password, ROLE_ADMIN)
        login = client.post('/api/auth/login', json={'username': username, 'password': password})
        assert login.status_code == 200

        assert client.get('/api/home', headers={'X-Forwarded-For': '198.51.100.10'}).status_code == 200
        assert client.get('/api/__tests__/explode', headers={'X-Forwarded-For': '198.51.100.11'}).status_code == 500
        assert client.get('/.env', headers={'X-Forwarded-For': '198.51.100.12'}).status_code == 404
        assert client.get('/.git/config', headers={'X-Forwarded-For': '198.51.100.12'}).status_code == 404
        failed_login = client.post(
            '/api/auth/login',
            json={'username': username, 'password': 'wrong-password'},
            headers={'X-Forwarded-For': '198.51.100.13'},
        )
        assert failed_login.status_code == 401

        dashboard = client.get('/api/admin/logs/security-dashboard')
        assert dashboard.status_code == 200, dashboard.text
        body = dashboard.json()
        assert body['total_events'] == 3
        assert body['unique_ips'] == 2
        assert body['signal_counts'][SECURITY_SIGNAL_RECONNAISSANCE] == 2
        assert body['signal_counts'][SECURITY_SIGNAL_LOGIN_FAILURE] == 1

    with SessionLocal() as db:
        rows = list(db.scalars(select(SecuritySignalBucket).where(
            SecuritySignalBucket.client_ip.in_(['198.51.100.10', '198.51.100.11', '198.51.100.12', '198.51.100.13'])
        )).all())
        assert {
            (
                row.client_ip,
                row.signal,
                row.reason,
                row.request_target,
                row.event_count,
            )
            for row in rows
        } == {
            (
                '198.51.100.12',
                SECURITY_SIGNAL_RECONNAISSANCE,
                'suspicious_probe',
                'probe:environment-file',
                1,
            ),
            (
                '198.51.100.12',
                SECURITY_SIGNAL_RECONNAISSANCE,
                'suspicious_probe',
                'probe:git-metadata',
                1,
            ),
            (
                '198.51.100.13',
                SECURITY_SIGNAL_LOGIN_FAILURE,
                'login_rejected',
                '/api/auth/login',
                1,
            ),
        }
        assert set(SecuritySignalBucket.__table__.columns.keys()) == {
            'id', 'day', 'client_ip', 'signal', 'reason', 'request_target', 'event_count',
        }


def test_client_supplied_request_id_is_not_reused() -> None:
    supplied = 'visitor-email@example.test'
    with TestClient(app) as client:
        response = client.get('/api/health', headers={'X-Request-ID': supplied})
        assert response.status_code == 200
        generated = response.headers['X-Request-ID']
        assert generated != supplied
        assert len(generated) == 32
        int(generated, 16)


def test_raw_request_log_endpoints_no_longer_exist() -> None:
    username = 'no-raw-log-admin'
    password = 'BlackwaterNoRawLogs123!'
    with TestClient(app) as client:
        _create_user(username, password, ROLE_ADMIN)
        assert client.post('/api/auth/login', json={'username': username, 'password': password}).status_code == 200
        assert client.get('/api/admin/logs').status_code == 404
        assert client.get('/api/admin/logs/summary').status_code == 404
        assert client.delete('/api/admin/logs', params={'confirm': 'true'}).status_code == 404
        assert client.delete('/api/admin/logs/1').status_code == 404


def test_moderator_cannot_read_ip_ban_candidates() -> None:
    username = 'privacy-signal-moderator'
    password = 'BlackwaterPrivacySignals123!'
    with TestClient(app) as client:
        _create_user(username, password, ROLE_MODERATOR)
        assert client.post('/api/auth/login', json={'username': username, 'password': password}).status_code == 200
        assert client.get('/api/admin/logs/security-dashboard').status_code == 403


def test_security_signals_are_deleted_immediately_when_ip_is_blocked() -> None:
    username = 'signal-purge-admin'
    password = 'BlackwaterSignalPurge123!'
    blocked_ip = '198.51.100.212'
    with TestClient(app) as client:
        _create_user(username, password, ROLE_ADMIN)
        with SessionLocal() as db:
            db.add_all([
            SecuritySignalBucket(client_ip=blocked_ip, signal=SECURITY_SIGNAL_RECONNAISSANCE),
            SecuritySignalBucket(client_ip=blocked_ip, signal=SECURITY_SIGNAL_LOGIN_FAILURE),
            ])
            db.commit()

        assert client.post('/api/auth/login', json={'username': username, 'password': password}).status_code == 200
        created = client.post('/api/admin/ip-blocks', json={
            'ip_address': blocked_ip,
            'reason': 'Repeated hostile signals',
        })
        assert created.status_code == 201, created.text
        dashboard = client.get('/api/admin/logs/security-dashboard', params={'client_ip': blocked_ip})
        assert dashboard.status_code == 200
        assert dashboard.json()['total_events'] == 0

    with SessionLocal() as db:
        assert list(db.scalars(select(SecuritySignalBucket).where(SecuritySignalBucket.client_ip == blocked_ip))) == []


def test_request_log_policy_is_strictly_limited_to_ban_signals() -> None:
    assert should_log_request('/api/health', 200) is False
    assert should_log_request('/api/builds', 200) is False
    assert should_log_request('/api/builds', 404) is False
    assert should_log_request('/api/builds', 500) is False
    assert should_log_request('/.git/config', 404) is True
    assert should_log_request('/api/auth/login', 401) is True
    assert should_log_request('/api/anything', 429) is True
    assert should_log_request('/.env', 500, RuntimeError('boom')) is False


def test_security_signal_context_keeps_only_safe_aggregated_targets() -> None:
    login = security_context_for_request('/api/auth/login', 401, '/api/auth/login')
    assert login is not None
    assert (login.reason, login.request_target) == ('login_rejected', '/api/auth/login')

    limited = security_context_for_request(
        '/api/builds/42', 429, '/api/builds/{build_id}'
    )
    assert limited is not None
    assert (limited.reason, limited.request_target) == (
        'rate_limit_exceeded',
        '/api/builds/{build_id}',
    )

    probe = security_context_for_request('/.env?secret=value', 404)
    assert probe is not None
    assert (probe.reason, probe.request_target) == (
        'suspicious_probe',
        'probe:environment-file',
    )

    unmatched = security_context_for_request('/visitor-provided/value', 429)
    assert unmatched is not None
    assert unmatched.request_target == 'unmatched'
