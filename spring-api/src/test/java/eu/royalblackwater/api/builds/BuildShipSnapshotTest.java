package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class BuildShipSnapshotTest {
    @Test
    void capacitiesRespectMortarModificationAndNeverBecomeNegative() {
        BuildShipSnapshot ship = snapshot();

        assertThat(ship.capacity("weapon_mortar", false)).isEqualTo(2);
        assertThat(ship.capacity("weapon_mortar", true)).isEqualTo(5);
        assertThat(ship.capacity("weapon_port", false)).isEqualTo(1);
        assertThat(ship.capacity("weapon_port", true)).isZero();
        assertThat(ship.capacity("weapon_starboard", true)).isZero();
        assertThat(ship.capacity("weapon_front", true)).isEqualTo(4);
        assertThat(ship.capacity("missing", true)).isZero();
    }

    @Test
    void mortarCaliberUsesTheHighestAvailableCaliber() {
        BuildShipSnapshot ship = snapshot();
        assertThat(ship.mortarCaliber(false)).isEqualTo(18.0);
        assertThat(ship.mortarCaliber(true)).isEqualTo(24.0);

        BuildShipSnapshot withoutMortarMount = new BuildShipSnapshot(null, 0, 0, 0, false, Map.of(),
                new BuildShipSnapshot.MortarModification(1, 24.0, 0, Map.of()), Map.of());
        assertThat(withoutMortarMount.mortarCaliber(false)).isNull();
        assertThat(withoutMortarMount.mortarCaliber(true)).isEqualTo(24.0);
    }

    @Test
    void specialCapacityAndEffectsFailClosedForMissingState() {
        BuildShipSnapshot ship = snapshot();
        assertThat(ship.specialCapacity("weapon_front")).isEqualTo(2);
        assertThat(ship.specialCapacity("missing")).isZero();
        assertThat(ship.mortarEffects(false)).isEmpty();
        assertThat(ship.mortarEffects(true)).containsEntry("reload_pct", 5);

        BuildShipSnapshot noModification = new BuildShipSnapshot(null, 0, 0, 0, false, Map.of(), null, Map.of());
        assertThat(noModification.mortarEffects(true)).isEmpty();
    }

    private static BuildShipSnapshot snapshot() {
        return new BuildShipSnapshot(null, 5, 100, 20, true, Map.of(
                "weapon_mortar", new BuildShipSnapshot.WeaponMount(2, 0, 4, 18.0),
                "weapon_port", new BuildShipSnapshot.WeaponMount(1, 0, 5, 20.0),
                "weapon_starboard", new BuildShipSnapshot.WeaponMount(2, 0, 5, 20.0),
                "weapon_front", new BuildShipSnapshot.WeaponMount(4, 2, 5, 20.0)),
                new BuildShipSnapshot.MortarModification(3, 24.0, -3, Map.of("reload_pct", 5)), Map.of());
    }
}
