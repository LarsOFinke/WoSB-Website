package eu.royalblackwater.api.files.service;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class FileTypePolicyTest {
    @Test
    void sanitizesPathControlAndDirectionCharactersFromDisplayNames() {
        assertThat(FileTypePolicy.sanitizeOriginalName("../\\..\\report\u202Efdp.pdf", "fallback.pdf"))
                .isEqualTo("reportfdp.pdf");
        assertThat(FileTypePolicy.sanitizeOriginalName(".hidden.txt", "fallback.txt"))
                .isEqualTo("hidden.txt");
        assertThat(FileTypePolicy.sanitizeOriginalName("\u0000\u200F", "fallback.txt"))
                .isEqualTo("fallback.txt");
    }
}
