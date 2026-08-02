from datetime import timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.modules.accounts.models.user import User
from app.modules.privacy.models.privacy_contact_request import PrivacyContactRequest
from app.modules.privacy.schemas.privacy_contact_request import (
    PrivacyContactCreate,
    PrivacyContactResolve,
)


class PrivacyContactError(ValueError):
    pass


class PrivacyContactService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self, payload: PrivacyContactCreate, current_user: User | None
    ) -> PrivacyContactRequest:
        recent = self.db.scalar(
            select(func.count())
            .select_from(PrivacyContactRequest)
            .where(
                PrivacyContactRequest.reply_email == payload.reply_email,
                PrivacyContactRequest.created_at >= utc_now() - timedelta(minutes=30),
            )
        )
        if int(recent or 0) >= 3:
            raise PrivacyContactError("Too many recent privacy messages for this reply address.")
        request = PrivacyContactRequest(
            user_id=current_user.id if current_user else None,
            reply_email=payload.reply_email,
            subject=" ".join(payload.subject.split()),
            message=payload.message.strip(),
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_all(self) -> list[PrivacyContactRequest]:
        return list(
            self.db.scalars(
                select(PrivacyContactRequest).order_by(
                    case((PrivacyContactRequest.status == "pending", 0), else_=1),
                    PrivacyContactRequest.created_at.asc(),
                ).limit(250)
            ).all()
        )

    def resolve(
        self, request_id: int, actor: User, payload: PrivacyContactResolve
    ) -> PrivacyContactRequest:
        request = self.db.get(PrivacyContactRequest, request_id)
        if request is None:
            raise PrivacyContactError("Privacy contact request not found.")
        if request.status != "pending":
            raise PrivacyContactError("Privacy contact request has already been resolved.")
        request.status = "completed" if payload.decision == "complete" else "rejected"
        request.resolution_note = payload.resolution_note.strip()
        request.handled_by_user_id = actor.id
        request.resolved_at = utc_now()
        self.db.commit()
        self.db.refresh(request)
        return request
