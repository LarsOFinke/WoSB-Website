package eu.royalblackwater.api.onboarding;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.NewcomerGuideBlockInput;
import eu.royalblackwater.api.dto.NewcomerGuideResourceInput;
import eu.royalblackwater.api.dto.NewcomerGuideUpdate;
import eu.royalblackwater.api.onboarding.repository.NewcomerGuideRepository;
import eu.royalblackwater.api.onboarding.service.NewcomerGuideService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class NewcomerGuideServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);
    private static final AuthenticatedUser STAFF = new AuthenticatedUser(8, "staff", "moderator", true, true, false);

    @Test
    void replaceRequiresStaffBeforeAnyDatabaseMutation() {
        NewcomerGuideRepository repository = mock(NewcomerGuideRepository.class);
        NewcomerGuideUpdate update = new NewcomerGuideUpdate(List.of(), "Intro", "Guide");

        assertThatThrownBy(() -> service(repository).replace(update, USER))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(403));
        verify(repository, never()).update(anyString(), anyMap());
    }

    @Test
    void replaceRejectsUnsafeExternalAndInternalResources() {
        NewcomerGuideRepository repository = mock(NewcomerGuideRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        NewcomerGuideResourceInput unsafe = new NewcomerGuideResourceInput(null, "Link", null,
                "external", "javascript:alert(1)");
        NewcomerGuideBlockInput resources = new NewcomerGuideBlockInput("resources", null, List.of(unsafe), "Links");

        assertThatThrownBy(() -> service(repository).replace(
                        new NewcomerGuideUpdate(List.of(resources), "Intro", "Guide"), STAFF))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("complete http(s) URL");
    }

    private static NewcomerGuideService service(NewcomerGuideRepository repository) {
        return new NewcomerGuideService(repository, mock(AuditService.class), CLOCK);
    }
}
