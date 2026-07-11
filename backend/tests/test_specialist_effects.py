from app.modules.builds.services.specialist_effect_service import resolve_specialist_effects


def test_specialist_effects_expand_per_sailor_and_per_boarder_values() -> None:
    effects = resolve_specialist_effects(
        [
            ({"speed_per_sailor_pct": 0.2}, 1),
            ({"boarding_cargo_weight_per_boarder_pct": 0.5}, 1),
            ({"reload_pct": 4}, 2),
        ],
        sailors=80,
        soldiers=40,
        musketeers=20,
        mercenaries=10,
    )

    assert effects == {
        "speed_pct": 16,
        "boarding_cargo_weight_pct": 35,
        "reload_pct": 8,
    }


def test_specialist_boolean_effects_do_not_stack() -> None:
    effects = resolve_specialist_effects(
        [({"steady_course_enabled": 1}, 4)],
        sailors=0,
        soldiers=0,
        musketeers=0,
        mercenaries=0,
    )

    assert effects == {"steady_course_enabled": 1}
