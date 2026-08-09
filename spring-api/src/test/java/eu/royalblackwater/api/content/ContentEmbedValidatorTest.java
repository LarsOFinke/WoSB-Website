package eu.royalblackwater.api.content;

import eu.royalblackwater.api.content.service.ContentEmbedValidator;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ContentEmbedValidatorTest {
    private final ContentEmbedValidator validator = new ContentEmbedValidator();

    @Test
    void acceptsOwnedEmbedsAndRejectsInvalidOptionsOrForeignReferences() {
        validator.validateFiles("[[file:7|large]] and [[file:8]]", List.of(7L, 8L));
        validator.validateBuilds("[[build:9|card]]", List.of(9L));

        assertThatThrownBy(() -> validator.validateFiles("[[file:7|huge]]", List.of(7L)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Invalid inline file size");
        assertThatThrownBy(() -> validator.validateBuilds("[[build:99|card]]", List.of(9L)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("linked to the same guide");
    }

    @Test
    void enforcesEmbedCountLimits() {
        String files = java.util.stream.IntStream.rangeClosed(1, 25)
                .mapToObj(id -> "[[file:" + id + "]]" ).collect(java.util.stream.Collectors.joining(" "));
        List<Long> ids = java.util.stream.LongStream.rangeClosed(1, 25).boxed().toList();
        assertThatThrownBy(() -> validator.validateFiles(files, ids))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Maximum is 24");
    }
}
