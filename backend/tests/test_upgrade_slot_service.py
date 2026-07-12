from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access


def test_upgrade_slot_sources_stack_independently_to_seven() -> None:
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=6,
        research_upgrade_slot_unlocked=True,
        unlock_effect_slots=1,
    )

    assert access.base_slots == 4
    assert access.research_slots == 1
    assert access.unlock_effect_slots == 1
    assert access.ship_extra_slots == 1
    assert access.slot_5_unlocked is True
    assert access.slot_6_available is True
    assert access.slot_7_available is True
    assert access.available_slots == 7


def test_normal_ship_with_research_and_expansion_stops_at_six() -> None:
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=5,
        research_upgrade_slot_unlocked=True,
        unlock_effect_slots=1,
    )

    assert access.ship_extra_slots == 0
    assert access.slot_7_available is False
    assert access.available_slots == 6
