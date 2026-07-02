from sqlalchemy.orm import Session

from app.repositories import ProfileRepository, ShipRepository, UserRepository
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.profile.profile_not_found_error import ProfileNotFoundError


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.profiles = ProfileRepository(db)
        self.users = UserRepository(db)
        self.ships = ShipRepository(db)

    def get_profile(self, *, user_id: int = 1) -> ProfileRead:
        profile = self.profiles.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError("Profil nicht gefunden.")
        return self._to_read(profile)

    def update_profile(self, payload: ProfileUpdate, *, user_id: int = 1) -> ProfileRead:
        profile = self.profiles.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError("Profil nicht gefunden.")

        data = payload.model_dump(exclude_unset=True)
        if "display_name" in data and payload.display_name is not None:
            profile.user.display_name = payload.display_name
        if "main_role" in data and payload.main_role is not None:
            profile.main_role = payload.main_role
        if "fleet" in data and payload.fleet is not None:
            profile.fleet_name = payload.fleet
        if "bio" in data and payload.bio is not None:
            profile.bio = payload.bio
        if "preferred_ship_id" in data:
            ship = self.ships.get(payload.preferred_ship_id) if payload.preferred_ship_id else None
            profile.preferred_ship_id = ship.id if ship else None

        self.db.commit()
        refreshed = self.profiles.get_by_user_id(user_id)
        assert refreshed is not None
        return self._to_read(refreshed)

    @staticmethod
    def _to_read(profile) -> ProfileRead:
        return ProfileRead(
            user_id=profile.user_id,
            display_name=profile.user.display_name,
            main_role=profile.main_role,
            fleet=profile.fleet_name,
            bio=profile.bio,
            preferred_ship_id=profile.preferred_ship_id,
            preferred_ship_name=profile.preferred_ship.name if profile.preferred_ship else None,
        )
