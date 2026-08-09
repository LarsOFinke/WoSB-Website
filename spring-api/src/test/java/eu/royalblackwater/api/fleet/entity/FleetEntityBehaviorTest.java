package eu.royalblackwater.api.fleet.entity;

import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.assertj.core.api.Assertions.assertThat;

class FleetEntityBehaviorTest {
    @Test
    void fleetRolePermissionFlagsAndMetadataAreExposedWithoutTransformation() {
        FleetRoleEntity role = new FleetRoleEntity();
        ReflectionTestUtils.setField(role, "id", 7);
        ReflectionTestUtils.setField(role, "code", "commander");
        ReflectionTestUtils.setField(role, "label", "Commander");
        ReflectionTestUtils.setField(role, "rank", 90);
        ReflectionTestUtils.setField(role, "leadership", true);
        ReflectionTestUtils.setField(role, "canManageFleet", true);
        ReflectionTestUtils.setField(role, "canManageMembers", false);
        ReflectionTestUtils.setField(role, "system", true);
        ReflectionTestUtils.setField(role, "active", true);

        assertThat(role.getId()).isEqualTo(7);
        assertThat(role.getCode()).isEqualTo("commander");
        assertThat(role.getLabel()).isEqualTo("Commander");
        assertThat(role.getRank()).isEqualTo(90);
        assertThat(role.isLeadership()).isTrue();
        assertThat(role.canManageFleet()).isTrue();
        assertThat(role.canManageMembers()).isFalse();
        assertThat(role.isSystem()).isTrue();
        assertThat(role.isActive()).isTrue();
    }
}
