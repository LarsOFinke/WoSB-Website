from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.accounts.models.user import ROLE_USER, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.builds.models.build_file_attachment import BuildFileAttachment
from app.modules.files.models.file_asset import StoredFile
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.bootstrap.manager import SeedManager
from app.core.config import settings
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


def test_build_printout_is_public_deduplicated_and_replaced_in_place() -> None:
    ship_id = _prepare_catalog()
    _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")
    _ensure_user(OTHER_USERNAME, OTHER_PASSWORD, "Build Edit Other")
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    first_png = png_header + b"first-printout"
    second_png = png_header + b"changed-printout"

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        created = client.post("/api/builds", json=_anson_payload(ship_id, name="Public printout"))
        build_id = created.json()["id"]
        endpoint = f"/api/builds/{build_id}/printout"

        published = client.put(endpoint, files={"image": ("build.png", first_png, "image/png")})
        assert published.status_code == 200, published.text
        assert published.json()["changed"] is True
        checksum = published.json()["checksum"]

        duplicate = client.put(endpoint, files={"image": ("build.png", first_png, "image/png")})
        assert duplicate.status_code == 200, duplicate.text
        assert duplicate.json()["changed"] is False
        assert duplicate.json()["checksum"] == checksum

        _logout(client)
        public = client.get(endpoint)
        assert public.status_code == 200
        assert public.content == first_png
        assert public.headers["etag"] == f'"{checksum}"'

        _login(client, OTHER_USERNAME, OTHER_PASSWORD)
        denied = client.put(endpoint, files={"image": ("build.png", second_png, "image/png")})
        assert denied.status_code == 403
        _logout(client)

        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        replaced = client.put(endpoint, files={"image": ("build.png", second_png, "image/png")})
        assert replaced.status_code == 200, replaced.text
        assert replaced.json()["changed"] is True
        assert client.get(endpoint).content == second_png
        printout_dir = Path(settings.upload_dir) / "build-printouts"
        assert [path.name for path in printout_dir.glob(f"build-{build_id}*.png")] == [
            f"build-{build_id}.png"
        ]

        attached_path = Path(settings.upload_dir) / "build-files" / str(build_id) / "notes.txt"
        attached_path.parent.mkdir(parents=True, exist_ok=True)
        attached_path.write_text("build-owned attachment", encoding="utf-8")
        with SessionLocal() as db:
            stored_file = StoredFile(
                owner_id=None,
                original_name="notes.txt",
                stored_name=f"build-{build_id}-notes.txt",
                relative_path=str(attached_path.relative_to(Path(settings.upload_dir))),
                mime_type="text/plain",
                size_bytes=attached_path.stat().st_size,
                usage_context="general",
                is_public=False,
            )
            db.add(stored_file)
            db.flush()
            file_id = stored_file.id
            db.add(BuildFileAttachment(build_id=build_id, file_id=file_id))
            db.commit()

        second_build = client.post(
            "/api/builds", json=_anson_payload(ship_id, name="Shared file owner")
        )
        second_build_id = second_build.json()["id"]
        shared_path = attached_path.with_name("shared.txt")
        shared_path.write_text("shared build attachment", encoding="utf-8")
        with SessionLocal() as db:
            shared_file = StoredFile(
                owner_id=None,
                original_name="shared.txt",
                stored_name=f"build-{build_id}-shared.txt",
                relative_path=str(shared_path.relative_to(Path(settings.upload_dir))),
                mime_type="text/plain",
                size_bytes=shared_path.stat().st_size,
                usage_context="general",
                is_public=False,
            )
            db.add(shared_file)
            db.flush()
            shared_file_id = shared_file.id
            db.add_all(
                [
                    BuildFileAttachment(build_id=build_id, file_id=shared_file_id),
                    BuildFileAttachment(build_id=second_build_id, file_id=shared_file_id),
                ]
            )
            db.commit()

        deleted = client.delete(f"/api/builds/mine/{build_id}")
        assert deleted.status_code == 204
        assert client.get(endpoint).status_code == 404
        assert not attached_path.exists()
        with SessionLocal() as db:
            assert db.get(StoredFile, file_id) is None
            assert db.get(StoredFile, shared_file_id) is not None
        assert shared_path.exists()


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


def test_first_mate_scales_sail_deployment_without_changing_ship_speed() -> None:
    ship_id = _prepare_catalog()
    _ensure_user(OWNER_USERNAME, OWNER_PASSWORD, "Build Edit Owner")

    with TestClient(app) as client:
        _login(client, OWNER_USERNAME, OWNER_PASSWORD)
        response = client.post(
            "/api/builds",
            json={
                "build_name": "First Mate sail deployment",
                "ship_id": ship_id,
                "sailors": 80,
                "soldiers": 80,
                "special_crew_slots": [{"item": "First Mate", "quantity": 1}],
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["ship_stats"]["special_crew_effects"] == {"sail_deployment_speed_pct": 16}
        base_cruise_max = float(body["ship_stats"]["base_stats"]["speed_knots"])
        assert body["ship_stats"]["effective_stats"]["speed_knots"] == base_cruise_max
        deployment_row = next(
            row
            for row in body["ship_stats"]["stat_rows"]
            if row["key"] == "sail_deployment_speed_pct"
        )
        assert deployment_row["modifier"] == 16


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
        assert specialist_response.json()["special_crew_slots"] == [
            {"item": "Doctor", "quantity": 1}
        ]

        weapon_payload = {
            "build_name": "Too many bow weapons",
            "ship_id": ship_id,
            "sailors": 80,
            "front_weapon_slots": [{"item": "Twin 14-pdr", "quantity": 3}],
        }
        weapon_response = client.post("/api/builds", json=weapon_payload)
        assert weapon_response.status_code == 400
        assert "exceeds this ship's capacity (2)" in weapon_response.json()["detail"]


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


def test_build_collection_endpoints_are_paginated_and_use_lightweight_summaries() -> None:
    ship_id = _prepare_catalog()
    username = "build-page-owner"
    password = "BuildPageOwner123!"
    _ensure_user(username, password, "Build Page Owner")

    with TestClient(app) as client:
        _login(client, username, password)
        for index in range(3):
            response = client.post(
                "/api/builds",
                json=_anson_payload(ship_id, name=f"Pagination Regression {index}"),
            )
            assert response.status_code == 201, response.text

        first = client.get(
            "/api/builds",
            params={"search": "Pagination Regression", "limit": 2, "offset": 0},
        )
        assert first.status_code == 200, first.text
        first_page = first.json()
        assert first_page["total"] == 3
        assert first_page["limit"] == 2
        assert first_page["offset"] == 0
        assert len(first_page["items"]) == 2
        assert "ship_stats" not in first_page["items"][0]
        assert first_page["items"][0]["metrics"]["crew_total"] == 160

        second = client.get(
            "/api/builds/mine",
            params={"search": "Pagination Regression", "limit": 2, "offset": 2},
        )
        assert second.status_code == 200, second.text
        second_page = second.json()
        assert second_page["total"] == 3
        assert second_page["offset"] == 2
        assert len(second_page["items"]) == 1

        assert client.get("/api/builds", params={"limit": 101}).status_code == 422
