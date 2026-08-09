package eu.royalblackwater.api.persistence;

import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class JdbcQueryServiceTest {
    private final NamedParameterJdbcTemplate template = mock(NamedParameterJdbcTemplate.class);
    private final JdbcQueryService jdbc = new JdbcQueryService(template);

    @Test
    void queryAndUpdateDelegateParameterizedSql() {
        Map<String, Object> parameters = Map.of("id", 7);
        Map<String, Object> row = Map.of("id", 7);
        when(template.queryForList("select", parameters)).thenReturn(List.of(row));
        when(template.update("update", parameters)).thenReturn(2);

        assertThat(jdbc.query("select", parameters)).containsExactly(row);
        assertThat(jdbc.update("update", parameters)).isEqualTo(2);
    }

    @Test
    void optionalAcceptsZeroOrOneRowAndRejectsAmbiguousResults() {
        when(template.queryForList("empty", Map.of())).thenReturn(List.of());
        when(template.queryForList("one", Map.of())).thenReturn(List.of(Map.of("id", 1)));
        when(template.queryForList("many", Map.of())).thenReturn(List.of(Map.of("id", 1), Map.of("id", 2)));

        assertThat(jdbc.optional("empty", Map.of())).isEmpty();
        assertThat(jdbc.optional("one", Map.of())).contains(Map.of("id", 1));
        assertThatThrownBy(() -> jdbc.optional("many", Map.of()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Expected at most one row");
    }

    @Test
    void requiredReturnsTheOnlyRowAndFailsWhenMissing() {
        when(template.queryForList("one", Map.of())).thenReturn(List.of(Map.of("id", 1)));
        when(template.queryForList("empty", Map.of())).thenReturn(List.of());

        assertThat(jdbc.required("one", Map.of())).containsEntry("id", 1);
        assertThatThrownBy(() -> jdbc.required("empty", Map.of()))
                .isInstanceOf(NoSuchElementException.class);
    }

    @Test
    void insertReturningIdCopiesNamedParametersAndRequiresIdentifier() {
        when(template.queryForObject(eq("insert"), any(MapSqlParameterSource.class), eq(Number.class)))
                .thenReturn(42L);

        assertThat(jdbc.insertReturningId("insert", Map.of("name", "Captain", "active", true))).isEqualTo(42L);

        ArgumentCaptor<MapSqlParameterSource> source = ArgumentCaptor.forClass(MapSqlParameterSource.class);
        verify(template).queryForObject(eq("insert"), source.capture(), eq(Number.class));
        assertThat(source.getValue().getValue("name")).isEqualTo("Captain");
        assertThat(source.getValue().getValue("active")).isEqualTo(true);

        when(template.queryForObject(eq("missing"), any(MapSqlParameterSource.class), eq(Number.class)))
                .thenReturn(null);
        assertThatThrownBy(() -> jdbc.insertReturningId("missing", Map.of()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("did not return an identifier");
    }

    @Test
    void countNormalizesNullDatabaseResultToZero() {
        when(template.queryForObject("count", Map.of(), Long.class)).thenReturn(5L);
        when(template.queryForObject("null-count", Map.of(), Long.class)).thenReturn(null);

        assertThat(jdbc.count("count", Map.of())).isEqualTo(5L);
        assertThat(jdbc.count("null-count", Map.of())).isZero();
    }
}
