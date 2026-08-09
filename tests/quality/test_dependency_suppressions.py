from infrastructure.scripts.quality.check_dependency_suppressions import fixed_versions, validate_policy


def cve_record(*matches):
    return {"configurations": [{"nodes": [{"cpeMatch": list(matches)}]}]}


def match(criteria, **bounds):
    return {"criteria": criteria, "vulnerable": True, **bounds}


def test_fixed_versions_reads_nvd_version_range():
    record = cve_record(match("cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*", versionEndExcluding="11.0.25"))
    assert fixed_versions(record, "apache", "tomcat") == {"11.0.25"}


def test_fixed_versions_ignores_other_products_and_non_vulnerable_matches():
    record = cve_record(
        match("cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*", vulnerable=False, versionEndExcluding="11.0.25"),
        match("cpe:2.3:a:other:tomcat:*:*:*:*:*:*:*:*", versionEndExcluding="11.0.25"),
    )
    assert fixed_versions(record, "apache", "tomcat") == set()


def test_policy_fails_when_nvd_reports_newer_fix():
    policy = {"policies": [{"cve": "CVE-1", "vendor": "apache", "product": "tomcat",
                             "current_version": "11.0.24", "action": "allow-unfixed-only"}]}
    record = cve_record(match("cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*", versionEndExcluding="11.0.25"))
    assert validate_policy(policy, None, lambda cve, key: {"vulnerabilities": [{"cve": record}]}) == [
        "CVE-1: NVD reports a patched version (11.0.25)"
    ]


def test_policy_allows_suppression_when_no_fix_is_recorded():
    policy = {"policies": [{"cve": "CVE-1", "vendor": "apache", "product": "tomcat",
                             "current_version": "11.0.24", "action": "allow-unfixed-only"}]}
    assert validate_policy(policy, None, lambda cve, key: {"vulnerabilities": [{"cve": {}}]}) == []


def test_policy_allows_nvd_fix_while_fixed_maven_artifact_is_unavailable():
    policy = {"policies": [{
        "cve": "CVE-1", "vendor": "apache", "product": "tomcat",
        "package_url": "pkg:maven/org.apache.tomcat.embed/tomcat-embed-websocket@11.0.24",
        "current_version": "11.0.24", "action": "allow-unfixed-only",
        "availability": {"type": "maven", "repository": "https://repo.example.invalid/maven2"},
    }]}
    record = cve_record(match("cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*", versionEndExcluding="11.0.25"))
    assert validate_policy(
        policy, None, lambda cve, key: {"vulnerabilities": [{"cve": record}]},
        lambda package, version, repository: False,
    ) == []


def test_policy_fails_when_nvd_fix_is_fetchable():
    policy = {"policies": [{
        "cve": "CVE-1", "vendor": "apache", "product": "tomcat",
        "package_url": "pkg:maven/org.apache.tomcat.embed/tomcat-embed-websocket@11.0.24",
        "current_version": "11.0.24", "action": "allow-unfixed-only",
        "availability": {"type": "maven", "repository": "https://repo.example.invalid/maven2"},
    }]}
    record = cve_record(match("cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*", versionEndExcluding="11.0.25"))
    assert validate_policy(
        policy, None, lambda cve, key: {"vulnerabilities": [{"cve": record}]},
        lambda package, version, repository: True,
    ) == ["CVE-1: NVD reports a fetchable patched version (11.0.25)"]
