package eu.royalblackwater.api.forum;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.content.service.ContentEmbedValidator;
import eu.royalblackwater.api.dto.ForumThreadCreate;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.forum.repository.ForumRepository;
import eu.royalblackwater.api.forum.service.ForumService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class ForumServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void listNormalizesSearchAndLegacyLogisticsCategory() {
        ForumRepository repository = mock(ForumRepository.class);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of());
        ForumService service = service(repository, mock(FileAssetService.class));

        service.list("  convoy ", "loistics", 40, 10);

        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).query(anyString(), parameters.capture());
        assertThat(parameters.getValue()).containsEntry("search", "%convoy%")
                .containsEntry("category", "logistics")
                .containsEntry("limit", 40)
                .containsEntry("offset", 10);
    }

    @Test
    void createValidatesAttachmentsAndInlineEmbedsBeforeWritingThread() {
        ForumRepository repository = mock(ForumRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        when(files.ownedFiles(List.of(), USER)).thenReturn(List.of());
        when(repository.insertReturningId(anyString(), anyMap())).thenReturn(41L, 42L);
        when(repository.optional(anyString(), anyMap())).thenReturn(java.util.Optional.empty());
        ForumService service = service(repository, files);

        org.assertj.core.api.Assertions.assertThatThrownBy(() -> service.create(
                        new ForumThreadCreate("[[file:99]]", "general", List.of(), "Thread"), USER))
                .isInstanceOf(org.springframework.web.server.ResponseStatusException.class)
                .hasMessageContaining("attached to the same content");
        verify(repository, org.mockito.Mockito.never()).insertReturningId(anyString(), anyMap());
    }

    private static ForumService service(ForumRepository repository, FileAssetService files) {
        return new ForumService(repository, files, new ContentEmbedValidator(), mock(AuditService.class), CLOCK);
    }
}
