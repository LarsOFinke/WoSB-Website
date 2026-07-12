from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.accounts.models.user import ROLE_USER, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.seeds.manager import SeedManager
from main import app


OWNER_USERNAME = "build-edit-limit-owner"
OWNER_PASSWORD = "BuildEditLimitOwner123!"
OTHER_USERNAME = "build-edit-limit-other"
OTHER_PASSWORD = "BuildEditLimitOther123!"


def _ensure_user(username: str, password: str, display_name: str) -> User:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            return existing
        return create_user(
            db,
            username=username,
            password=password,
            display_name=display_name,
            role=ROLE_USER,
        )


def _prepare_catalog() -> int:
    register_all_models()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed = SeedManager(db)
        seed.seed_role_catalog()
        seed.seed_weapon_slot_types()
        seed.seed_ships()
        seed.seed_build_options()
        anson = db.scalar(select(Ship).where(Ship.name == "Anson"))
        assert anson is not None
        return anson.id


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def _anson_payload(ship_id: int, *, name: str = "Editable Anson") -> dict[str, object]:
    return {
        "build_name": name,
        "build_type": "balanced",
        "ship_id": ship_id,
        "sailors": 80,
        "soldiers": 80,
        "special_crew_slots": [{"item": "Doctor", "quantity": 1}],
        "hold_slots": [{"item": "Tackles", "quantity": 1}],
    }


def test_doctor_keeps_anson_at_160_crew_and_owner_can_edit_build() -> None:
    ship_id = _prepare_catalog()
    owner = _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")
    _ensure_user(OTHER_USERNAME, OTHER_PASSWORD, "Build Edit Other")

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        created = client.post("/api/builds", json=_anson_payload(ship_id))
        assert created.status_code == 201, created.text
        body = created.json()
        build_id = body["id"]
        assert body["owner_id"] == owner.id
        assert body["ship"]["crew_capacity"] == 160
        assert body["ship"]["sailor_minimum"] == 80
        assert body["ship_stats"]["sailor_target"] == 80
        assert body["ship_stats"]["sailing_efficiency_pct"] == 100
        assert body["ship_stats"]["crew_capacity"] == 160
        assert body["ship_stats"]["crew_total"] == 160
        assert body["ship_stats"]["special_crew_effects"] == {
            "boarding_company_shelling_survivability_pct": 40
        }
        assert body["special_crew_slots"] == [{"item": "Doctor", "quantity": 1}]
        assert body["hold_slots"] == [{"item": "Tackles", "quantity": 1}]

        updated_payload = _anson_payload(ship_id, name="Edited Anson")
        updated_payload["details"] = "Updated through the build editor."
        updated = client.put(f"/api/builds/mine/{build_id}", json=updated_payload)
        assert updated.status_code == 200, updated.text
        assert updated.json()["build_name"] == "Edited Anson"
        assert updated.json()["details"] == "Updated through the build editor."
        assert updated.json()["ship_stats"]["crew_capacity"] == 160
        _logout(client)

        _login(client, OTHER_USERNAME, OTHER_PASSWORD)
        denied = client.put(f"/api/builds/mine/{build_id}", json=updated_payload)
        assert denied.status_code == 404


def test_doctor_does_not_create_six_extra_crew_places() -> None:
    ship_id = _prepare_catalog()
    _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        response = client.post(
            "/api/builds",
            json={
                "build_name": "Doctor is not crew capacity",
                "ship_id": ship_id,
                "sailors": 80,
                "soldiers": 86,
                "special_crew_slots": [{"item": "Doctor", "quantity": 1}],
            },
        )
        assert response.status_code == 400
        assert "effective ship capacity (160)" in response.json()["detail"]


def test_first_mate_scales_speed_with_assigned_sailors() -> None:
    ship_id = _prepare_catalog()
    _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        response = client.post(
            "/api/builds",
            json={
                "build_name": "First Mate sailor scaling",
                "ship_id": ship_id,
                "sailors": 80,
                "soldiers": 80,
                "special_crew_slots": [{"item": "First Mate", "quantity": 1}],
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["ship_stats"]["special_crew_effects"]["speed_pct"] == 16
        base_speed = float(body["ship_stats"]["base_stats"]["speed_knots"])
        assert body["ship_stats"]["effective_stats"]["speed_knots"] == round(base_speed * 1.16, 1)


def test_specialist_quantity_is_normalized_and_weapon_capacity_is_enforced() -> None:
    ship_id = _prepare_catalog()
    _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)

        specialist_payload = {
            "build_name": "Specialist quantity is ignored",
            "ship_id": ship_id,
            "sailors": 80,
            "special_crew_slots": [{"item": "Doctor", "quantity": 9}],
        }
        specialist_response = client.post("/api/builds", json=specialist_payload)
        assert specialist_response.status_code == 201, specialist_response.text
        assert specialist_response.json()["special_crew_slots"] == [{"item": "Doctor", "quantity": 1}]

        weapon_payload = {
            "build_name": "Too many bow weapons",
            "ship_id": ship_id,
            "sailors": 80,
            "front_weapon_slots": [{"item": "Twin 14-pdr", "quantity": 5}],
        }
        weapon_response = client.post("/api/builds", json=weapon_payload)
        assert weapon_response.status_code == 400
        assert "exceeds this ship's capacity (4)" in weapon_response.json()["detail"]


def test_anson_sailor_minimum_blocks_too_few_but_not_additional_sailors() -> None:
    ship_id = _prepare_catalog()
    _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        below_minimum = {
            "build_name": "Anson below sailor minimum",
            "ship_id": ship_id,
            "sailors": 40,
            "soldiers": 120,
        }
        response = client.post("/api/builds", json=below_minimum)
        assert response.status_code == 400
        assert "required minimum (80)" in response.json()["detail"]

        above_minimum = {
            "build_name": "Anson above sailor minimum",
            "ship_id": ship_id,
            "sailors": 100,
            "soldiers": 60,
        }
        accepted = client.post("/api/builds", json=above_minimum)
        assert accepted.status_code == 201, accepted.text
        assert accepted.json()["ship_stats"]["sailor_minimum"] == 80
        assert accepted.json()["ship_stats"]["sailing_efficiency_pct"] == 100
        assert accepted.json()["ship_stats"]["crew_total"] == 160

