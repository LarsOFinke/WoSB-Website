package eu.royalblackwater.api.account;

import eu.royalblackwater.api.account.service.UserReferenceService;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class UserReferenceServiceTest {
    @Test
    void resolvesAListOfOwnersWithOneBatchQuery() {
        AccountDataRepository repository = mock(AccountDataRepository.class);
        when(repository.query(contains("where u.id in (:ids)"), anyMap())).thenReturn(List.of(
                Map.of("id", 1L, "display_name", "Anne"),
                Map.of("id", 2L, "display_name", "Blackbeard")));

        Map<Long, ?> result = new UserReferenceService(repository).readMany(List.of(2L, 1L, 2L));

        assertThat(result).containsOnlyKeys(1L, 2L);
        verify(repository).query(contains("where u.id in (:ids)"), anyMap());
    }
}
