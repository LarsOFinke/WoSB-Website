from __future__ import annotations

from cryptography.fernet import Fernet, MultiFernet
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.secret_box import SecretBox, SecretBoxError, webhook_secret_box
from app.db.base import Base
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.outbound_webhook import OutboundWebhook
from app.modules.admin.schemas.outbound_webhook import (
    OutboundWebhookBroadcastRequest,
    OutboundWebhookCreate,
)
from app.modules.admin.services.outbound_webhook_service import (
    OutboundWebhookError,
    create_webhook,
    encrypt_legacy_webhook_endpoints,
    endpoint_url_for_delivery,
)
from app.modules.registry import register_all_models


def isolated_session() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def _box(*keys: bytes) -> SecretBox:
    fernets = [Fernet(key) for key in keys]
    return SecretBox(primary=fernets[0], cryptor=MultiFernet(fernets))


def test_secret_box_encrypts_authenticates_and_rotates() -> None:
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()
    old_box = _box(old_key)
    rotating_box = _box(new_key, old_key)

    ciphertext = old_box.encrypt("https://discord.com/api/webhooks/123/token")
    assert ciphertext.startswith("fernet:v1:")
    assert "discord.com" not in ciphertext
    assert rotating_box.decrypt(ciphertext).endswith("/123/token")
    assert rotating_box.needs_rotation(ciphertext)

    rotated = rotating_box.rotate(ciphertext)
    assert rotated != ciphertext
    assert not rotating_box.needs_rotation(rotated)
    assert rotating_box.decrypt(rotated).endswith("/123/token")


def test_secret_box_rejects_tampered_ciphertext() -> None:
    box = _box(Fernet.generate_key())
    ciphertext = box.encrypt("secret")
    offset = len(box.prefix) + 12
    replacement = "A" if ciphertext[offset] != "A" else "B"
    tampered = f"{ciphertext[:offset]}{replacement}{ciphertext[offset + 1:]}"
    try:
        box.decrypt(tampered)
    except SecretBoxError:
        pass
    else:  # pragma: no cover - cryptographic failure would be critical
        raise AssertionError("tampered ciphertext was accepted")


def test_webhook_service_stores_endpoint_encrypted_and_masks_api_value() -> None:
    with isolated_session() as db:
        actor = create_user(
            db,
            username="encrypted-hook-admin",
            password="BlackwaterWebhookEncryption123!",
            display_name="Webhook Encryption Admin",
            role=ROLE_ADMIN,
        )
        plaintext = "https://discord.com/api/webhooks/123456789012345678/long-test-token"
        result = create_webhook(
            db,
            OutboundWebhookCreate(
                name="Encrypted hook",
                endpoint_url=plaintext,
                event_types=["integration.test"],
            ),
            actor,
        )
        stored = db.get(OutboundWebhook, result.id)
        assert stored is not None
        assert stored.endpoint_url.startswith("fernet:v1:")
        assert plaintext not in stored.endpoint_url
        assert webhook_secret_box.decrypt(stored.endpoint_url) == plaintext
        assert "long-test-token" not in result.endpoint_url


def test_maintenance_encrypts_legacy_plaintext_endpoint() -> None:
    with isolated_session() as db:
        actor = create_user(
            db,
            username="legacy-hook-admin",
            password="BlackwaterLegacyEncryption123!",
            display_name="Legacy Hook Admin",
            role=ROLE_ADMIN,
        )
        row = OutboundWebhook(
            name="Legacy hook",
            endpoint_url="https://discord.com/api/webhooks/123456789012345678/legacy-token",
            event_types_json='["integration.test"]',
            scope_type="global",
            created_by_user_id=actor.id,
            created_by_username=actor.username,
        )
        db.add(row)
        db.commit()

        assert encrypt_legacy_webhook_endpoints(db) == 1
        db.refresh(row)
        assert row.endpoint_url.startswith("fernet:v1:")
        assert webhook_secret_box.decrypt(row.endpoint_url).endswith("/legacy-token")
        assert encrypt_legacy_webhook_endpoints(db) == 0


def test_delivery_revalidates_the_decrypted_discord_target() -> None:
    row = OutboundWebhook(
        name="Tampered target",
        endpoint_url=webhook_secret_box.encrypt("https://example.com/api/webhooks/123/token"),
        event_types_json='["integration.test"]',
        scope_type="global",
        created_by_user_id=1,
        created_by_username="audit",
    )

    try:
        endpoint_url_for_delivery(row)
    except OutboundWebhookError as exc:
        assert "official Discord" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("non-Discord encrypted target crossed the outbound boundary")


def test_avatar_override_is_rejected_at_the_api_boundary() -> None:
    try:
        OutboundWebhookBroadcastRequest(
            webhook_ids=[1],
            message="Fleet broadcast",
            discord_avatar_url="https://example.invalid/avatar.png",
        )
    except ValidationError as exc:
        assert "discord_avatar_url" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("obsolete avatar override was accepted")
