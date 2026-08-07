from infrastructure.scripts.generation import generate_spring_routes as routes


def multipart_operations():
    result = []
    for path, item in routes.SCHEMA["paths"].items():
        for method, operation in item.items():
            if method not in routes.HTTP:
                continue
            content = operation.get("requestBody", {}).get("content", {})
            if "multipart/form-data" in content:
                result.append((path, method, operation))
    return result


def test_multipart_contract_documents_transport_rejection():
    operations = multipart_operations()

    assert len(operations) == 2
    for path, method, operation in operations:
        assert "415" in operation["responses"], f"{method.upper()} {path} must document wrong content type"
        schema = operation["responses"]["415"]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ApiError"}


def test_generated_multipart_routes_declare_consumes_media_type():
    outputs, operation_count = routes.render_outputs()

    assert operation_count == 177
    for path, method, _ in multipart_operations():
        group = routes.group_for(path)
        class_name = routes.camel(group, upper=True) + "Api"
        source = outputs[routes.TARGET / f"{class_name}.java"]
        mapping = routes.HTTP[method]
        expected = (
            f'@{mapping}(value = "{path}", '
            'consumes = MediaType.MULTIPART_FORM_DATA_VALUE)'
        )
        assert expected in source
