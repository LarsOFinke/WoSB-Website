package eu.royalblackwater.api.masterdata;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.contract.MasterDataCategoryRead;
import eu.royalblackwater.api.transport.ContractConversionService;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class MasterDataQueryServiceTest {
    @Test
    void excludesInternalSeedChecksumFromCategoryContract() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        ContractConversionService contracts = mock(ContractConversionService.class);
        when(jdbc.query(anyString(), anyMap())).thenReturn(List.of(Map.of(
                "id", 1L,
                "seed_key", "managed-category",
                "seed_checksum", "internal-checksum",
                "is_seed_overridden", false)));
        when(contracts.convert(anyMap(), eq(MasterDataCategoryRead.class)))
                .thenReturn(mock(MasterDataCategoryRead.class));

        new MasterDataQueryService(jdbc, contracts).categories();

        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> values = ArgumentCaptor.forClass(Map.class);
        verify(contracts).convert(values.capture(), eq(MasterDataCategoryRead.class));
        assertThat(values.getValue()).doesNotContainKey("seed_checksum");
        assertThat(values.getValue()).containsEntry("seed_status", "managed");
    }

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
