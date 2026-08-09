package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.repository.BuildCatalogRepository;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.ships.mapper.ShipMapper;
import eu.royalblackwater.api.ships.repository.ShipRepository;
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
}
