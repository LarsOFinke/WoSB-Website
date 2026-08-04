package eu.royalblackwater.api.account;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class UserReferenceServiceTest {
    @Test
    void resolvesAListOfOwnersWithOneBatchQuery() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.query(contains("where u.id in (:ids)"), anyMap())).thenReturn(List.of(
                Map.of("id", 1L, "display_name", "Anne"),
                Map.of("id", 2L, "display_name", "Blackbeard")));

        Map<Long, ?> result = new UserReferenceService(jdbc).readMany(List.of(2L, 1L, 2L));

        assertThat(result).containsOnlyKeys(1L, 2L);
        verify(jdbc).query(contains("where u.id in (:ids)"), anyMap());
    }
}
