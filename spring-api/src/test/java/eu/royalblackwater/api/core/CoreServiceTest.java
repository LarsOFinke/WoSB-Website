package eu.royalblackwater.api.core;

import eu.royalblackwater.api.core.mapper.CoreDtoMapper;
import eu.royalblackwater.api.core.repository.CoreRepository;
import eu.royalblackwater.api.core.service.CoreService;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class CoreServiceTest {
    @Test
    void healthAndHomeExposeStablePublicMetadata() {
        CoreService service = new CoreService(mock(CoreRepository.class), new CoreDtoMapper());

        assertThat(service.health().status()).isEqualTo("ok");
        assertThat(service.home()).satisfies(home -> {
            assertThat(home.route()).isEqualTo("/home");
            assertThat(home.modules()).extracting("key")
                    .containsExactly("builds", "guides", "forum", "calendar", "groups");
        });
    }

    @Test
    void readinessVerifiesTheRuntimeDatabaseConnection() {
        CoreRepository repository = mock(CoreRepository.class);

        assertThat(new CoreService(repository, new CoreDtoMapper()).readiness().status()).isEqualTo("ready");
        verify(repository).verifyDatabaseConnection();
    }

    @Test
    void readinessWrapsDatabaseFailuresAsServiceUnavailable() {
        CoreRepository repository = mock(CoreRepository.class);
        org.mockito.Mockito.doThrow(new IllegalStateException("database offline"))
                .when(repository).verifyDatabaseConnection();

        assertThatThrownBy(() -> new CoreService(repository, new CoreDtoMapper()).readiness())
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Database is not ready")
                .hasCauseInstanceOf(IllegalStateException.class);
    }
}
