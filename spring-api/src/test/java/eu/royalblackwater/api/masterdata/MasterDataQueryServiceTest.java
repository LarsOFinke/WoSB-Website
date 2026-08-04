package eu.royalblackwater.api.masterdata;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.transport.ContractConversionService;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class MasterDataQueryServiceTest {
    @Test
    void loadsShipRelationsWithAFixedNumberOfQueries() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        ContractConversionService contracts = mock(ContractConversionService.class);
        when(jdbc.query(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (sql.startsWith("select * from ships order by")) {
                return List.of(
                        Map.of("id", 1L, "seed_key", "ship-one", "is_seed_overridden", false),
                        Map.of("id", 2L, "seed_key", "ship-two", "is_seed_overridden", false));
            }
            return List.of();
        });

        assertThat(new MasterDataQueryService(jdbc, contracts).ships()).hasSize(2);
        verify(jdbc, times(5)).query(anyString(), anyMap());
    }
}
