from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.models import Group, GroupParticipant, User
from app.repositories import GroupRepository, ShipRepository
from app.schemas.group import GroupCreate, GroupParticipantCreate, GroupParticipantRead, GroupRead, GroupUpdate
from app.services.group.group_full_error import GroupFullError
from app.services.group.group_not_found_error import GroupNotFoundError
from app.services.group.group_permission_error import GroupPermissionError

GROUP_STATUS_OPEN = "open"
GROUP_STATUS_FULL = "full"
GROUP_STATUS_CLOSED = "closed"
GROUP_STATUS_EXPIRED = "expired"

ACTIVE_JOIN_STATUSES = {GROUP_STATUS_OPEN}
VALID_GROUP_STATUSES = {GROUP_STATUS_OPEN, GROUP_STATUS_FULL, GROUP_STATUS_CLOSED, GROUP_STATUS_EXPIRED}

FOCUS_LABELS = {
    "pve_farming": "PvE Farming",
    "pve_imp_hunting": "PvE Imp-Hunting",
    "pve_general": "PvE Allgemein",
    "pvp_open_world": "PvP Open-World",
    "pvp_arena": "PvP Arena",
    "pvp_general": "PvP Allgemein",
    "trading": "Trading",
    "other": "Sonstiges",
}

STATUS_LABELS = {
    GROUP_STATUS_OPEN: "Offen",
    GROUP_STATUS_FULL: "Voll",
    GROUP_STATUS_CLOSED: "Geschlossen",
    GROUP_STATUS_EXPIRED: "Abgelaufen",
}


class GroupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.groups = GroupRepository(db)
        self.ships = ShipRepository(db)

    def list_groups(self, *, viewer: User | None = None, include_inactive: bool = False) -> list[GroupRead]:
        groups = self.groups.list(include_inactive=include_inactive)
        changed = self._expire_groups_if_needed(groups)
        changed = self._refresh_statuses(groups) or changed
        if changed:
            self.db.commit()
            groups = self.groups.list(include_inactive=include_inactive)
        return [self._to_read(group, viewer=viewer) for group in groups]

    def list_manageable_groups(self, *, viewer: User) -> list[GroupRead]:
        groups = self.groups.list(include_inactive=True) if viewer.role == "admin" else self.groups.list_by_owner(viewer.id)
        changed = self._expire_groups_if_needed(groups)
        changed = self._refresh_statuses(groups) or changed
        if changed:
            self.db.commit()
            groups = self.groups.list(include_inactive=True) if viewer.role == "admin" else self.groups.list_by_owner(viewer.id)
        return [self._to_read(group, viewer=viewer) for group in groups]

    def get_group(self, group_id: int, *, viewer: User | None = None) -> GroupRead | None:
        group = self.groups.get(group_id)
        if not group:
            return None
        changed = self._expire_group_if_needed(group)
        changed = self._refresh_group_status(group) or changed
        if changed:
            self.db.commit()
            group = self.groups.get(group_id)
            assert group is not None
        return self._to_read(group, viewer=viewer)

    def create_group(self, payload: GroupCreate, *, owner: User) -> GroupRead:
        ship = self.ships.get(payload.ship_id) if payload.ship_id else None
        self._ensure_ship_rate_allowed(payload.min_ship_rate)
        group = Group(
            owner_id=owner.id,
            ship_id=ship.id if ship else None,
            ship_class_label=payload.ship_class or (ship.ship_class if ship else "Beliebig"),
            title=payload.title,
            description=payload.description,
            focus=payload.focus,
            max_members=payload.max_members,
            min_ship_rate=payload.min_ship_rate,
            allow_anonymous=payload.allow_anonymous,
            fleet_restriction=self._normalize_text(payload.fleet_restriction),
            scheduled_at=payload.scheduled_at,
            status=GROUP_STATUS_OPEN,
            active=True,
            expires_at=self._now() + timedelta(hours=24),
        )
        self.groups.create(group)
        self.db.flush()
        self.groups.add_participant(
            GroupParticipant(
                group_id=group.id,
                user_id=owner.id,
                is_anonymous=False,
                display_name=owner.display_name,
                status="member",
                participant_role=None,
                fleet_name=getattr(owner.profile, "fleet_name", None) if getattr(owner, "profile", None) else None,
                join_token=None,
                active=True,
            )
        )
        self._refresh_group_status(group)
        self.db.commit()
        self.db.expire_all()
        created = self.groups.get(group.id)
        assert created is not None
        return self._to_read(created, viewer=owner)

    def update_group(self, group_id: int, payload: GroupUpdate, *, actor: User) -> GroupRead:
        group = self._get_group_or_raise(group_id)
        self._ensure_can_manage(group, actor)
        if group.status == GROUP_STATUS_EXPIRED:
            raise GroupPermissionError("Abgelaufene Gruppen können nicht mehr bearbeitet werden.")

        update_data = payload.model_dump(exclude_unset=True)
        if "ship_id" in update_data:
            ship = self.ships.get(payload.ship_id) if payload.ship_id else None
            group.ship_id = ship.id if ship else None
            if ship:
                group.ship_class_label = ship.ship_class
        if "ship_class" in update_data and payload.ship_class is not None:
            group.ship_class_label = payload.ship_class
        if "status" in update_data and payload.status is not None and payload.status not in VALID_GROUP_STATUSES:
            raise GroupPermissionError("Ungültiger Gruppenstatus.")
        if "min_ship_rate" in update_data:
            self._ensure_ship_rate_allowed(payload.min_ship_rate)

        for field in [
            "title",
            "description",
            "focus",
            "max_members",
            "min_ship_rate",
            "allow_anonymous",
            "fleet_restriction",
            "scheduled_at",
            "status",
        ]:
            if field in update_data:
                setattr(group, field, update_data[field])

        if group.status in {GROUP_STATUS_CLOSED, GROUP_STATUS_EXPIRED}:
            now = self._now()
            group.active = False
            group.closed_at = group.closed_at or now
            group.archived_at = group.archived_at or now

        self._refresh_group_status(group)
        self.db.commit()
        self.db.expire_all()
        refreshed = self.groups.get(group.id)
        assert refreshed is not None
        return self._to_read(refreshed, viewer=actor)

    def close_group(self, group_id: int, *, actor: User) -> GroupRead:
        group = self._get_group_or_raise(group_id)
        self._ensure_can_manage(group, actor)
        now = self._now()
        group.status = GROUP_STATUS_CLOSED
        group.active = False
        group.closed_at = now
        group.archived_at = now
        self.db.commit()
        self.db.expire_all()
        refreshed = self.groups.get(group.id)
        assert refreshed is not None
        return self._to_read(refreshed, viewer=actor)

    def delete_group(self, group_id: int, *, actor: User) -> None:
        group = self._get_group_or_raise(group_id)
        self._ensure_can_manage(group, actor)
        self.groups.delete(group)
        self.db.commit()

    def join_group(self, group_id: int, payload: GroupParticipantCreate, *, actor: User | None = None) -> GroupRead:
        group = self._get_group_or_raise(group_id)
        self._expire_group_if_needed(group)
        self._refresh_group_status(group)
        self._ensure_can_join(group, actor=actor, payload=payload)

        if actor:
            existing = self._find_user_participation(group, actor.id)
            if existing:
                return self._to_read(group, viewer=actor)
            display_name = self._normalize_text(payload.display_name) or actor.display_name
            user_id = actor.id
            is_anonymous = False
            join_token = None
            join_token_hash = None
            fleet_name = self._normalize_text(payload.fleet_name) or (
                getattr(actor.profile, "fleet_name", None) if getattr(actor, "profile", None) else None
            )
        else:
            display_name = self._normalize_text(payload.display_name)
            if not display_name:
                raise GroupPermissionError("Gäste müssen für die Anmeldung einen Ingame-Namen angeben.")
            if not group.allow_anonymous:
                raise GroupPermissionError("Diese Gruppe erlaubt keine anonyme Teilnahme.")
            if self._find_display_name_participation(group, display_name):
                raise GroupPermissionError("Dieser Name ist in der Gruppe bereits vergeben.")
            user_id = None
            is_anonymous = True
            join_token = self._create_join_token()
            join_token_hash = self._hash_token(join_token)
            fleet_name = self._normalize_text(payload.fleet_name)

        selected_ship = self.ships.get(payload.ship_id) if payload.ship_id else None
        participant = GroupParticipant(
            group_id=group.id,
            user_id=user_id,
            is_anonymous=is_anonymous,
            display_name=display_name,
            status="member",
            participant_role=self._normalize_text(payload.participant_role),
            join_token=None,
            anonymous_edit_token_hash=join_token_hash,
            fleet_name=fleet_name,
            ship_id=selected_ship.id if selected_ship else None,
            custom_ship_name=self._normalize_text(payload.custom_ship_name),
            custom_ship_rate=payload.custom_ship_rate,
            note=self._normalize_text(payload.note),
            active=True,
        )
        self.groups.add_participant(participant)
        self._refresh_group_status(group)
        self.db.commit()
        self.db.expire_all()
        refreshed = self.groups.get(group.id)
        assert refreshed is not None
        return self._to_read(
            refreshed,
            viewer=actor,
            guest_join_token=join_token,
            guest_display_name=display_name if actor is None else None,
        )

    def leave_group_by_token(self, join_token: str) -> None:
        token_hash = self._hash_token(join_token)
        participant = self.groups.get_participant_by_token_hash(token_hash) or self.groups.get_participant_by_token(join_token)
        if not participant:
            raise GroupNotFoundError("Teilnahme nicht gefunden.")
        participant.active = False
        participant.status = "left"
        participant.left_at = self._now()
        group = participant.group
        self._refresh_group_status(group)
        self.db.commit()

    def _get_group_or_raise(self, group_id: int) -> Group:
        group = self.groups.get(group_id)
        if not group:
            raise GroupNotFoundError("Gruppe nicht gefunden.")
        return group

    def _ensure_can_manage(self, group: Group, actor: User) -> None:
        if not self._can_manage(group, actor):
            raise GroupPermissionError("Du darfst diese Gruppe nicht verwalten.")

    def _ensure_can_join(self, group: Group, *, actor: User | None, payload: GroupParticipantCreate) -> None:
        if not group.active:
            raise GroupPermissionError("Diese Gruppe ist nicht mehr aktiv.")
        if group.status == GROUP_STATUS_EXPIRED:
            raise GroupPermissionError("Diese Gruppe ist bereits abgelaufen.")
        if group.status == GROUP_STATUS_CLOSED:
            raise GroupPermissionError("Diese Gruppe wurde geschlossen.")
        if self._active_member_count(group) >= group.max_members:
            group.status = GROUP_STATUS_FULL
            raise GroupFullError("Diese Gruppe ist bereits voll.")
        if actor and self._find_user_participation(group, actor.id):
            raise GroupPermissionError("Du bist bereits für diese Gruppe angemeldet.")
        if group.min_ship_rate is not None:
            chosen_rate = self._resolve_payload_rate(payload)
            if actor is None and chosen_rate is None:
                raise GroupPermissionError("Bitte gib für den Gast-Beitritt eine Schiffsrate an.")
            if chosen_rate is not None and chosen_rate > group.min_ship_rate:
                raise GroupPermissionError("Das ausgewählte Schiff erfüllt die Mindest-Rate nicht.")

    def _resolve_payload_rate(self, payload: GroupParticipantCreate) -> int | None:
        if payload.ship_id:
            ship = self.ships.get(payload.ship_id)
            if ship:
                return self._parse_rate(ship.rate)
        return payload.custom_ship_rate

    @staticmethod
    def _ensure_ship_rate_allowed(rate: int | None) -> None:
        if rate is not None and not 1 <= rate <= 7:
            raise GroupPermissionError("Die Mindest-Schiffsrate muss zwischen 1 und 7 liegen.")

    def _expire_groups_if_needed(self, groups: list[Group]) -> bool:
        changed = False
        for group in groups:
            changed = self._expire_group_if_needed(group) or changed
        return changed

    def _expire_group_if_needed(self, group: Group) -> bool:
        if not group.active or group.status not in {GROUP_STATUS_OPEN, GROUP_STATUS_FULL}:
            return False
        if not group.expires_at:
            return False
        if self._as_aware(group.expires_at) > self._now():
            return False
        now = self._now()
        group.status = GROUP_STATUS_EXPIRED
        group.active = False
        group.closed_at = now
        group.archived_at = now
        return True

    def _refresh_statuses(self, groups: list[Group]) -> bool:
        changed = False
        for group in groups:
            changed = self._refresh_group_status(group) or changed
        return changed

    def _refresh_group_status(self, group: Group) -> bool:
        if not group.active or group.status in {GROUP_STATUS_CLOSED, GROUP_STATUS_EXPIRED}:
            return False
        old_status = group.status
        group.status = GROUP_STATUS_FULL if self._active_member_count(group) >= group.max_members else GROUP_STATUS_OPEN
        return old_status != group.status

    @staticmethod
    def _active_members(group: Group) -> list[GroupParticipant]:
        return [participant for participant in group.participants if participant.active and participant.status == "member"]

    def _active_member_count(self, group: Group) -> int:
        return len(self._active_members(group))

    @staticmethod
    def _can_manage(group: Group, actor: User | None) -> bool:
        return bool(actor and (actor.role == "admin" or group.owner_id == actor.id))

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _find_user_participation(group: Group, user_id: int) -> GroupParticipant | None:
        return next(
            (participant for participant in group.participants if participant.active and participant.user_id == user_id),
            None,
        )

    @staticmethod
    def _find_display_name_participation(group: Group, display_name: str) -> GroupParticipant | None:
        normalized = display_name.casefold()
        return next(
            (
                participant
                for participant in group.participants
                if participant.active and participant.display_name.casefold() == normalized
            ),
            None,
        )

    @staticmethod
    def _create_join_token() -> str:
        return token_urlsafe(32)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_rate(rate: str | int | None) -> int | None:
        if rate is None:
            return None
        if isinstance(rate, int):
            return rate

        normalized = str(rate).strip().upper()
        roman_rates = {
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
        }
        if normalized in roman_rates:
            return roman_rates[normalized]

        digits = "".join(char for char in normalized if char.isdigit())
        return int(digits) if digits else None

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _as_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _join_reason(self, group: Group, *, viewer: User | None, is_joined: bool) -> str | None:
        if is_joined:
            return "Du bist bereits angemeldet."
        if not group.active:
            return "Diese Gruppe ist nicht mehr aktiv."
        if group.status == GROUP_STATUS_EXPIRED:
            return "Diese Gruppe ist abgelaufen."
        if group.status == GROUP_STATUS_CLOSED:
            return "Diese Gruppe wurde geschlossen."
        if group.status == GROUP_STATUS_FULL or self._active_member_count(group) >= group.max_members:
            return "Diese Gruppe ist voll."
        if viewer is None and not group.allow_anonymous:
            return "Anonyme Teilnahme ist für diese Gruppe deaktiviert."
        return None

    def _to_read(
        self,
        group: Group,
        *,
        viewer: User | None = None,
        guest_join_token: str | None = None,
        guest_display_name: str | None = None,
    ) -> GroupRead:
        active_members = self._active_members(group)
        members = [p.display_name for p in active_members]
        waiting_list: list[str] = []
        user_participation = self._find_user_participation(group, viewer.id) if viewer else None
        is_joined = user_participation is not None or guest_display_name is not None
        active_count = len(active_members)
        is_full = active_count >= group.max_members
        can_manage = self._can_manage(group, viewer)
        can_join_reason = self._join_reason(group, viewer=viewer, is_joined=is_joined)
        can_join = can_join_reason is None

        return GroupRead(
            id=group.id,
            owner_id=group.owner_id,
            owner_name=group.owner.display_name if group.owner else None,
            title=group.title,
            description=group.description,
            focus=group.focus,
            focus_label=FOCUS_LABELS.get(group.focus, group.focus),
            ship_id=group.ship_id,
            ship_name=group.ship.name if group.ship else None,
            ship_class=group.ship.ship_class if group.ship else group.ship_class_label,
            rate=group.ship.rate if group.ship else None,
            max_members=group.max_members,
            min_ship_rate=group.min_ship_rate,
            allow_anonymous=group.allow_anonymous,
            fleet_restriction=group.fleet_restriction,
            scheduled_at=group.scheduled_at,
            created_at=group.created_at,
            expires_at=group.expires_at,
            closed_at=group.closed_at,
            archived_at=group.archived_at,
            status=group.status,
            status_label=STATUS_LABELS.get(group.status, group.status),
            active=group.active,
            members=members,
            waiting_list=waiting_list,
            participants=[
                GroupParticipantRead(
                    id=participant.id,
                    display_name=participant.display_name,
                    status=participant.status,
                    participant_role=participant.participant_role,
                    is_anonymous=participant.is_anonymous,
                    fleet_name=participant.fleet_name,
                    ship_id=participant.ship_id,
                    ship_name=participant.ship.name if participant.ship else None,
                    ship_rate=participant.ship.rate if participant.ship else None,
                    custom_ship_name=participant.custom_ship_name,
                    custom_ship_rate=participant.custom_ship_rate,
                    note=participant.note if can_manage else None,
                    active=participant.active,
                    joined_at=participant.joined_at,
                    left_at=participant.left_at,
                    join_token=None,
                )
                for participant in group.participants
                if participant.active or can_manage
            ],
            participant_count=active_count,
            free_slots=max(group.max_members - active_count, 0),
            is_full=is_full,
            is_joined=is_joined,
            can_join=can_join,
            can_join_reason=can_join_reason,
            can_manage=can_manage,
            guest_join_token=guest_join_token,
        )
