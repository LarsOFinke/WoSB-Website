package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.dto.BuildCatalogOption;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.builds.dto.BuildSlotSelection;
import eu.royalblackwater.api.builds.service.BuildEffectService;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class BuildEffectServiceTest {
    private final BuildEffectService service = new BuildEffectService();

    @Test
    void aggregatesRegularFeatureAndMortarEffectsButIgnoresInventoryEffects() {
        BuildPayload payload = mock(BuildPayload.class);
        BuildShipSnapshot ship = mock(BuildShipSnapshot.class);
        when(payload.mortarModification()).thenReturn(true);
        when(ship.mortarEffects(true)).thenReturn(Map.of("speed_pct", -5, "armor", 2));
        BuildFeatureSnapshot feature = new BuildFeatureSnapshot(1L, 1, Map.of("armor", 3));

        BuildSlotSelection sail = slot("sail", Map.of("speed_pct", 10, "armor", 1));
        BuildSlotSelection weapon = slot("weapon_front", Map.of("armor", 999));
        BuildSlotSelection ammo = slot("ammunition", Map.of("armor", 999));

        var result = service.resolve(payload, ship, feature, List.of(sail, weapon, ammo));

        assertThat(result.sets()).hasSize(3);
        assertThat(result.totals()).containsEntry("speed_pct", 5L).containsEntry("armor", 6L);
        assertThat(result.totals().get("armor").longValue()).isNotEqualTo(2004L);
    }

    @Test
    void specialistDynamicEffectsScaleWithSailorsAndBoarders() {
        BuildPayload payload = mock(BuildPayload.class);
        BuildShipSnapshot ship = mock(BuildShipSnapshot.class);
        when(payload.sailors()).thenReturn(10L);
        when(payload.soldiers()).thenReturn(2L);
        when(payload.musketeers()).thenReturn(3L);
        when(payload.mercenaries()).thenReturn(1L);
        when(payload.mortarModification()).thenReturn(false);
        when(ship.mortarEffects(false)).thenReturn(Map.of());

        BuildSlotSelection specialist = slot("special_crew", Map.of(
                "sail_deployment_speed_per_sailor_pct", 2,
                "boarding_cargo_weight_per_boarder_pct", 1.5,
                "special_mode_enabled", 0,
                "armor", 3));

        var result = service.resolve(payload, ship, null, List.of(specialist));

        assertThat(result.totals()).containsEntry("sail_deployment_speed_pct", 20L)
                .containsEntry("boarding_cargo_weight_pct", 9L)
                .containsEntry("special_mode_enabled", 1L)
                .containsEntry("armor", 3);
    }

    @Test
    void dynamicSpecialistEffectsKeepFractionalResultsWhenScalingIsNotIntegral() {
        BuildPayload payload = mock(BuildPayload.class);
        BuildShipSnapshot ship = mock(BuildShipSnapshot.class);
        when(payload.sailors()).thenReturn(3L);
        when(payload.soldiers()).thenReturn(0L);
        when(payload.musketeers()).thenReturn(0L);
        when(payload.mercenaries()).thenReturn(0L);
        when(payload.mortarModification()).thenReturn(false);
        when(ship.mortarEffects(false)).thenReturn(Map.of());

        BuildSlotSelection specialist = slot("special_crew", Map.of(
                "sail_deployment_speed_per_sailor_pct", 1.25));

        var result = service.resolve(payload, ship, null, List.of(specialist));

        assertThat(result.totals()).containsEntry("sail_deployment_speed_pct", 3.75);
    }

    @Test
    void duplicateEffectKeysAreSummedWithoutLosingFractionalValues() {
        BuildPayload payload = mock(BuildPayload.class);
        BuildShipSnapshot ship = mock(BuildShipSnapshot.class);
        when(payload.mortarModification()).thenReturn(false);
        when(ship.mortarEffects(false)).thenReturn(Map.of());

        var result = service.resolve(payload, ship, null, List.of(
                slot("sail", Map.of("turn_rate_pct", 1.25)),
                slot("upgrade", Map.of("turn_rate_pct", 2.5))));

        assertThat(result.totals().get("turn_rate_pct").doubleValue()).isEqualTo(3.75);
    }

    private static BuildSlotSelection slot(String type, Map<String, Number> effects) {
        BuildCatalogOption option = mock(BuildCatalogOption.class);
        when(option.effects()).thenReturn(effects);
        return new BuildSlotSelection(type, 1, 1L, "test", 1, option);
    }
}
