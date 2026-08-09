package eu.royalblackwater.api.onboarding;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.NewcomerGuideBlockInput;
import eu.royalblackwater.api.dto.NewcomerGuideResourceInput;
import eu.royalblackwater.api.dto.NewcomerGuideUpdate;
import eu.royalblackwater.api.onboarding.repository.NewcomerGuideRepository;
import eu.royalblackwater.api.onboarding.repository.queries.NewcomerGuideQueries;
import eu.royalblackwater.api.onboarding.service.NewcomerGuideService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class NewcomerGuideCoverageTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser STAFF = new AuthenticatedUser(8, "staff", "moderator", true, true, false);

    @Test
    void getCreatesMissingPageAndRendersEveryResourceKind() {
        NewcomerGuideRepository repository = mock(NewcomerGuideRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        when(repository.required(NewcomerGuideQueries.READ_SELECT_01, Map.of("id", 1L))).thenReturn(page());
        when(repository.query(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (NewcomerGuideQueries.READ_SELECT_02.equals(sql)) {
                return List.of(block(10L, "resources", "Useful links", null));
            }
            if (NewcomerGuideQueries.READ_SELECT_03.equals(sql)) {
                return List.of(
                        resource(1L, 101L, "guide", null, null, true, "Published guide", "Guide summary", null),
                        resource(2L, 102L, "guide", "Draft", null, false, "Draft guide", null, null),
                        resource(3L, 201L, "build", null, null, true, null, null, "Fast frigate"),
                        resource(4L, null, "internal", null, "/handbook", true, null, null, null),
                        resource(5L, null, "external", null, "https://example.com/help?q=1", true, null, null, null));
            }
            return List.of();
        });

        var guide = service(repository).get();

        assertThat(guide.blocks()).hasSize(1);
        assertThat(guide.blocks().getFirst().resources()).hasSize(5);
        assertThat(guide.blocks().getFirst().resources().stream().map(value -> value.href()).toList())
                .contains("/guides/101", "/guides/102", "/builds/201", "/handbook", "https://example.com/help?q=1");
        verify(repository).update(eq(NewcomerGuideQueries.ENSURE_PAGE_INSERT_01), anyMap());
    }

    @Test
    void replacePersistsTextAndAllResourceTypesAfterReferenceValidation() {
        NewcomerGuideRepository repository = mock(NewcomerGuideRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        when(repository.insertReturningId(anyString(), anyMap())).thenReturn(10L, 11L, 12L, 13L, 14L, 15L);
        when(repository.required(NewcomerGuideQueries.READ_SELECT_01, Map.of("id", 1L))).thenReturn(page());
        when(repository.query(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (NewcomerGuideQueries.VALIDATE_SELECT_01.equals(sql)) return List.of(Map.of("id", 101L));
            if (NewcomerGuideQueries.VALIDATE_SELECT_02.equals(sql)) return List.of(Map.of("id", 201L));
            return List.of();
        });
        List<NewcomerGuideResourceInput> resources = List.of(
                new NewcomerGuideResourceInput(null, null, 101L, "guide", null),
                new NewcomerGuideResourceInput(null, "Build", 201L, "build", null),
                new NewcomerGuideResourceInput(null, null, null, "internal", "/guides"),
                new NewcomerGuideResourceInput(null, "Docs", null, "external", "https://example.com/docs"));
        NewcomerGuideUpdate update = new NewcomerGuideUpdate(List.of(
                new NewcomerGuideBlockInput("text", " Welcome aboard ", null, " Start here "),
                new NewcomerGuideBlockInput("resources", null, resources, " Resources ")),
                null, " Captain guide ");

        var result = service(repository).replace(update, STAFF);

        assertThat(result.title()).isEqualTo("Captain guide");
        verify(repository).update(NewcomerGuideQueries.REPLACE_DELETE_01, Map.of("id", 1L));
        verify(repository, org.mockito.Mockito.atLeast(2)).insertReturningId(anyString(), anyMap());
    }

    @Test
    void replaceCoversValidationFailuresForBlocksResourcesAndReferences() {
        NewcomerGuideRepository repository = mock(NewcomerGuideRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        NewcomerGuideService service = service(repository);

        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("unknown", "body", null, "Title")), STAFF),
                "Unsupported guide block type");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("text", "body", null, "   ")), STAFF),
                "Block title is required");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("text", "  ", null, "Title")), STAFF),
                "Text blocks require body content");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("resources", null,
                List.of(new NewcomerGuideResourceInput(null, null, null, "unknown", null)), "Links")), STAFF),
                "Unsupported guide resource type");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("resources", null,
                List.of(new NewcomerGuideResourceInput(null, null, null, "guide", null)), "Links")), STAFF),
                "selected guide");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("resources", null,
                List.of(new NewcomerGuideResourceInput(null, null, null, "build", null)), "Links")), STAFF),
                "selected build");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("resources", null,
                List.of(new NewcomerGuideResourceInput(null, null, null, "internal", "//evil")), "Links")), STAFF),
                "single '/'");
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("resources", null,
                List.of(new NewcomerGuideResourceInput(null, null, null, "external", "https://[bad")), "Links")), STAFF),
                "complete http(s) URL");

        when(repository.query(NewcomerGuideQueries.VALIDATE_SELECT_01, Map.of("ids", List.of(101L))))
                .thenReturn(List.of());
        assertBad(() -> service.replace(update(new NewcomerGuideBlockInput("resources", null,
                List.of(new NewcomerGuideResourceInput(null, null, 101L, "guide", null)), "Links")), STAFF),
                "selected guide");
    }

    private static NewcomerGuideUpdate update(NewcomerGuideBlockInput block) {
        return new NewcomerGuideUpdate(List.of(block), "Intro", "Guide");
    }

    private static void assertBad(org.assertj.core.api.ThrowableAssert.ThrowingCallable call, String message) {
        assertThatThrownBy(call).isInstanceOf(ResponseStatusException.class).hasMessageContaining(message);
    }

    private static NewcomerGuideService service(NewcomerGuideRepository repository) {
        return new NewcomerGuideService(repository, mock(AuditService.class), CLOCK);
    }

    private static Map<String, Object> page() {
        return new HashMap<>(Map.of(
                "intro", "Intro", "title", "Captain guide", "updated_at", LocalDateTime.of(2030, 1, 15, 12, 0),
                "updated_by", "staff"));
    }

    private static Map<String, Object> block(long id, String type, String title, String body) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", id);
        row.put("block_type", type);
        row.put("title", title);
        row.put("body", body);
        return row;
    }

    private static Map<String, Object> resource(long id, Long resourceId, String type, String label, String url,
            boolean published, String guideTitle, String guideSummary, String buildName) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", id);
        row.put("block_id", 10L);
        row.put("resource_id", resourceId);
        row.put("resource_type", type);
        row.put("label", label);
        row.put("url", url);
        row.put("is_published", published);
        row.put("guide_title", guideTitle);
        row.put("guide_summary", guideSummary);
        row.put("build_name", buildName);
        return row;
    }
}
