from __future__ import annotations

import secrets

from sqlalchemy import case, delete, select, update
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.time import utc_now
from app.db.base import Base
from app.modules.accounts.models.user import User
from app.modules.privacy.models.data_subject_request import DataSubjectRequest
from app.modules.privacy.schemas.data_subject_request import (
    DataSubjectRequestCreate,
    DataSubjectRequestResolve,
)


class DataSubjectRequestError(ValueError):
    pass


class DataSubjectRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User, payload: DataSubjectRequestCreate) -> DataSubjectRequest:
        if user.is_bootstrap_admin and payload.request_type == "deletion":
            raise DataSubjectRequestError(
                "The bootstrap administrator cannot request account deletion."
            )
        if payload.request_type == "deletion" and payload.confirmation != user.username:
            raise DataSubjectRequestError("Confirm account deletion with your username.")
        existing = self.db.scalar(
            select(DataSubjectRequest).where(
                DataSubjectRequest.subject_user_id == user.id,
                DataSubjectRequest.request_type == payload.request_type,
                DataSubjectRequest.status == "pending",
            )
        )
        if existing is not None:
            raise DataSubjectRequestError("An equivalent request is already pending.")
        request = DataSubjectRequest(
            subject_user_id=user.id,
            request_type=payload.request_type,
            details=(payload.details or "").strip() or None,
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_for_user(self, user_id: int) -> list[DataSubjectRequest]:
        return list(
            self.db.scalars(
                select(DataSubjectRequest)
                .where(DataSubjectRequest.subject_user_id == user_id)
                .order_by(DataSubjectRequest.created_at.desc())
                .limit(100)
            ).all()
        )

    def list_all(self) -> list[DataSubjectRequest]:
        return list(
            self.db.scalars(
                select(DataSubjectRequest).order_by(
                    case((DataSubjectRequest.status == "pending", 0), else_=1),
                    DataSubjectRequest.created_at.asc(),
                ).limit(250)
            ).all()
        )

    def resolve(
        self,
        request_id: int,
        actor: User,
        payload: DataSubjectRequestResolve,
    ) -> DataSubjectRequest:
        request = self.db.get(DataSubjectRequest, request_id)
        if request is None:
            raise DataSubjectRequestError("Privacy request not found.")
        if request.status != "pending":
            raise DataSubjectRequestError("Privacy request has already been resolved.")
        subject = self.db.get(User, request.subject_user_id)
        if subject is None:
            raise DataSubjectRequestError("Subject account no longer exists.")
        if payload.decision == "complete" and request.request_type == "deletion":
            self._pseudonymize(subject)
        request.status = "completed" if payload.decision == "complete" else "rejected"
        request.resolution_note = payload.resolution_note.strip()
        request.handled_by_user_id = actor.id
        request.resolved_at = utc_now()
        self.db.commit()
        self.db.refresh(request)
        return request

    def _pseudonymize(self, user: User) -> None:
        if user.is_bootstrap_admin:
            raise DataSubjectRequestError("The bootstrap administrator cannot be deleted.")
        previous_username = user.username
        user.username = f"deleted-{user.id}-{secrets.token_hex(4)}"
        user.password_hash = hash_password(secrets.token_urlsafe(48))
        user.is_active = False
        if user.profile is not None:
            self.db.delete(user.profile)

        for table_name in (
            "auth_sessions",
            "fleet_memberships",
            "group_members",
            "build_votes",
        ):
            table = Base.metadata.tables.get(table_name)
            if table is not None and "user_id" in table.c:
                self.db.execute(delete(table).where(table.c.user_id == user.id))

        for table in Base.metadata.tables.values():
            for column in table.c:
                if not column.nullable:
                    continue
                if any(
                    foreign_key.column.table.name == "users" for foreign_key in column.foreign_keys
                ):
                    self.db.execute(
                        update(table).where(column == user.id).values({column.name: None})
                    )

        audit_logs = Base.metadata.tables.get("audit_logs")
        if audit_logs is not None:
            self.db.execute(
                update(audit_logs)
                .where(audit_logs.c.actor_username == previous_username)
                .values(actor_username="[deleted user]")
            )
        privacy_contacts = Base.metadata.tables.get("privacy_contact_requests")
        if privacy_contacts is not None:
            self.db.execute(
                update(privacy_contacts)
                .where(privacy_contacts.c.user_id == user.id)
                .values(
                    user_id=None,
                    reply_email="deleted@example.invalid",
                    message="[removed with account deletion]",
                )
            )
        self.db.add(user)
