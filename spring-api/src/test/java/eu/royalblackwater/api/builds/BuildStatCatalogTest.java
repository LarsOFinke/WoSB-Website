package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.service.BuildStatCatalog;
import java.util.HashSet;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class BuildStatCatalogTest {
    @Test
    void generatedCatalogHasUniqueStableKeysAndBoundedMetadata() {
        assertThat(BuildStatCatalog.ALL).isNotEmpty();
        var keys = new HashSet<String>();
        BuildStatCatalog.ALL.forEach(definition -> {
            assertThat(definition.key()).matches("[a-z0-9_]+");
            assertThat(definition.label()).isNotBlank();
            assertThat(definition.category()).isNotBlank();
            assertThat(definition.source()).isNotBlank();
            assertThat(definition.precision()).isBetween(0, 4);
            assertThat(keys.add(definition.key())).as("duplicate stat key %s", definition.key()).isTrue();
        });
    }
}
