from fastapi.testclient import TestClient
from sqlalchemy import select

from app.bootstrap.manager import SeedManager
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.accounts.models.user import ROLE_MODERATOR, ROLE_USER, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from main import app


def _user(username: str, password: str, role: str = ROLE_USER) -> User:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing:
            return existing
        return create_user(db, username=username, password=password, display_name=username, role=role)


def _catalog() -> int:
    register_all_models()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed = SeedManager(db)
        seed.seed_role_catalog()
        seed.seed_weapon_slot_types()
        seed.seed_ships()
        seed.seed_build_options()
        ship = db.scalar(select(Ship).where(Ship.name == "Anson"))
        assert ship is not None
        return ship.id


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    assert client.post("/api/auth/logout").status_code == 204


def _payload(ship_id: int, name: str) -> dict[str, object]:
    return {"build_name": name, "build_type": "balanced", "ship_id": ship_id, "sailors": 80}


def test_registered_users_have_exactly_one_upvote_per_build() -> None:
    ship_id = _catalog()
    _user("vote-owner", "VoteOwnerPassword123!")
    _user("vote-member-one", "VoteMemberOne123!")
    _user("vote-member-two", "VoteMemberTwo123!")

    with TestClient(app) as client:
        _login(client, "vote-owner", "VoteOwnerPassword123!")
        created = client.post("/api/builds", json=_payload(ship_id, "Vote target"))
        assert created.status_code == 201, created.text
        build_id = created.json()["id"]
        _logout(client)

        _login(client, "vote-member-one", "VoteMemberOne123!")
        first = client.post(f"/api/builds/{build_id}/upvote")
        assert first.status_code == 200
        assert first.json() == {"build_id": build_id, "upvote_count": 1, "has_upvoted": True}
        duplicate = client.post(f"/api/builds/{build_id}/upvote")
        assert duplicate.status_code == 200
        assert duplicate.json()["upvote_count"] == 1
        detail = client.get(f"/api/builds/{build_id}").json()
        assert detail["upvote_count"] == 1
        assert detail["has_upvoted"] is True
        _logout(client)

        _login(client, "vote-member-two", "VoteMemberTwo123!")
        second = client.post(f"/api/builds/{build_id}/upvote")
        assert second.json()["upvote_count"] == 2
        overview = client.get("/api/builds").json()
        row = next(item for item in overview["items"] if item["id"] == build_id)
        assert row["upvote_count"] == 2
        assert row["has_upvoted"] is True
        removed = client.delete(f"/api/builds/{build_id}/upvote")
        assert removed.json()["upvote_count"] == 1
        removed_again = client.delete(f"/api/builds/{build_id}/upvote")
        assert removed_again.json()["upvote_count"] == 1


def test_moderator_can_crud_roles_and_assign_them_to_builds() -> None:
    ship_id = _catalog()
    _user("role-owner", "RoleOwnerPassword123!")
    _user("role-moderator", "RoleModerator123!", ROLE_MODERATOR)

    with TestClient(app) as client:
        _login(client, "role-owner", "RoleOwnerPassword123!")
        created = client.post("/api/builds", json=_payload(ship_id, "Role target"))
        assert created.status_code == 201, created.text
        build_id = created.json()["id"]
        _logout(client)

        _login(client, "role-moderator", "RoleModerator123!")
        created_role = client.post("/api/admin/build-roles", json={
            "slug": "support",
            "label": "Support",
            "description": "Fleet support role",
            "sort_order": 50,
        })
        assert created_role.status_code == 201, created_role.text
        updated = client.put("/api/admin/build-roles/support", json={
            "label": "Fleet Support",
            "description": "Support and logistics",
            "sort_order": 15,
        })
        assert updated.status_code == 200, updated.text
        assert updated.json()["label"] == "Fleet Support"

        assigned = client.put(f"/api/admin/builds/{build_id}/role", json={"build_type": "support"})
        assert assigned.status_code == 200, assigned.text
        assert assigned.json()["build_type"] == "support"
        assert assigned.json()["build_role_label"] == "Fleet Support"

        in_use = client.delete("/api/admin/build-roles/support")
        assert in_use.status_code == 400
        assert "assigned" in in_use.json()["detail"]

        reassigned = client.put(f"/api/admin/builds/{build_id}/role", json={"build_type": "balanced"})
        assert reassigned.status_code == 200
        assert client.delete("/api/admin/build-roles/support").status_code == 204
        slugs = {role["slug"] for role in client.get("/api/admin/build-roles").json()}
        assert "support" not in slugs
