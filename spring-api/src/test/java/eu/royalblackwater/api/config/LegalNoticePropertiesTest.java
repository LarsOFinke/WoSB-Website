package eu.royalblackwater.api.config;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class LegalNoticePropertiesTest {

    @Test
    void retainsAValidPublicHttpsRepository() {
        assertThat(properties("https://github.com/example/community-project").publicRepositoryUrl())
                .isEqualTo("https://github.com/example/community-project");
    }

    @Test
    void rejectsUnsafeOrMalformedEnvironmentRepositoryReferences() {
        assertThat(properties("http://github.com/example/community-project").publicRepositoryUrl()).isEmpty();
        assertThat(properties("https://user:secret@github.com/example/project").publicRepositoryUrl()).isEmpty();
        assertThat(properties("https:// invalid").publicRepositoryUrl()).isEmpty();
    }

    private static LegalNoticeProperties properties(String repositoryUrl) {
        return new LegalNoticeProperties(false,
                "", "", "", "", "", "", "Deutschland", "", "", "", "", "", "", "", "",
                "", "", "", "", "Deutschland", "", "", repositoryUrl);
    }
}
