from pathlib import Path

from infrastructure.scripts.quality import audit_sql_runtime as audit


def write_probe(root: Path, sql_expression: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "Probe.java").write_text(
        """
        final class Probe {
            void run() {
                query(%s, Map.of("fleetId", 1));
            }
        }
        """ % sql_expression,
        encoding="utf-8",
    )


def test_named_parameter_audit_catches_merged_sql_token(tmp_path, monkeypatch):
    write_probe(tmp_path, '"select * from fleets where id=:fleetId" + "order by id"')
    monkeypatch.setattr(audit, "JAVA", tmp_path)

    issues, checked = audit.named_parameter_issues({})

    assert checked == 1
    assert len(issues) == 1
    assert "fleetIdorder" in issues[0].detail


def test_named_parameter_audit_accepts_delimited_sql_fragments(tmp_path, monkeypatch):
    write_probe(tmp_path, '"select * from fleets where id=:fleetId" + " order by id"')
    monkeypatch.setattr(audit, "JAVA", tmp_path)

    issues, checked = audit.named_parameter_issues({})

    assert checked == 1
    assert issues == []


def test_table_audit_rejects_retired_relation(tmp_path, monkeypatch):
    write_probe(tmp_path, '"select * from retired_build_items where id=:fleetId"')
    monkeypatch.setattr(audit, "JAVA", tmp_path)

    issues, checked = audit.table_reference_issues({"fleets": {"id"}}, {})

    assert checked == 1
    assert len(issues) == 1
    assert "retired_build_items" in issues[0].detail


def test_alias_column_audit_rejects_unknown_column(tmp_path, monkeypatch):
    write_probe(tmp_path, '"select f.retired_column from fleets f where f.id=:fleetId"')
    monkeypatch.setattr(audit, "JAVA", tmp_path)

    issues, checked = audit.schema_reference_issues({"fleets": {"id"}}, {})

    assert checked == 2
    assert len(issues) == 1
    assert "f.retired_column" in issues[0].detail
