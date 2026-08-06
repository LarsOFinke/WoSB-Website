package eu.royalblackwater.api.masterdata;

import eu.royalblackwater.api.masterdata.model.SeedCatalog;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
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
}
