from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import Profile, User
from app.repositories import UserRepository
from app.schemas.auth import AuthResponse, AuthUser, RegisterRequest
from app.services.auth.auth_error import AuthError
from app.services.auth.username_already_exists_error import UsernameAlreadyExistsError


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> AuthResponse:
        user = self.users.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Ungültige Zugangsdaten.")

        return self._to_auth_response(user)

    def register(self, payload: RegisterRequest) -> AuthResponse:
        if self.users.get_by_username(payload.username):
            raise UsernameAlreadyExistsError("Benutzername ist bereits vergeben.")

        display_name = payload.display_name or payload.username
        user = self.users.create(
            User(
                username=payload.username,
                password_hash=hash_password(payload.password),
                display_name=display_name,
                role="member",
            )
        )
        self.db.add(
            Profile(
                user_id=user.id,
                main_role="Kapitän",
                fleet_name="Ohne Flotte",
                bio="",
            )
        )
        self.db.commit()
        refreshed = self.users.get_by_username(payload.username)
        assert refreshed is not None
        return self._to_auth_response(refreshed)

    @staticmethod
    def to_auth_user(user: User) -> AuthUser:
        return AuthUser(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            is_admin=user.role == "admin",
        )

    @classmethod
    def _to_auth_response(cls, user: User) -> AuthResponse:
        return AuthResponse(
            access_token=create_access_token(user.id),
            user=cls.to_auth_user(user),
        )
