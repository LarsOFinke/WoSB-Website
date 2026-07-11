import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.text


def test_staff_can_read_update_status_but_only_admin_can_queue() -> None:
    control_dir = Path(settings.control_dir)
    shutil.rmtree(control_dir, ignore_errors=True)
    control_dir.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username='system-moderator',
                password='BlackwaterSystemMod123!',
                display_name='System Moderator',
                role=ROLE_MODERATOR,
            )
            create_user(
                db,
                username='system-admin',
                password='BlackwaterSystemAdmin123!',
                display_name='System Admin',
                role=ROLE_ADMIN,
            )

        assert client.get('/api/admin/system/update').status_code == 401

        _login(client, 'system-moderator', 'BlackwaterSystemMod123!')
        status_response = client.get('/api/admin/system/update')
        assert status_response.status_code == 200
        assert status_response.json()['state'] == 'idle'
        assert client.post('/api/admin/system/update', json={}).status_code == 403
        assert client.post('/api/auth/logout').status_code == 204

        _login(client, 'system-admin', 'BlackwaterSystemAdmin123!')
        queued = client.post('/api/admin/system/update')
        assert queued.status_code == 202, queued.text
        payload = queued.json()
        assert payload['accepted'] is True
        assert payload['status']['state'] == 'queued'
        assert payload['status']['operation'] == 'update'
        request_file = control_dir / 'update.request'
        assert request_file.is_file()
        assert json.loads(request_file.read_text(encoding='utf-8'))['operation'] == 'update'
        assert client.post('/api/admin/system/update', json={}).status_code == 409

        shutil.rmtree(control_dir, ignore_errors=True)
        control_dir.mkdir(parents=True, exist_ok=True)

        migration_update = client.post(
            '/api/admin/system/update',
            json={'operation': 'update_migrate_seed'},
        )
        assert migration_update.status_code == 202, migration_update.text
        migration_payload = migration_update.json()
        assert migration_payload['status']['operation'] == 'update_migrate_seed'
        request_payload = json.loads(request_file.read_text(encoding='utf-8'))
        assert request_payload['operation'] == 'update_migrate_seed'

        shutil.rmtree(control_dir, ignore_errors=True)
        control_dir.mkdir(parents=True, exist_ok=True)
        invalid = client.post('/api/admin/system/update', json={'operation': 'shell_command'})
        assert invalid.status_code == 422

    shutil.rmtree(control_dir, ignore_errors=True)
