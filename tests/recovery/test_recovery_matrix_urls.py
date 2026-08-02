from scripts.test_recovery_matrix import admin_database, database_url


def test_recovery_matrix_preserves_database_password() -> None:
    base = "postgresql+psycopg://rbf_ci:rbf_ci_password@127.0.0.1:5432/rbf_ci"

    target = database_url(base, "rbf_recovery_source_42")
    admin = admin_database(base)

    assert "rbf_ci_password" in target
    assert "rbf_ci_password" in admin
    assert "***" not in target
    assert target.endswith("/rbf_recovery_source_42")
    assert admin.endswith("/postgres")
