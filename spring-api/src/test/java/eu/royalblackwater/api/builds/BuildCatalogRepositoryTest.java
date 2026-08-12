package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.dto.BuildCatalogOption;
import eu.royalblackwater.api.builds.repository.BuildCatalogRepository;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.ships.mapper.ShipMapper;
import eu.royalblackwater.api.ships.repository.ShipRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class BuildCatalogRepositoryTest {
    @Test
    void featureEffectsKeepIntegralDatabaseValuesAsLongs() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.optional(anyString(), any())).thenReturn(Optional.of(Map.of(
                "id", 7L,
                "upgrade_slots_granted", 1)));
        when(jdbc.query(anyString(), any())).thenReturn(List.of(Map.of(
                "effect_key", "extra_upgrade_slots",
                "effect_value", 2.0)));
        BuildCatalogRepository repository = new BuildCatalogRepository(
                jdbc, mock(ShipRepository.class), mock(ShipMapper.class));

        var feature = repository.feature(7L).orElseThrow();

        assertThat(feature.effects()).containsEntry("extra_upgrade_slots", 2L);
    }

    @Test
    void shipUpgradeOverridesExposeTheCompleteShipSpecificEffectForTheSelectedShip() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.query(anyString(), any())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0, String.class);
            if (sql.contains("from build_item_options")) {
                LocalDateTime timestamp = LocalDateTime.of(2030, 1, 15, 12, 0);
                return List.of(
                        Map.of("id", 12L, "category_key", "upgrade", "name", "Teak Frames",
                                "sort_order", 1, "created_at", timestamp, "updated_at", timestamp),
                        Map.of("id", 13L, "category_key", "upgrade", "name", "Extra Bunks",
                                "sort_order", 2, "created_at", timestamp, "updated_at", timestamp));
            }
            if (sql.contains("build_item_option_slot_types")) return List.of();
            if (sql.contains("from build_item_effects")) {
                return List.of(
                        Map.of("option_id", 12L, "effect_key", "crew_capacity", "effect_value", 10.0),
                        Map.of("option_id", 13L, "effect_key", "crew_capacity", "effect_value", 14.0));
            }
            if (sql.contains("from ship_upgrade_effect_overrides")) {
                return List.of(
                        Map.of("option_id", 12L, "effect_key", "crew_capacity", "effect_value", 14.0),
                        Map.of("option_id", 13L, "effect_key", "crew_capacity", "effect_value", 20.0));
            }
            return List.of();
        });
        BuildCatalogRepository repository = new BuildCatalogRepository(
                jdbc, mock(ShipRepository.class), mock(ShipMapper.class));

        Map<String, BuildCatalogOption> options = repository.options(99L).stream()
                .collect(java.util.stream.Collectors.toMap(BuildCatalogOption::name, value -> value));
        var teakFrames = options.get("Teak Frames");
        var extraBunks = options.get("Extra Bunks");

        assertThat(teakFrames.baseEffects()).containsEntry("crew_capacity", 10L);
        assertThat(teakFrames.effects()).containsEntry("crew_capacity", 14L);
        assertThat(extraBunks.baseEffects()).containsEntry("crew_capacity", 14L);
        assertThat(extraBunks.effects()).containsEntry("crew_capacity", 20L);
        assertThat(options.values()).allMatch(BuildCatalogOption::shipSpecific);
    }
}
