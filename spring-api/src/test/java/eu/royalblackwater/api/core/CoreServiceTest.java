package eu.royalblackwater.api.core;

import eu.royalblackwater.api.core.mapper.CoreDtoMapper;
import eu.royalblackwater.api.core.repository.CoreRepository;
import eu.royalblackwater.api.core.service.CoreService;
import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.MigrationInfo;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Answers.RETURNS_DEEP_STUBS;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class CoreServiceTest {
    @Test
    void healthAndHomeExposeStablePublicMetadata() {
        CoreService service = new CoreService(mock(CoreRepository.class), mock(Flyway.class), new CoreDtoMapper());

        assertThat(service.health().status()).isEqualTo("ok");
        assertThat(service.home()).satisfies(home -> {
            assertThat(home.route()).isEqualTo("/home");
            assertThat(home.modules()).extracting("key")
                    .containsExactly("builds", "guides", "forum", "calendar", "groups");
        });
    }

    @Test
    void readinessVerifiesDatabaseMigrationStateAndFlywayValidation() {
        CoreRepository repository = mock(CoreRepository.class);
        Flyway flyway = mock(Flyway.class, RETURNS_DEEP_STUBS);
        when(flyway.info().pending()).thenReturn(new MigrationInfo[0]);

        assertThat(new CoreService(repository, flyway, new CoreDtoMapper()).readiness().status()).isEqualTo("ready");
        verify(repository).verifyDatabaseConnection();
        verify(flyway).validate();
    }

    @Test
    void readinessFailsClosedWhenMigrationsArePending() {
        CoreRepository repository = mock(CoreRepository.class);
        Flyway flyway = mock(Flyway.class, RETURNS_DEEP_STUBS);
        when(flyway.info().pending()).thenReturn(new MigrationInfo[]{mock(MigrationInfo.class)});

        assertThatThrownBy(() -> new CoreService(repository, flyway, new CoreDtoMapper()).readiness())
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(503))
                .hasMessageContaining("Database is not ready");
    }

    @Test
    void readinessWrapsDatabaseFailuresAsServiceUnavailable() {
        CoreRepository repository = mock(CoreRepository.class);
        Flyway flyway = mock(Flyway.class, RETURNS_DEEP_STUBS);
        org.mockito.Mockito.doThrow(new IllegalStateException("database offline"))
                .when(repository).verifyDatabaseConnection();

        assertThatThrownBy(() -> new CoreService(repository, flyway, new CoreDtoMapper()).readiness())
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Database is not ready")
                .hasCauseInstanceOf(IllegalStateException.class);
    }
}
