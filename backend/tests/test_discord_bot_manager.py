from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.text


def _create_admin(suffix: str) -> tuple[str, str]:
    username = f'discord-bot-admin-{suffix}'
    password = 'BlackwaterDiscordBotManager123!'
    with SessionLocal() as db:
        create_user(db, username=username, password=password, display_name='Discord Bot Admin', role=ROLE_ADMIN)
    return username, password


def _cleanup() -> Path:
    control_dir = Path(settings.control_dir)
    control_dir.mkdir(parents=True, exist_ok=True)
    for name in ('discord-bot-status.json', 'discord-bot.request', 'discord-bot.log'):
        (control_dir / name).unlink(missing_ok=True)
    return control_dir


def test_admin_can_read_and_queue_discord_bot_install() -> None:
    control_dir = _cleanup()
    with TestClient(app) as client:
        username, password = _create_admin('install')
        _login(client, username, password)
        status = client.get('/api/admin/system/discord-bot')
        assert status.status_code == 200, status.text
        assert status.json()['installed'] is False
        queued = client.post('/api/admin/system/discord-bot', json={'operation': 'install'})
        assert queued.status_code == 202, queued.text
        assert queued.json()['status']['state'] == 'queued'
        request_payload = json.loads((control_dir / 'discord-bot.request').read_text(encoding='utf-8'))
        assert request_payload['operation'] == 'install'
    _cleanup()


def test_non_install_operation_requires_installed_bot() -> None:
    _cleanup()
    with TestClient(app) as client:
        username, password = _create_admin('restart')
        _login(client, username, password)
        response = client.post('/api/admin/system/discord-bot', json={'operation': 'restart'})
        assert response.status_code == 409
    _cleanup()


def test_admin_can_queue_protected_discord_bot_runtime_configuration() -> None:
    control_dir = _cleanup()
    (control_dir / 'discord-bot-status.json').write_text(
        json.dumps(
            {
                'state': 'idle',
                'operation': 'status',
                'message': 'installed',
                'configured': True,
                'installed': True,
                'service_state': 'inactive',
                'configuration': {},
            }
        ),
        encoding='utf-8',
    )
    with TestClient(app) as client:
        username, password = _create_admin('configure')
        _login(client, username, password)
        response = client.put(
            '/api/admin/system/discord-bot/configuration',
            json={
                'discord_bot_token': 'discord-token-value-that-is-long-enough',
                'webhook_secret': 'webhook-signing-secret-that-is-long-enough-123456',
                'website_base_url': 'https://fleet.example',
                'channels': {
                    'events': '100000000000000001',
                    'guides': '100000000000000002',
                    'builds': '100000000000000003',
                    'forum': '100000000000000004',
                    'default': '100000000000000005',
                },
                'suppress_notifications': True,
                'restart_after_save': True,
            },
        )
        assert response.status_code == 202, response.text
        request_file = control_dir / 'discord-bot.request'
        request_payload = json.loads(request_file.read_text(encoding='utf-8'))
        assert request_payload['operation'] == 'configure'
        assert request_payload['configuration']['discord_bot_token'].startswith('discord-token')
        assert request_payload['configuration']['channels']['events'] == '100000000000000001'
        assert request_file.stat().st_mode & 0o777 == 0o600
        status_payload = json.loads((control_dir / 'discord-bot-status.json').read_text(encoding='utf-8'))
        assert 'discord-token-value' not in json.dumps(status_payload)
        assert 'webhook-signing-secret' not in json.dumps(status_payload)
    _cleanup()


def test_discord_bot_configuration_rejects_invalid_channel_ids() -> None:
    control_dir = _cleanup()
    (control_dir / 'discord-bot-status.json').write_text(
        json.dumps({'state': 'idle', 'configured': True, 'installed': True, 'configuration': {}}),
        encoding='utf-8',
    )
    with TestClient(app) as client:
        username, password = _create_admin('invalid-channel')
        _login(client, username, password)
        response = client.put(
            '/api/admin/system/discord-bot/configuration',
            json={
                'discord_bot_token': 'discord-token-value-that-is-long-enough',
                'webhook_secret': 'webhook-signing-secret-that-is-long-enough-123456',
                'website_base_url': 'https://fleet.example',
                'channels': {
                    'events': 'not-a-channel',
                    'guides': '100000000000000002',
                    'builds': '100000000000000003',
                    'forum': '100000000000000004',
                    'default': '100000000000000005',
                },
            },
        )
        assert response.status_code == 422
        assert not (control_dir / 'discord-bot.request').exists()
    _cleanup()
