package eu.royalblackwater.api.masterdata;

import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.masterdata.mapper.MasterDataDtoMapper;
import eu.royalblackwater.api.masterdata.repository.MasterDataRepository;
import eu.royalblackwater.api.masterdata.service.MasterDataQueryService;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class MasterDataQueryServiceTest {
    @Test
    void mapsManagedCategoryWithoutLeakingInternalSeedChecksum() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", 1L);
        row.put("key", "managed-category");
        row.put("label", "Managed category");
        row.put("seed_key", "managed-category");
        row.put("seed_checksum", "internal-checksum");
        row.put("is_seed_overridden", false);
        row.put("created_at", LocalDateTime.of(2026, 8, 7, 10, 0));
        row.put("updated_at", LocalDateTime.of(2026, 8, 7, 10, 0));

        MasterDataCategoryRead result = new MasterDataDtoMapper().category(row);

        assertThat(result.seedStatus()).isEqualTo("managed");
        assertThat(result.key()).isEqualTo("managed-category");
    }

    @Test
    void loadsShipRelationsWithAFixedNumberOfQueries() {
        MasterDataRepository repository = mock(MasterDataRepository.class);
        when(repository.query(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (sql.startsWith("select * from ships order by")) {
                return List.of(shipRow(1L, "ship-one"), shipRow(2L, "ship-two"));
            }
            return List.of();
        });

        assertThat(new MasterDataQueryService(repository, new MasterDataDtoMapper()).ships()).hasSize(2);
        verify(repository, times(5)).query(anyString(), anyMap());
    }

    private static Map<String, Object> shipRow(long id, String seedKey) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id);
        row.put("name", "Ship " + id);
        row.put("rate", 5L);
        row.put("ship_type", "frigate");
        row.put("seed_key", seedKey);
        row.put("is_seed_overridden", false);
        row.put("created_at", LocalDateTime.of(2026, 8, 7, 10, 0));
        row.put("updated_at", LocalDateTime.of(2026, 8, 7, 10, 0));
        return row;
    }
}
