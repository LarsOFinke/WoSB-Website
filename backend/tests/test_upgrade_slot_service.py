from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access


def test_all_slot_sources_stack_to_eight() -> None:
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=6,
        research_upgrade_slots=1,
        unlock_effect_slots=2,
    )

    assert access.base_slots == 4
    assert access.research_slots == 1
    assert access.unlock_effect_slots == 2
    assert access.ship_extra_slots == 1
    assert access.slot_5_unlocked is True
    assert access.slot_6_available is True
    assert access.slot_7_available is True
    assert access.slot_8_available is True
    assert access.available_slots == 8


def test_normal_ship_with_research_and_structural_expansion_reaches_seven() -> None:
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=5,
        research_upgrade_slots=1,
        unlock_effect_slots=2,
    )

    assert access.ship_extra_slots == 0
    assert access.slot_7_available is True
    assert access.slot_8_available is False
    assert access.available_slots == 7


def test_structural_expansion_alone_adds_both_tooltip_slots() -> None:
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=5,
        unlock_effect_slots=2,
    )

    assert access.available_slots == 6
    assert access.slot_6_available is True
    assert access.slot_7_available is False


def test_ship_without_upgrade_rack_stays_at_zero() -> None:
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=0,
        research_upgrade_slots=1,
        unlock_effect_slots=2,
    )

    assert access.base_slots == 0
    assert access.research_slots == 0
    assert access.unlock_effect_slots == 0
    assert access.available_slots == 0
    assert access.slot_5_unlocked is False
