package eu.royalblackwater.api.ships;

import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.ships.filter.ShipListFilter;
import eu.royalblackwater.api.ships.mapper.ShipMapper;
import eu.royalblackwater.api.ships.repository.ShipRepository;
import eu.royalblackwater.api.ships.service.ShipQueryService;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class ShipQueryServiceTest {
    @Test
    void activeShipsBuildsNormalizedParameterizedFilters() {
        ShipRepository repository = mock(ShipRepository.class);
        ShipMapper mapper = mock(ShipMapper.class);
        Map<String, Object> row = Map.of("id", 7L);
        ShipRead mapped = mock(ShipRead.class);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(row));
        when(mapper.toRead(row)).thenReturn(mapped);

        var filter = new ShipListFilter(new ListFilter("Frigate", 25, 50), 5L, "HEAVY");
        assertThat(new ShipQueryService(repository, mapper).activeShips(filter)).containsExactly(mapped);

        ArgumentCaptor<String> sql = ArgumentCaptor.forClass(String.class);
        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).query(sql.capture(), parameters.capture());
        assertThat(sql.getValue()).contains(":search", ":rate", ":shipType", "order by");
        assertThat(parameters.getValue()).containsEntry("search", "%frigate%")
                .containsEntry("rate", 5L)
                .containsEntry("shipType", "heavy")
                .containsEntry("limit", 25)
                .containsEntry("offset", 50);
    }

    @Test
    void activeShipsOmitsOptionalPredicatesWhenFiltersAreAbsent() {
        ShipRepository repository = mock(ShipRepository.class);
        ShipMapper mapper = mock(ShipMapper.class);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of());

        new ShipQueryService(repository, mapper).activeShips(ShipListFilter.all());

        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).query(anyString(), parameters.capture());
        assertThat(parameters.getValue()).containsOnlyKeys("limit", "offset")
                .containsEntry("limit", 250)
                .containsEntry("offset", 0);
    }

    @Test
    void activeShipMapsPresentRowsAndReturnsNullForMissingShips() {
        ShipRepository repository = mock(ShipRepository.class);
        ShipMapper mapper = mock(ShipMapper.class);
        Map<String, Object> row = Map.of("id", 3L);
        ShipRead mapped = mock(ShipRead.class);
        when(repository.findActive(3L)).thenReturn(Optional.of(row));
        when(repository.findActive(4L)).thenReturn(Optional.empty());
        when(mapper.toRead(row)).thenReturn(mapped);
        ShipQueryService service = new ShipQueryService(repository, mapper);

        assertThat(service.activeShip(3L)).isSameAs(mapped);
        assertThat(service.activeShip(4L)).isNull();
    }
}
