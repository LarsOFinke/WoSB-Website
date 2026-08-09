package eu.royalblackwater.api.raidhelper;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperPayloadRenderer;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.service.RaidHelperDeliveryWorker;
import eu.royalblackwater.api.raidhelper.service.RaidHelperDestinationService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperHttpClient;
import eu.royalblackwater.api.raidhelper.service.RaidHelperLinkService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperPolicy;
import eu.royalblackwater.api.raidhelper.service.RaidHelperProbeService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperProfileService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperTemplateService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.FernetSecretBox;
import eu.royalblackwater.api.squads.service.SquadAccessPolicy;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionCallback;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RaidHelperBusinessServicesTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-08-08T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser MEMBER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void profileDestinationAndTemplateAdministrationAreAdminOnly() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        RaidHelperPolicy policy = new RaidHelperPolicy(new ObjectMapper());
        AuditService audit = mock(AuditService.class);
        RaidHelperDtoMapper mapper = mock(RaidHelperDtoMapper.class);

        RaidHelperProfileService profiles = new RaidHelperProfileService(repository, policy, mock(FernetSecretBox.class), audit, CLOCK, mapper);
        RaidHelperDestinationService destinations = new RaidHelperDestinationService(repository, policy, audit, CLOCK, mapper);
        RaidHelperTemplateService templates = new RaidHelperTemplateService(repository, policy, audit, CLOCK, mapper);

        assertEquals(403, assertThrows(ResponseStatusException.class, () -> profiles.list(MEMBER)).getStatusCode().value());
        assertEquals(403, assertThrows(ResponseStatusException.class, () -> destinations.list(MEMBER)).getStatusCode().value());
        assertEquals(403, assertThrows(ResponseStatusException.class, () -> templates.list(MEMBER)).getStatusCode().value());
        verify(repository, never()).query(anyString(), anyMap());
    }

    @Test
    void probeIsAdminOnlyBeforeNetworkAccess() {
        RaidHelperHttpClient client = mock(RaidHelperHttpClient.class);
        RaidHelperProbeService probe = new RaidHelperProbeService(mock(RaidHelperRepository.class), mock(RaidHelperProfileService.class),
                mock(RaidHelperTemplateService.class), client, mock(RaidHelperPayloadRenderer.class), mock(RaidHelperDtoMapper.class), CLOCK);

        ResponseStatusException error = assertThrows(ResponseStatusException.class, () -> probe.profile(MEMBER, 12));

        assertEquals(403, error.getStatusCode().value());
        verify(client, never()).request(any(), anyString(), anyString(), any());
    }

    @Test
    void linkServiceFailsClosedWhenOfficialFleetIsNotConfigured() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        RaidHelperLinkService links = new RaidHelperLinkService(repository, mock(RaidHelperPolicy.class),
                mock(FleetAccessPolicy.class), mock(SquadAccessPolicy.class), CLOCK, mock(RaidHelperDtoMapper.class));
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.empty());

        ResponseStatusException error = assertThrows(ResponseStatusException.class, links::officialFleetId);

        assertEquals(400, error.getStatusCode().value());
    }

    @Test
    void deliveryWorkerStopsCleanlyWhenQueueIsEmpty() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        TransactionTemplate transactions = mock(TransactionTemplate.class);
        doAnswer(invocation -> {
            @SuppressWarnings("unchecked")
            TransactionCallback<Long> callback = invocation.getArgument(0);
            return callback.doInTransaction(null);
        }).when(transactions).execute(any());
        doAnswer(invocation -> null).when(transactions).executeWithoutResult(any());
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.empty());
        RaidHelperHttpClient client = mock(RaidHelperHttpClient.class);
        RaidHelperDeliveryWorker worker = new RaidHelperDeliveryWorker(repository, client, mock(RaidHelperPayloadRenderer.class),
                transactions, CLOCK, mock(RaidHelperDtoMapper.class));

        worker.deliverQueuedLinks();

        verify(repository).optional(anyString(), anyMap());
        verify(client, never()).request(any(), anyString(), anyString(), any());
    }
}
