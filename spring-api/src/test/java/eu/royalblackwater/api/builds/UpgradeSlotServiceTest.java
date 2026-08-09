package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.dto.BuildCatalogOption;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.builds.dto.BuildSlotSelection;
import eu.royalblackwater.api.builds.service.UpgradeSlotService;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class UpgradeSlotServiceTest {
    private final UpgradeSlotService service = new UpgradeSlotService();

    @Test
    void clampsBaseSlotsAndExposesLockedFlags() {
        var access = service.calculate(ship(3), null, List.of());
        assertThat(access.baseSlots()).isEqualTo(3);
        assertThat(access.availableSlots()).isEqualTo(3);
        assertThat(access.slot5()).isFalse();
        assertThat(access.slot8()).isFalse();
    }

    @Test
    void researchAndNativeExtraSlotsUnlockUpToEightSlots() {
        var access = service.calculate(ship(7), new BuildFeatureSnapshot(1L, 2, Map.of()), List.of());
        assertThat(access.baseSlots()).isEqualTo(4);
        assertThat(access.researchSlots()).isEqualTo(2);
        assertThat(access.shipExtraSlots()).isEqualTo(2);
        assertThat(access.availableSlots()).isEqualTo(8);
        assertThat(access.slot5()).isTrue();
        assertThat(access.slot8()).isTrue();
    }

    @Test
    void expansionEffectsOnlyCountFromAlreadyReachableUpgradeSlots() {
        var access = service.calculate(ship(4), null, List.of(upgrade(1, 2), upgrade(6, 4)));
        assertThat(access.expansionSlots()).isEqualTo(2);
        assertThat(access.availableSlots()).isEqualTo(6);
        assertThat(access.slot6()).isTrue();
        assertThat(access.slot7()).isFalse();
    }

    @Test
    void negativeAndExcessiveEffectsAreClamped() {
        var access = service.calculate(ship(4), null, List.of(upgrade(1, -5), upgrade(2, 99)));
        assertThat(access.expansionSlots()).isEqualTo(4);
        assertThat(access.availableSlots()).isEqualTo(8);
    }

    @Test
    void shipsWithoutUpgradeRackCannotGainSlotsFromExpansionEffects() {
        var access = service.calculate(ship(0), new BuildFeatureSnapshot(1L, 8, Map.of()), List.of(upgrade(1, 8)));
        assertThat(access.availableSlots()).isZero();
        assertThat(access.expansionSlots()).isZero();
        assertThat(access.researchSlots()).isZero();
    }

    private static BuildShipSnapshot ship(int upgradeSlots) {
        return new BuildShipSnapshot(null, upgradeSlots, 0, 0, false, Map.of(), null, Map.of());
    }

    private static BuildSlotSelection upgrade(int index, int extraSlots) {
        BuildCatalogOption option = mock(BuildCatalogOption.class);
        when(option.effects()).thenReturn(Map.of("extra_upgrade_slots", extraSlots));
        return new BuildSlotSelection("upgrade", index, index, "Upgrade " + index, 1, option);
    }
}
