package eu.royalblackwater.api.guides;

import eu.royalblackwater.api.account.service.UserReferenceService;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.service.BuildService;
import eu.royalblackwater.api.content.service.ContentEmbedValidator;
import eu.royalblackwater.api.dto.GuideCreate;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.guides.repository.GuideRepository;
import eu.royalblackwater.api.guides.service.GuideService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GuideServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void listNormalizesUnknownCategoryAndPreservesPaging() {
        GuideRepository repository = mock(GuideRepository.class);
        UserReferenceService users = mock(UserReferenceService.class);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of());
        when(users.readMany(List.of())).thenReturn(Map.of());
        GuideService service = service(repository, mock(FileAssetService.class), mock(BuildService.class), users);

        service.list("  boarding ", "unknown-category", 30, 60, USER);

        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).query(anyString(), parameters.capture());
        assertThat(parameters.getValue()).containsEntry("search", "%boarding%")
                .containsEntry("category", "general")
                .containsEntry("limit", 30)
                .containsEntry("offset", 60);
    }

    @Test
    void createRejectsInlineBuildNotDeclaredInLinkedBuildsBeforePersistence() {
        GuideRepository repository = mock(GuideRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        BuildService builds = mock(BuildService.class);
        when(files.ownedFiles(List.of(), USER)).thenReturn(List.of());
        when(builds.getMany(List.of(), USER)).thenReturn(List.of());

        GuideService service = service(repository, files, builds, mock(UserReferenceService.class));
        assertThatThrownBy(() -> service.create(
                        new GuideCreate("[[build:9|card]]", List.of(), "general", List.of(), null, "Guide"), USER))
                .isInstanceOf(org.springframework.web.server.ResponseStatusException.class)
                .hasMessageContaining("linked to the same guide");
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    private static GuideService service(GuideRepository repository, FileAssetService files, BuildService builds,
                                        UserReferenceService users) {
        return new GuideService(repository, files, builds, users, new ContentEmbedValidator(),
                mock(AuditService.class), CLOCK);
    }
}
