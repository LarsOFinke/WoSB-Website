package eu.royalblackwater.api.masterdata;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.MasterDataCategoryUpdate;
import eu.royalblackwater.api.masterdata.mapper.MasterDataDtoMapper;
import eu.royalblackwater.api.masterdata.repository.MasterDataRepository;
import eu.royalblackwater.api.masterdata.repository.SeedCatalog;
import eu.royalblackwater.api.masterdata.service.MasterDataMutationService;
import eu.royalblackwater.api.masterdata.service.MasterDataQueryService;
import eu.royalblackwater.api.masterdata.service.ReferenceDataSeeder;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.atLeast;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class MasterDataMutationServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ACTOR =
            new AuthenticatedUser(7, "captain", "admin", true, true, true);

    @Test
    void mutationServiceRejectsUpdatesForMissingRecords() {
        MasterDataRepository repository = mock(MasterDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        MasterDataMutationService service = new MasterDataMutationService(repository,
                mock(MasterDataQueryService.class), mock(ReferenceDataSeeder.class), mock(AuditService.class), CLOCK,
                mock(MasterDataDtoMapper.class));

        assertThatThrownBy(() -> service.updateCategory(ACTOR, 99L,
                new MasterDataCategoryUpdate(true, "Missing", 1L)))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Master-data record not found");
    }

    @Test
    void mutationServiceRefusesToDeleteCategoriesThatStillContainOptions() {
        MasterDataRepository repository = mock(MasterDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L, 2L);
        MasterDataMutationService service = new MasterDataMutationService(repository,
                mock(MasterDataQueryService.class), mock(ReferenceDataSeeder.class), mock(AuditService.class), CLOCK,
                mock(MasterDataDtoMapper.class));

        assertThatThrownBy(() -> service.deleteCategory(ACTOR, 5L))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("still contains options");
    }

    @Test
    void referenceDataSeederSynchronizesAnEmptyCatalogAndStillMaintainsSystemBuildRoles() {
        SeedCatalog catalog = mock(SeedCatalog.class);
        when(catalog.systemRoles()).thenReturn(Map.of());
        when(catalog.systemFleets()).thenReturn(List.of());
        when(catalog.definitions()).thenReturn(Map.of());
        when(catalog.categories()).thenReturn(List.of());
        when(catalog.options()).thenReturn(List.of());
        when(catalog.ships()).thenReturn(List.of());
        when(catalog.buildRules()).thenReturn(Map.of());
        MasterDataRepository repository = mock(MasterDataRepository.class);
        ReferenceDataSeeder seeder = new ReferenceDataSeeder(catalog, repository, new ObjectMapper(), CLOCK);

        ReferenceDataSeeder.SeedResult result = seeder.synchronize(true);

        assertThat(result).isEqualTo(new ReferenceDataSeeder.SeedResult(0, 0, 0, 0));
        verify(repository, atLeast(5)).update(anyString(), anyMap());
    }
}
