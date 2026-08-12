package eu.royalblackwater.api.masterdata;

import eu.royalblackwater.api.masterdata.repository.SeedCatalog;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import tools.jackson.databind.ObjectMapper;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SeedCatalogTest {
    @Test
    void preservesNullableSeedFieldsInReadOnlyMaps() {
        Map<String, Object> seed = new java.util.LinkedHashMap<>(Map.of("seed_key", "option"));
        seed.put("nullable", null);
        List<Map<String, Object>> result = SeedCatalog.listOfMaps(List.of(seed));

        assertThat(result.getFirst()).containsEntry("nullable", null);
        assertThatThrownBy(() -> result.getFirst().put("changed", true))
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void deZevenCrewUpgradeOverridesStoreCompleteEffectiveValues() {
        SeedCatalog catalog = new SeedCatalog(new PathMatchingResourcePatternResolver(), new ObjectMapper());
        Map<String, Object> ship = catalog.ships().stream()
                .filter(value -> "De Zeven Provincien".equals(value.get("name")))
                .findFirst().orElseThrow();
        Map<String, Map<String, Object>> overrides = SeedCatalog.listOfMaps(ship.get("upgrade_effect_overrides"))
                .stream().collect(java.util.stream.Collectors.toMap(
                        value -> String.valueOf(value.get("upgrade_seed_id")), value -> value));

        assertThat(effects(overrides.get("teak-frames"))).containsEntry("crew_capacity", 14);
        assertThat(effects(overrides.get("extra-bunks"))).containsEntry("crew_capacity", 20);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> effects(Map<String, Object> override) {
        return (Map<String, Object>) override.get("stat_effects");
    }
}
