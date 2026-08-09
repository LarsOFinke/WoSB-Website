package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.dto.BuildCreate;
import eu.royalblackwater.api.dto.BuildUpdate;
import eu.royalblackwater.api.dto.InventorySlot;
import java.util.List;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BuildPayloadTest {
    @Test
    void createNormalizesBoundaryValuesAndInventory() {
        BuildPayload payload = BuildPayload.from(create(
                "  Broadside  ", null, List.of(" PVP_SOLO ", "pvp_solo", "combat"),
                List.of(new InventorySlot("  Long Gun  ", null), new InventorySlot(" ", 8L)),
                List.of(new InventorySlot(" Carpenter ", 3L), new InventorySlot("carpenter", 7L)),
                "  Notes  ", -5L, true, true));

        assertThat(payload.name()).isEqualTo("Broadside");
        assertThat(payload.type()).isEqualTo("balanced");
        assertThat(payload.shipId()).isEqualTo(42L);
        assertThat(payload.classifications()).containsExactly("pvp_solo", "combat");
        assertThat(payload.sails()).isEqualTo("square");
        assertThat(payload.upgrades()).hasSize(8).containsExactly("oak", null, null, null, null, null, null, null);
        assertThat(payload.lantern()).isEqualTo("lantern");
        assertThat(payload.researchSlot()).isTrue();
        assertThat(payload.mortarModification()).isTrue();
        assertThat(payload.sailors()).isZero();
        assertThat(payload.frontWeapons()).containsExactly(new InventorySlot("Long Gun", 1L));
        assertThat(payload.specialCrew()).containsExactly(new InventorySlot("Carpenter", 1L));
        assertThat(payload.details()).isEqualTo("Notes");
    }

    @Test
    void updateUsesTheSameNormalizationContract() {
        BuildPayload payload = BuildPayload.from(update("  Raider  ", " FAST_ROLE ", List.of("FAST")));

        assertThat(payload.name()).isEqualTo("Raider");
        assertThat(payload.type()).isEqualTo("fast_role");
        assertThat(payload.classifications()).containsExactly("fast");
        assertThat(payload.sailors()).isEqualTo(8L);
        assertThat(payload.soldiers()).isEqualTo(3L);
    }

    @Test
    void rejectsInvalidRoleClassificationAndBounds() {
        assertThatThrownBy(() -> BuildPayload.from(create("Valid", "bad role!", List.of(), List.of(), List.of(), null, 0L, false, false)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageContaining("Invalid build role");
        assertThatThrownBy(() -> BuildPayload.from(create("Valid", "combat", List.of("unknown"), List.of(), List.of(), null, 0L, false, false)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageContaining("Invalid build classification");
        assertThatThrownBy(() -> BuildPayload.from(create("Valid", "combat",
                List.of("port_battle", "pve_solo", "pve_group", "pve_instanced", "pvp_solo", "pvp_group", "pvp_instanced"),
                List.of(), List.of(), null, 0L, false, false)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageContaining("at most 6 classifications");
        assertThatThrownBy(() -> BuildPayload.from(create(" ", "combat", List.of(), List.of(), List.of(), null, 0L, false, false)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageContaining("Build name is required");
        assertThatThrownBy(() -> BuildPayload.from(create("x".repeat(141), "combat", List.of(), List.of(), List.of(), null, 0L, false, false)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageContaining("Build name is too long");
        assertThatThrownBy(() -> BuildPayload.from(create("Valid", "combat", List.of(), List.of(), List.of(), "x".repeat(3001), 0L, false, false)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageContaining("Details are too long");
    }

    @Test
    void slotLookupCoversEveryBucketAndUnknownTypes() {
        InventorySlot slot = new InventorySlot("item", 2L);
        BuildPayload payload = new BuildPayload("n", "t", 1L, List.of(), null, List.of(), null, false, false,
                0, 0, 0, 0, List.of(slot), List.of(slot), List.of(slot), List.of(slot), List.of(slot),
                List.of(slot), List.of(slot), List.of(slot), List.of(slot), List.of(slot), null);

        assertThat(payload.slots("weapon_front")).containsExactly(slot);
        assertThat(payload.slots("weapon_rear")).containsExactly(slot);
        assertThat(payload.slots("weapon_port")).containsExactly(slot);
        assertThat(payload.slots("weapon_starboard")).containsExactly(slot);
        assertThat(payload.slots("weapon_mortar")).containsExactly(slot);
        assertThat(payload.slots("weapon_special")).containsExactly(slot);
        assertThat(payload.slots("special_crew")).containsExactly(slot);
        assertThat(payload.slots("ammunition")).containsExactly(slot);
        assertThat(payload.slots("consumable")).containsExactly(slot);
        assertThat(payload.slots("hold")).containsExactly(slot);
        assertThat(payload.slots("unknown")).isEmpty();
    }

    private static BuildCreate create(String name, String type, List<String> classifications,
                                      List<InventorySlot> front, List<InventorySlot> crew, String details,
                                      Long sailors, Boolean research, Boolean mortar) {
        return new BuildCreate(
                List.of(), name, type, classifications, List.of(), details, front, List.of(), " lantern ", 0L,
                mortar, List.of(), 0L, List.of(), List.of(), research, sailors, " square ", 42L, -1L, crew,
                List.of(), List.of(), " oak ", null, null, null, null, null, null, null);
    }

    private static BuildUpdate update(String name, String type, List<String> classifications) {
        return new BuildUpdate(
                List.of(), name, type, classifications, List.of(), null, List.of(), List.of(), null, 0L,
                false, List.of(), 0L, List.of(), List.of(), false, 8L, null, 42L, 3L, List.of(),
                List.of(), List.of(), null, null, null, null, null, null, null, null);
    }
}
