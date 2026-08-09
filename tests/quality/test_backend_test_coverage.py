from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.scripts.quality import check_backend_test_coverage as audit


def _java(path: Path, name: str = "Probe.java") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text("final class Probe {}\n", encoding="utf-8")


def test_module_inventory_discovers_only_java_backed_modules(tmp_path):
    _java(tmp_path / "account")
    (tmp_path / "empty").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "note.txt").write_text("x", encoding="utf-8")

    assert audit.module_names(tmp_path) == {"account"}


def test_require_fails_closed_with_backend_test_prefix():
    with pytest.raises(SystemExit, match=r"^\[backend-tests\] missing coverage$"):
        audit.require(False, "missing coverage")


def test_business_inventory_includes_components_outside_direct_service_packages():
    components = {path.relative_to(audit.MAIN).as_posix() for path in audit.business_component_sources()}

    assert "persistence/JdbcQueryService.java" in components
    assert "dto/CookieConsentPolicy.java" not in components
    assert any(path.endswith("Service.java") for path in components)
    assert any(path.endswith("Policy.java") for path in components)


def test_documented_go_live_floors_remain_strict_and_exclusions_stay_narrow():
    pom = audit.POM.read_text(encoding="utf-8")

    assert "<coverage.line.minimum>0.80</coverage.line.minimum>" in pom
    assert "<coverage.branch.minimum>0.65</coverage.branch.minimum>" in pom
    assert "<coverage.method.minimum>0.80</coverage.method.minimum>" in pom
    assert "<coverage.package.line.minimum>0.60</coverage.package.line.minimum>" in pom
    assert "<counter>CLASS</counter>" in pom
    assert "<value>MISSEDCOUNT</value>" in pom
    assert "<maximum>0</maximum>" in pom
    assert "<exclude>eu/royalblackwater/api/dto/**</exclude>" in pom
    assert "<exclude>**/repository/queries/**</exclude>" in pom
    assert "<exclude>**/dto/**</exclude>" not in pom
    assert "<exclude>**/entity/**</exclude>" not in pom
    assert "<exclude>**/*Application*</exclude>" not in pom
