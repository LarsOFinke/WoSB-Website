package eu.royalblackwater.api.persistence;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class PersistenceUtilitiesTest {
    @Test
    void rowValuesConvertSupportedJdbcShapesAndFailClosedOnWrongTypes() {
        LocalDate date = LocalDate.of(2030, 1, 15);
        LocalDateTime time = LocalDateTime.of(2030, 1, 15, 12, 0);
        Map<String, Object> row = Map.of(
                "id", 7,
                "flag", true,
                "date", java.sql.Date.valueOf(date),
                "time", Timestamp.valueOf(time),
                "text", "value");

        assertThat(RowValues.longValue(row, "id")).isEqualTo(7L);
        assertThat(RowValues.intValue(row, "id")).isEqualTo(7);
        assertThat(RowValues.booleanValue(row, "flag")).isTrue();
        assertThat(RowValues.date(row, "date")).isEqualTo(date);
        assertThat(RowValues.dateTime(row, "time")).isEqualTo(time);
        assertThat(RowValues.requiredString(row, "text")).isEqualTo("value");
        assertThat(RowValues.nullableLong(row, "missing")).isNull();
        assertThatThrownBy(() -> RowValues.longValue(row, "text")).isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> RowValues.booleanValue(row, "text")).isInstanceOf(IllegalStateException.class);
    }

    @Test
    void sqlParametersKeepNullsAndRequirePairs() {
        assertThat(SqlParameters.ofNullable("a", 1, "b", null))
                .containsEntry("a", 1).containsKey("b");
        assertThatThrownBy(() -> SqlParameters.ofNullable("a", 1, "b"))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void sqlUpdateRejectsUnsafeIdentifiersAndBuildsParameterizedAssignments() {
        assertThatThrownBy(() -> new SqlUpdate("users;drop", "id", 7))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new SqlUpdate("users", "id", 7).set("bad-name", "x"))
                .isInstanceOf(IllegalArgumentException.class);

        SqlUpdate update = new SqlUpdate("users", "id", 7)
                .set("display_name", "Captain")
                .set("active", true);
        assertThat(update.isEmpty()).isFalse();
        assertThat(update.columns()).containsExactlyInAnyOrder("display_name", "active");
        assertThat(update.sql()).isEqualTo(
                "update users set display_name = :value_display_name, active = :value_active where id = :row_id");
        assertThat(update.parameters()).containsEntry("value_display_name", "Captain")
                .containsEntry("value_active", true)
                .containsEntry("row_id", 7);
        assertThatThrownBy(() -> new SqlUpdate("users", "id", 7).sql())
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void repositorySupportDelegatesEveryJdbcPrimitive() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        JdbcRepositorySupport repository = new JdbcRepositorySupport(jdbc) { };
        Map<String, Object> row = Map.of("id", 1L);
        when(jdbc.query("q", Map.of())).thenReturn(java.util.List.of(row));
        when(jdbc.optional("o", Map.of())).thenReturn(java.util.Optional.of(row));
        when(jdbc.required("r", Map.of())).thenReturn(row);
        when(jdbc.update("u", Map.of())).thenReturn(2);
        when(jdbc.insertReturningId("i", Map.of())).thenReturn(3L);
        when(jdbc.count("c", Map.of())).thenReturn(4L);

        assertThat(repository.query("q", Map.of())).containsExactly(row);
        assertThat(repository.optional("o", Map.of())).contains(row);
        assertThat(repository.required("r", Map.of())).isSameAs(row);
        assertThat(repository.update("u", Map.of())).isEqualTo(2);
        assertThat(repository.insertReturningId("i", Map.of())).isEqualTo(3L);
        assertThat(repository.count("c", Map.of())).isEqualTo(4L);
        verify(jdbc).count("c", Map.of());
    }
}
