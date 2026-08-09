package eu.royalblackwater.api.raidhelper.dto;

import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RaidHelperJsonPayloadDtoTest {
    @Test
    void nullPayloadBecomesImmutableEmptyObject() {
        RaidHelperJsonPayloadDto payload = RaidHelperJsonPayloadDto.of(null);
        assertThat(payload.values()).isEmpty();
        assertThatThrownBy(() -> payload.values().put("x", 1))
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void payloadDefensivelyCopiesCallerMap() {
        Map<String, Object> source = new LinkedHashMap<>();
        source.put("name", "raid");
        RaidHelperJsonPayloadDto payload = new RaidHelperJsonPayloadDto(source);
        source.put("name", "changed");
        source.put("extra", true);

        assertThat(payload.values()).containsExactly(Map.entry("name", "raid"));
        assertThatThrownBy(() -> payload.values().put("other", 2))
                .isInstanceOf(UnsupportedOperationException.class);
    }
}
