package eu.royalblackwater.api.warehouse;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import eu.royalblackwater.api.warehouse.service.WarehouseResourceService;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class WarehouseResourceServiceTest {
    private static final AuthenticatedUser MEMBER =
            new AuthenticatedUser(8, "member", "user", false, false, false);

    @Test
    void listsActiveResourcesAndCanonicalizesSubmittedNames() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.query(WarehouseQueries.ACTIVE_RESOURCES_SELECT_01, Map.of()))
                .thenReturn(List.of(Map.of("name", "Battlemark"), Map.of("name", "Iron")));
        when(repository.optional(WarehouseQueries.ACTIVE_RESOURCE_BY_NAME_SELECT_01, Map.of("name", "iron")))
                .thenReturn(Optional.of(Map.of("name", "Iron")));
        WarehouseResourceService service = new WarehouseResourceService(repository);

        assertThat(service.active(MEMBER)).containsExactly("Battlemark", "Iron");
        assertThat(service.requireActiveName(" iron ")).isEqualTo("Iron");
    }

    @Test
    void rejectsUnknownResources() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.optional(WarehouseQueries.ACTIVE_RESOURCE_BY_NAME_SELECT_01,
                Map.of("name", "Unknown"))).thenReturn(Optional.empty());

        assertThatThrownBy(() -> new WarehouseResourceService(repository).requireActiveName("Unknown"))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("active warehouse resource");
    }
}
