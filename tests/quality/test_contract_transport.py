from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = json.loads((ROOT / "openapi/openapi.json").read_text(encoding="utf-8"))
CONTROLLERS = ROOT / "spring-api/src/main/java/eu/royalblackwater/api"
HTTP = {"get", "post", "put", "patch", "delete"}


def multipart_operations():
    result = []
    for path, item in OPENAPI["paths"].items():
        for method, operation in item.items():
            if method not in HTTP:
                continue
            content = operation.get("requestBody", {}).get("content", {})
            if "multipart/form-data" in content:
                result.append((path, method, operation))
    return result


def controller_sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in CONTROLLERS.glob("*/controller/*Controller.java")
    )


def test_multipart_contract_documents_transport_rejection():
    operations = multipart_operations()

    assert len(operations) == 2
    for path, method, operation in operations:
        assert "415" in operation["responses"], f"{method.upper()} {path} must document wrong content type"
        schema = operation["responses"]["415"]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ApiError"}


def test_controller_owned_multipart_routes_declare_consumes_media_type():
    source = controller_sources()

    for path, method, _ in multipart_operations():
        mapping = method.capitalize()
        expected = (
            f'@{mapping}Mapping(value = "{path}", '
            'consumes = MediaType.MULTIPART_FORM_DATA_VALUE)'
        )
        assert expected in source


def test_controller_layer_owns_all_openapi_routes_without_generated_api_interfaces():
    source = controller_sources()
    mappings = re.findall(r"@(Get|Post|Put|Patch|Delete)Mapping\(", source)
    expected = sum(
        1
        for item in OPENAPI["paths"].values()
        for method, operation in item.items()
        if method in HTTP and isinstance(operation, dict)
    )

    assert expected == 189
    assert len(mappings) == expected
    assert not (ROOT / "spring-api/src/main/java/eu/royalblackwater/api/contract").exists()
