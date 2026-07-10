from pathlib import Path

from app.core.runtime_paths import normalize_database_url, resolve_runtime_path


def test_relative_runtime_path_is_resolved_against_backend_root(tmp_path: Path) -> None:
    result = resolve_runtime_path(
        "storage/uploads",
        base_dir=tmp_path,
        setting_name="UPLOAD_DIR",
    )

    assert result == (tmp_path / "storage" / "uploads").resolve()


def test_relative_sqlite_url_is_normalized_and_parent_is_created(tmp_path: Path) -> None:
    result = normalize_database_url("sqlite:///./storage/wosb.db", base_dir=tmp_path)

    expected_database = (tmp_path / "storage" / "wosb.db").resolve().as_posix()
    assert result == f"sqlite:///{expected_database}"
    assert (tmp_path / "storage").is_dir()


def test_non_sqlite_url_is_left_unchanged(tmp_path: Path) -> None:
    original = "postgresql://user:secret@example.invalid/app"

    assert normalize_database_url(original, base_dir=tmp_path) == original
