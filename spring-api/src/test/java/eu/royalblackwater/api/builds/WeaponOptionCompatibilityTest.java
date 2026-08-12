package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.filter.WeaponOptionCompatibility;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WeaponOptionCompatibilityTest {
    @Test
    void heavyMortarIgnoresMortarCaliberLimitsButRemainsAMortarOnlyWeapon() {
        assertThat(WeaponOptionCompatibility.isMortarCompatible("mortar_universal", 11.0, 6.0)).isTrue();
        assertThat(WeaponOptionCompatibility.isMortarKind("mortar_universal")).isTrue();
    }

    @Test
    void ordinaryMortarsRemainLimitedByCaliber() {
        assertThat(WeaponOptionCompatibility.isMortarCompatible("mortar", 11.0, 6.0)).isFalse();
        assertThat(WeaponOptionCompatibility.isMortarCompatible("mortar", 6.0, 6.0)).isTrue();
    }
}
