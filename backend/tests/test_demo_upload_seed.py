from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.seeds.demo_content import _copy_demo_file
from main import app


def test_demo_assets_are_copied_into_configured_upload_directory() -> None:
    size = _copy_demo_file("demo/line-battle.svg")
    target = Path(settings.upload_dir) / "demo" / "line-battle.svg"
    assert size > 0
    assert target.is_file()
    assert target.stat().st_size == size

    with TestClient(app) as client:
        response = client.get("/uploads/demo/line-battle.svg")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/svg+xml")


def test_seed_service_mounts_persistent_upload_volume() -> None:
    compose = Path(__file__).resolve().parents[2] / "infrastructure" / "compose.yml"
    text = compose.read_text(encoding="utf-8")
    seed_block = text.split("  seed:\n", 1)[1].split("  api:\n", 1)[0]
    assert "./data/uploads:/data/uploads" in seed_block


def test_demo_assets_live_inside_versioned_source_tree() -> None:
    seed_dir = Path(__file__).resolve().parents[1] / "src" / "app" / "seeds"
    for filename in ("line-battle.svg", "trade-convoy.svg"):
        asset = seed_dir / "assets" / "demo" / filename
        assert asset.is_file(), f"Missing versioned demo asset: {asset}"
        assert asset.stat().st_size > 0

    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY storage ./storage" not in dockerfile
    assert "COPY src ./src" in dockerfile
