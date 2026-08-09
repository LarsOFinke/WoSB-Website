package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.dto.BuildEffects;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildPageResult;
import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.builds.dto.BuildSlotSelection;
import eu.royalblackwater.api.builds.dto.UpgradeSlotAccess;
import eu.royalblackwater.api.builds.mapper.BuildAssembler;
import eu.royalblackwater.api.builds.repository.BuildCatalogRepository;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.BuildRepository;
import eu.royalblackwater.api.dto.BuildRoleCreate;
import eu.royalblackwater.api.dto.ShipStats;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class BuildServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ACTOR =
            new AuthenticatedUser(7, "captain", "admin", true, true, true);

    @Test
    void roleAdministrationRejectsInvalidSlugsAndProtectsTheLastRole() {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        BuildRoleAdministrationService service = new BuildRoleAdministrationService(
                repository, mock(AuditService.class), CLOCK);

        assertThatThrownBy(() -> service.create(new BuildRoleCreate("Role", null, "not valid!", 10L), ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Invalid build role slug");

        when(repository.count(any(), any())).thenReturn(1L);
        assertThatThrownBy(() -> service.delete("member", ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("At least one build role");
        verify(repository, never()).update(org.mockito.ArgumentMatchers.contains("delete"), any());
    }

    @Test
    void buildServiceNormalizesPaginationAndRejectsMissingDeletes() {
        BuildRepository builds = mock(BuildRepository.class);
        BuildAssembler assembler = mock(BuildAssembler.class);
        BuildPageResult page = mock(BuildPageResult.class);
        when(builds.page(null, null, null, null, 7L, 100L, 0L)).thenReturn(page);
        BuildService service = new BuildService(builds, mock(BuildValidationService.class), assembler,
                mock(BuildDataRepository.class), mock(BuildPrintoutService.class), mock(AuditService.class), CLOCK);

        service.list(null, null, null, 9_999, -20, ACTOR);
        verify(builds).page(null, null, null, null, 7L, 100L, 0L);
        verify(assembler).page(page);

        when(builds.deleteOwned(99, 7)).thenReturn(false);
        assertThatThrownBy(() -> service.deleteOwned(99, ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Build not found");
    }

    @Test
    void buildServiceDeduplicatesBulkIdsAndRequiresEveryRequestedBuild() {
        BuildRepository builds = mock(BuildRepository.class);
        BuildAssembler assembler = mock(BuildAssembler.class);
        BuildService service = new BuildService(builds, mock(BuildValidationService.class), assembler,
                mock(BuildDataRepository.class), mock(BuildPrintoutService.class), mock(AuditService.class), CLOCK);
        when(builds.findAll(List.of(4L, 5L), 7L)).thenReturn(List.of());

        assertThatThrownBy(() -> service.getMany(java.util.Arrays.asList(4L, null, 4L, -1L, 5L), ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Build not found");
        verify(builds).findAll(List.of(4L, 5L), 7L);
    }

    @Test
    void statsServiceCalculatesAStableEmptySlotSnapshot() {
        BuildEffectService effects = mock(BuildEffectService.class);
        UpgradeSlotService slots = mock(UpgradeSlotService.class);
        BuildStatCalculator calculator = mock(BuildStatCalculator.class);
        BuildPayload payload = new BuildPayload("test", "balanced", 1L, List.of(), null,
                java.util.Arrays.asList(null, null, null, null, null, null, null, null), null, false, false,
                10L, 0L, 0L, 0L, List.of(), List.of(), List.of(), List.of(), List.of(), List.of(),
                List.of(), List.of(), List.of(), List.of(), null);
        BuildShipSnapshot ship = new BuildShipSnapshot(null, 4, 20, 5, false, Map.of(), null, Map.of());
        BuildFeatureSnapshot feature = new BuildFeatureSnapshot(1L, 0, Map.of());
        BuildEffects resolved = new BuildEffects(List.of(), Map.of());
        UpgradeSlotAccess access = new UpgradeSlotAccess(4, false, false, false, false, 0, 0, 0, 4);
        when(effects.resolve(payload, ship, feature, List.of())).thenReturn(resolved);
        when(slots.calculate(ship, feature, List.of())).thenReturn(access);
        when(calculator.calculate(Map.of(), Map.of(), List.of())).thenReturn(List.of());
        when(calculator.effectiveStats(List.of())).thenReturn(Map.of());

        ShipStats result = new BuildStatsService(effects, slots, calculator)
                .calculate(payload, ship, feature, List.of());

        assertThat(result).isNotNull();
        verify(effects).resolve(payload, ship, feature, List.of());
        verify(slots).calculate(ship, feature, List.of());
    }


    @Test
    void statsServiceNormalizesIntegralSpecialistDifferencesToLongs() {
        BuildEffectService effects = mock(BuildEffectService.class);
        UpgradeSlotService slots = mock(UpgradeSlotService.class);
        BuildStatCalculator calculator = mock(BuildStatCalculator.class);
        BuildPayload payload = new BuildPayload("test", "balanced", 1L, List.of(), null,
                java.util.Arrays.asList(null, null, null, null, null, null, null, null), null, false, false,
                10L, 0L, 0L, 0L, List.of(), List.of(), List.of(), List.of(), List.of(), List.of(),
                List.of(), List.of(), List.of(), List.of(), null);
        BuildShipSnapshot ship = new BuildShipSnapshot(null, 4, 20, 5, false, Map.of(), null, Map.of());
        BuildFeatureSnapshot feature = new BuildFeatureSnapshot(1L, 0, Map.of());
        BuildSlotSelection specialist = mock(BuildSlotSelection.class);
        when(specialist.type()).thenReturn("special_crew");
        BuildEffects all = new BuildEffects(List.of(Map.of("armor", 3.0)), Map.of("armor", 3.0));
        BuildEffects without = new BuildEffects(List.of(), Map.of());
        UpgradeSlotAccess access = new UpgradeSlotAccess(4, false, false, false, false, 0, 0, 0, 4);
        when(effects.resolve(payload, ship, feature, List.of(specialist))).thenReturn(all);
        when(effects.resolve(payload, ship, feature, List.of())).thenReturn(without);
        when(slots.calculate(ship, feature, List.of(specialist))).thenReturn(access);
        when(calculator.calculate(Map.of(), Map.of("armor", 3.0), List.of(Map.of("armor", 3.0))))
                .thenReturn(List.of());
        when(calculator.effectiveStats(List.of())).thenReturn(Map.of());

        ShipStats result = new BuildStatsService(effects, slots, calculator)
                .calculate(payload, ship, feature, List.of(specialist));

        assertThat(result.specialCrewEffects()).containsEntry("armor", 3L);
    }

    @Test
    void validationRejectsUnknownBuildRolesBeforeCatalogLookup() {
        BuildCatalogRepository catalog = mock(BuildCatalogRepository.class);
        BuildDataRepository repository = mock(BuildDataRepository.class);
        BuildPayload payload = mock(BuildPayload.class);
        when(payload.type()).thenReturn("missing-role");
        when(repository.count(any(), any())).thenReturn(0L);
        BuildValidationService service = new BuildValidationService(catalog, repository,
                mock(BuildEffectService.class), mock(UpgradeSlotService.class));

        assertThatThrownBy(() -> service.prepare(payload))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("build role does not exist");
        verify(catalog, never()).ship(anyLong());
    }
}
