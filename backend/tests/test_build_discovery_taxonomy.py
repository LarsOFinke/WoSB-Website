import pytest
from pydantic import ValidationError

from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_limits import regular_specialist_count
from app.modules.guides.schemas.guide_create import GuideCreate


def test_build_classifications_are_normalized_and_deduplicated() -> None:
    payload = BuildCreate(
        build_name="Port defender",
        ship_id=1,
        classification_tags=[" Port_Battle ", "heavy", "port_battle"],
    )
    assert payload.classification_tags == ["port_battle", "heavy"]


def test_unknown_build_classification_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BuildCreate(build_name="Unknown", ship_id=1, classification_tags=["mystery"])


def test_ginger_does_not_consume_a_regular_specialist_slot() -> None:
    assert regular_specialist_count(["Doctor", "Gunner", "Cook", "Navigator", "Ginger"]) == 4


def test_guide_category_taxonomy_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError):
        GuideCreate(title="Unknown", category="mystery", body="Body")
