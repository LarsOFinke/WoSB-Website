from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_MODERATOR, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.audit_log import AuditLog
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.text


def test_moderator_can_review_and_approve_account_registration() -> None:
    moderator_username = 'access-review-moderator'
    moderator_password = 'BlackwaterAccessReview123!'
    applicant_username = 'access-review-applicant'
    applicant_password = 'BlackwaterApplicant123!'

    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=moderator_username,
                password=moderator_password,
                display_name='Access Review Moderator',
                role=ROLE_MODERATOR,
            )

        registration = client.post('/api/auth/register', json={
            'username': applicant_username,
            'password': applicant_password,
            'display_name': 'Access Review Applicant',
        })
        assert registration.status_code == 202, registration.text
        request_id = registration.json()['request']['id']

        _login(client, moderator_username, moderator_password)
        listing = client.get('/api/admin/registration-requests', params={'status': 'pending'})
        assert listing.status_code == 200, listing.text
        assert request_id in {row['id'] for row in listing.json()}

        filtered = client.get('/api/admin/registration-requests', params={
            'status': 'pending',
            'search': 'Access Review Applicant',
        })
        assert filtered.status_code == 200, filtered.text
        assert [row['id'] for row in filtered.json()] == [request_id]

        no_match = client.get('/api/admin/registration-requests', params={
            'status': 'pending',
            'search': 'definitely-not-this-applicant',
        })
        assert no_match.status_code == 200, no_match.text
        assert no_match.json() == []

        approval = client.post(
            f'/api/admin/registration-requests/{request_id}/approve',
            json={'note': 'Approved by moderator access review.'},
        )
        assert approval.status_code == 200, approval.text
        assert approval.json()['status'] == 'approved'

        with SessionLocal() as db:
            created_user = db.query(User).filter(User.username == applicant_username).one_or_none()
            assert created_user is not None
            assert created_user.is_active is True
            audit_entry = db.query(AuditLog).filter(
                AuditLog.entity_type == 'registration_request',
                AuditLog.entity_id == str(request_id),
                AuditLog.action == 'update',
            ).one_or_none()
            assert audit_entry is not None
            assert 'status' in json.loads(audit_entry.changed_fields_json or '[]')


def test_moderator_cannot_access_admin_privacy_and_integration_endpoints() -> None:
    username = 'privacy-boundary-moderator'
    password = 'BlackwaterPrivacyBoundary123!'
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name='Privacy Boundary Moderator',
                role=ROLE_MODERATOR,
            )
        _login(client, username, password)

        admin_only_gets = [
            '/api/admin/system/update',
            '/api/admin/system/discord-bot',
            '/api/admin/logs',
            '/api/admin/logs/summary',
            '/api/admin/logs/security-dashboard',
            '/api/admin/ip-blocks',
            '/api/admin/ip-blocks/summary',
            '/api/admin/audit-logs',
            '/api/admin/integrations/webhooks',
            '/api/admin/integrations/webhooks/events',
            '/api/admin/integrations/webhooks/summary',
            '/api/admin/integrations/webhooks/deliveries/history',
        ]
        for endpoint in admin_only_gets:
            response = client.get(endpoint)
            assert response.status_code == 403, f'{endpoint}: {response.status_code} {response.text}'
