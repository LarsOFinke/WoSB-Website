package eu.royalblackwater.api.raidhelper;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.RaidHelperDestinationTestRequest;
import eu.royalblackwater.api.dto.RaidHelperDestinationWrite;
import eu.royalblackwater.api.dto.RaidHelperDispatchSelection;
import eu.royalblackwater.api.dto.RaidHelperProfileCreate;
import eu.royalblackwater.api.dto.RaidHelperProfileWrite;
import eu.royalblackwater.api.dto.RaidHelperTemplateWrite;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperConnectionDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperDeliveryDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperEventDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperJsonPayloadDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperTemplateConfigDto;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperPayloadRenderer;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperDestinationQueries;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperLinkQueries;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperProbeQueries;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperProfileQueries;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperTemplateQueries;
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
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.transaction.support.TransactionCallback;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RaidHelperCoverageTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ADMIN = new AuthenticatedUser(1, "admin", "admin", true, true, true);
    private static final RaidHelperPolicy POLICY = new RaidHelperPolicy(new ObjectMapper());
    private static final RaidHelperDtoMapper MAPPER = new RaidHelperDtoMapper();

    @Test
    void successfulAdminCreatePathsInstantiateValidatedRecordsAndDestinationBuilder() {
        RaidHelperRepository repository = repositoryForCrud();
        FernetSecretBox secrets = mock(FernetSecretBox.class);
        when(secrets.encrypt(anyString())).thenReturn("encrypted-secret");
        when(repository.insertReturningId(anyString(), anyMap())).thenReturn(1L, 2L, 3L);
        AuditService audit = mock(AuditService.class);

        RaidHelperProfileService profiles = new RaidHelperProfileService(repository, POLICY, secrets, audit, CLOCK, MAPPER);
        RaidHelperDestinationService destinations = new RaidHelperDestinationService(repository, POLICY, audit, CLOCK, MAPPER);
        RaidHelperTemplateService templates = new RaidHelperTemplateService(repository, POLICY, audit, CLOCK, MAPPER);

        var profile = profiles.create(ADMIN, new RaidHelperProfileCreate(
                RaidHelperPolicy.DEFAULT_API_URL, "Bearer 'abcdefgh123'", "12345", true,
                "Primary", "12345", "UTC"));
        var destination = destinations.create(ADMIN, new RaidHelperDestinationWrite(
                List.of("training", "meeting"), "54321", true, false, "Fleet Ops", 1L, "fleet", null));
        var template = templates.create(ADMIN, new RaidHelperTemplateWrite(
                "Announcement", List.of("training"), "Description", true, true, "Default",
                "{\"title\":\"{{event.title}}\",\"date\":\"{{event.date}}\",\"time\":\"{{event.time}}\"}",
                1L, "", "both", "{{event.title}}", false));

        assertThat(profile.id()).isEqualTo(1L);
        assertThat(destination.id()).isEqualTo(2L);
        assertThat(template.id()).isEqualTo(3L);

        FleetAccessPolicy fleets = mock(FleetAccessPolicy.class);
        when(fleets.canManageFleet(ADMIN, 77L)).thenReturn(true);
        RaidHelperLinkService links = new RaidHelperLinkService(repository, POLICY, fleets,
                mock(SquadAccessPolicy.class), CLOCK, MAPPER);
        assertThat(links.options(ADMIN, "training", null)).hasSize(1);
    }

    @Test
    void profileUpdateCoversReplacementRotationLinkedServerAndDuplicateBranches() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(profileRow()));
        FernetSecretBox secrets = mock(FernetSecretBox.class);
        when(secrets.encrypt(anyString())).thenReturn("new-encrypted");
        when(secrets.needsRotation("encrypted-secret")).thenReturn(true);
        when(secrets.rotate("encrypted-secret")).thenReturn("rotated");
        RaidHelperProfileService service = new RaidHelperProfileService(repository, POLICY, secrets,
                mock(AuditService.class), CLOCK, MAPPER);

        service.update(ADMIN, 1L, new RaidHelperProfileWrite(RaidHelperPolicy.DEFAULT_API_URL,
                "abcdefgh123", null, true, "Primary", "12345", "UTC"));
        service.update(ADMIN, 1L, new RaidHelperProfileWrite(RaidHelperPolicy.DEFAULT_API_URL,
                null, null, true, "Primary", "12345", "UTC"));

        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        assertThatThrownBy(() -> service.update(ADMIN, 1L, new RaidHelperProfileWrite(
                RaidHelperPolicy.DEFAULT_API_URL, null, null, true, "Primary", "99999", "UTC")))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("cannot change its server ID");

        RaidHelperRepository duplicate = mock(RaidHelperRepository.class);
        when(duplicate.insertReturningId(anyString(), anyMap())).thenThrow(new DataIntegrityViolationException("duplicate"));
        FernetSecretBox duplicateSecrets = mock(FernetSecretBox.class);
        when(duplicateSecrets.encrypt(anyString())).thenReturn("encrypted");
        RaidHelperProfileService duplicateService = new RaidHelperProfileService(duplicate, POLICY, duplicateSecrets,
                mock(AuditService.class), CLOCK, MAPPER);
        assertThatThrownBy(() -> duplicateService.create(ADMIN, new RaidHelperProfileCreate(
                null, "abcdefgh", null, null, "Primary", "12345", null)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("already exists");
    }

    @Test
    void destinationAndTemplateValidationCoverScopeReferenceLinkAndDuplicateBranches() {
        RaidHelperRepository repository = repositoryForCrud();
        RaidHelperDestinationService destinations = new RaidHelperDestinationService(repository, POLICY,
                mock(AuditService.class), CLOCK, MAPPER);
        RaidHelperTemplateService templates = new RaidHelperTemplateService(repository, POLICY,
                mock(AuditService.class), CLOCK, MAPPER);

        assertThatThrownBy(() -> destinations.create(ADMIN, new RaidHelperDestinationWrite(
                List.of(), "54321", true, false, "Bad", 1L, "fleet", 5L)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("cannot reference a squad");
        assertThatThrownBy(() -> destinations.create(ADMIN, new RaidHelperDestinationWrite(
                List.of(), "54321", true, false, "Bad", 1L, "squad", null)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("require a squad");
        assertThatThrownBy(() -> destinations.create(ADMIN, new RaidHelperDestinationWrite(
                List.of(), "54321", true, false, "Bad", 1L, "invalid", null)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Invalid destination scope");

        RaidHelperRepository linked = repositoryForCrud();
        when(linked.count(RaidHelperDestinationQueries.HAS_LINKS_SELECT_01, Map.of("id", 2L))).thenReturn(1L);
        RaidHelperDestinationService linkedDestinations = new RaidHelperDestinationService(linked, POLICY,
                mock(AuditService.class), CLOCK, MAPPER);
        assertThatThrownBy(() -> linkedDestinations.update(ADMIN, 2L, new RaidHelperDestinationWrite(
                List.of("training"), "99999", true, false, "Moved", 1L, "fleet", null)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("cannot change profile, channel or scope");
        assertThatThrownBy(() -> linkedDestinations.delete(ADMIN, 2L))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("cannot be deleted");

        assertThatThrownBy(() -> templates.create(ADMIN, new RaidHelperTemplateWrite(
                null, List.of(), null, true, false, "Bad", null, 1L, null, "invalid", null, false)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Invalid template scope");

        RaidHelperRepository linkedTemplateRepo = repositoryForCrud();
        when(linkedTemplateRepo.count(RaidHelperTemplateQueries.HAS_LINKS_SELECT_01, Map.of("id", 3L))).thenReturn(1L);
        RaidHelperTemplateService linkedTemplates = new RaidHelperTemplateService(linkedTemplateRepo, POLICY,
                mock(AuditService.class), CLOCK, MAPPER);
        assertThatThrownBy(() -> linkedTemplates.update(ADMIN, 3L, new RaidHelperTemplateWrite(
                null, List.of("training"), null, true, false, "Moved",
                "{\"title\":\"x\",\"date\":\"x\",\"time\":\"x\"}", 2L, "", "both", null, false)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("cannot move to another profile");
        assertThatThrownBy(() -> linkedTemplates.delete(ADMIN, 3L))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("cannot be deleted");
    }

    @Test
    void linkConfigurationCoversInsertUpdateDeleteCancellationRetryAndSquadManagement() {
        RaidHelperRepository repository = repositoryForCrud();
        FleetAccessPolicy fleets = mock(FleetAccessPolicy.class);
        SquadAccessPolicy squads = mock(SquadAccessPolicy.class);
        when(fleets.canManageFleet(ADMIN, 77L)).thenReturn(true);
        when(squads.canManage(ADMIN, 5L, 77L)).thenReturn(true);
        RaidHelperLinkService links = new RaidHelperLinkService(repository, POLICY, fleets, squads, CLOCK, MAPPER);

        when(repository.query(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (RaidHelperLinkQueries.OPTIONS_SELECT_01.equals(sql)) return List.of(optionRow());
            if (RaidHelperLinkQueries.CONFIGURE_SELECT_01.equals(sql)) {
                return List.of(existingLink(1L, 2L, null), existingLink(2L, 99L, null), existingLink(3L, 100L, "evt-old"));
            }
            if (RaidHelperLinkQueries.LINKS_BY_EVENT_IDS_SELECT_01.equals(sql)) return List.of(eventLinkRow());
            return List.of();
        });
        links.configure(10L, "training", null,
                List.of(new RaidHelperDispatchSelection(2L, "67890", 3L)), ADMIN);
        assertThat(links.links(10L)).hasSize(1);
        assertThat(links.linksByEventIds(List.of())).isEmpty();
        links.queueCancellation(10L);
        when(repository.update(eq(RaidHelperLinkQueries.QUEUE_RETRY_UPDATE_01), anyMap()))
                .thenReturn(1);
        links.queueRetry(10L);

        when(repository.optional(RaidHelperLinkQueries.CAN_MANAGE_SELECT_01, Map.of("id", 5L)))
                .thenReturn(Optional.of(Map.of("is_active", true, "fleet_id", 77L)));
        assertThat(links.canManage(ADMIN, 5L)).isTrue();

        when(repository.update(eq(RaidHelperLinkQueries.QUEUE_RETRY_UPDATE_01), anyMap()))
                .thenReturn(0);
        assertThatThrownBy(() -> links.queueRetry(11L))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("no Raid-Helper destinations");
    }

    @Test
    void probeCoversProfileAndMinimalDestinationSuccessFailureAndMissingLeader() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        RaidHelperProfileService profiles = mock(RaidHelperProfileService.class);
        RaidHelperTemplateService templates = mock(RaidHelperTemplateService.class);
        RaidHelperHttpClient client = mock(RaidHelperHttpClient.class);
        RaidHelperPayloadRenderer renderer = mock(RaidHelperPayloadRenderer.class);
        RaidHelperConnectionDto connection = new RaidHelperConnectionDto(RaidHelperPolicy.DEFAULT_API_URL, "encrypted", "12345");
        when(profiles.connection(1L)).thenReturn(connection);
        when(client.request(connection, "GET", "/servers/12345/events", null))
                .thenReturn(new RaidHelperHttpClient.Response(200, Map.of()));
        RaidHelperProbeService probe = new RaidHelperProbeService(repository, profiles, templates, client, renderer, MAPPER, CLOCK);
        assertThat(probe.profile(ADMIN, 1L).ok()).isTrue();

        when(repository.required(RaidHelperProbeQueries.DESTINATION_WITH_PROFILE_SELECT_01, Map.of("id", 2L)))
                .thenReturn(destinationConfigRow("12345"));
        when(client.request(any(), org.mockito.ArgumentMatchers.eq("POST"), anyString(), any()))
                .thenReturn(new RaidHelperHttpClient.Response(201, Map.of("id", "evt-1")));
        when(client.externalId(any())).thenReturn("evt-1");
        when(client.request(any(), org.mockito.ArgumentMatchers.eq("DELETE"), anyString(), org.mockito.ArgumentMatchers.isNull()))
                .thenReturn(new RaidHelperHttpClient.Response(204, null));
        assertThat(probe.destination(ADMIN, 2L, new RaidHelperDestinationTestRequest(null, true)).ok()).isTrue();

        when(repository.required(RaidHelperProbeQueries.DESTINATION_WITH_PROFILE_SELECT_01, Map.of("id", 3L)))
                .thenReturn(destinationConfigRow(null));
        assertThat(probe.destination(ADMIN, 3L, new RaidHelperDestinationTestRequest(null, true)).ok()).isFalse();

        when(client.request(connection, "GET", "/servers/12345/events", null)).thenThrow(new RuntimeException("down"));
        assertThat(probe.profile(ADMIN, 1L).ok()).isFalse();
    }

    @Test
    void deliveryWorkerCoversCreateSuccessAndDeleteWithoutExternalId() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        TransactionTemplate transactions = transactions();
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("id", 1L)), Optional.<Map<String, Object>>empty());
        RaidHelperDtoMapper mapper = mock(RaidHelperDtoMapper.class);
        RaidHelperDeliveryDto delivery = mock(RaidHelperDeliveryDto.class);
        when(mapper.delivery(anyMap())).thenReturn(delivery);
        when(repository.required(anyString(), anyMap())).thenReturn(Map.of("id", 1L));
        when(delivery.operation()).thenReturn("create");
        when(delivery.destinationActive()).thenReturn(true);
        when(delivery.profileActive()).thenReturn(true);
        when(delivery.templateActive()).thenReturn(true);
        when(delivery.defaultLeaderId()).thenReturn("12345");
        when(delivery.serverId()).thenReturn("12345");
        when(delivery.channelId()).thenReturn("54321");
        RaidHelperConnectionDto connection = new RaidHelperConnectionDto(RaidHelperPolicy.DEFAULT_API_URL, "encrypted", "12345");
        when(delivery.connection()).thenReturn(connection);
        RaidHelperEventDto event = new RaidHelperEventDto(1L, "Event", "training", null, null,
                LocalDateTime.of(2030, 1, 15, 13, 0), LocalDateTime.of(2030, 1, 15, 14, 0), false, null, null);
        RaidHelperTemplateConfigDto template = new RaidHelperTemplateConfigDto(1L, 1L, true, "UTC", null,
                "{{event.title}}", "", "", "{}");
        when(delivery.event()).thenReturn(event);
        when(delivery.template()).thenReturn(template);
        RaidHelperPayloadRenderer renderer = mock(RaidHelperPayloadRenderer.class);
        RaidHelperJsonPayloadDto payload = RaidHelperJsonPayloadDto.of(Map.of("title", "Event"));
        when(renderer.render(event, template, "12345")).thenReturn(payload);
        RaidHelperHttpClient client = mock(RaidHelperHttpClient.class);
        when(client.request(connection, "POST", "/servers/12345/channels/54321/event", payload))
                .thenReturn(new RaidHelperHttpClient.Response(201, Map.of("id", "evt-1")));
        when(client.externalId(any())).thenReturn("evt-1");

        new RaidHelperDeliveryWorker(repository, client, renderer, transactions, CLOCK, mapper).deliverQueuedLinks();
        verify(repository, org.mockito.Mockito.atLeastOnce()).update(anyString(), anyMap());

        RaidHelperRepository deleteRepository = mock(RaidHelperRepository.class);
        when(deleteRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("id", 2L)), Optional.<Map<String, Object>>empty());
        when(deleteRepository.required(anyString(), anyMap())).thenReturn(Map.of("id", 2L));
        RaidHelperDtoMapper deleteMapper = mock(RaidHelperDtoMapper.class);
        RaidHelperDeliveryDto delete = mock(RaidHelperDeliveryDto.class);
        when(deleteMapper.delivery(anyMap())).thenReturn(delete);
        when(delete.operation()).thenReturn("delete");
        new RaidHelperDeliveryWorker(deleteRepository, mock(RaidHelperHttpClient.class), mock(RaidHelperPayloadRenderer.class),
                transactions(), CLOCK, deleteMapper).deliverQueuedLinks();
        verify(deleteRepository, org.mockito.Mockito.atLeastOnce()).update(anyString(), anyMap());
    }

    private static RaidHelperRepository repositoryForCrud() {
        RaidHelperRepository repository = mock(RaidHelperRepository.class);
        when(repository.count(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (RaidHelperDestinationQueries.VALIDATE_SELECT_01.equals(sql)
                    || RaidHelperDestinationQueries.VALIDATE_SELECT_02.equals(sql)
                    || RaidHelperTemplateQueries.VALIDATE_SELECT_01.equals(sql)) return 1L;
            return 0L;
        });
        when(repository.optional(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (RaidHelperProfileQueries.ROW_SELECT_01.equals(sql)) return Optional.of(profileRow());
            if (RaidHelperDestinationQueries.ROW_SELECT_01.equals(sql)
                    || (RaidHelperDestinationQueries.BASE_QUERY + RaidHelperDestinationQueries.DETAIL_WHERE_01).equals(sql)) {
                return Optional.of(destinationRow());
            }
            if (RaidHelperTemplateQueries.ROW_SELECT_01.equals(sql)
                    || (RaidHelperTemplateQueries.BASE_QUERY + RaidHelperTemplateQueries.DETAIL_WHERE_01).equals(sql)) {
                return Optional.of(templateRow());
            }
            if (RaidHelperLinkQueries.OFFICIAL_FLEET_ID_SELECT_01.equals(sql)) return Optional.of(Map.of("id", 77L));
            return Optional.of(profileRow());
        });
        when(repository.query(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (RaidHelperDestinationQueries.READ_SELECT_01.equals(sql)
                    || RaidHelperTemplateQueries.READ_SELECT_01.equals(sql)) return List.of(Map.of("category", "training"));
            if (RaidHelperLinkQueries.OPTIONS_SELECT_01.equals(sql)) return List.of(optionRow());
            if (RaidHelperProfileQueries.LIST_SELECT_01.equals(sql)) return List.of(profileRow());
            return List.of();
        });
        return repository;
    }

    private static TransactionTemplate transactions() {
        TransactionTemplate transactions = mock(TransactionTemplate.class);
        doAnswer(invocation -> {
            @SuppressWarnings("unchecked") TransactionCallback<Object> callback = invocation.getArgument(0);
            return callback.doInTransaction(null);
        }).when(transactions).execute(any());
        doAnswer(invocation -> {
            java.util.function.Consumer<org.springframework.transaction.TransactionStatus> callback = invocation.getArgument(0);
            callback.accept(null);
            return null;
        }).when(transactions).executeWithoutResult(any());
        return transactions;
    }

    private static Map<String, Object> profileRow() {
        Map<String, Object> row = baseRow();
        row.put("id", 1L);
        row.put("name", "Primary");
        row.put("server_id", "12345");
        row.put("api_base_url", RaidHelperPolicy.DEFAULT_API_URL);
        row.put("api_key_encrypted", "encrypted-secret");
        row.put("default_leader_id", "12345");
        row.put("is_active", true);
        row.put("created_by_username", "admin");
        row.put("timezone", "UTC");
        return row;
    }

    private static Map<String, Object> destinationRow() {
        Map<String, Object> row = profileRow();
        row.put("id", 2L);
        row.put("profile_id", 1L);
        row.put("profile_name", "Primary");
        row.put("name", "Fleet Ops");
        row.put("channel_id", "54321");
        row.put("scope_type", "fleet");
        row.put("squad_id", null);
        row.put("squad_name", null);
        row.put("is_default", false);
        return row;
    }

    private static Map<String, Object> templateRow() {
        Map<String, Object> row = profileRow();
        row.put("id", 3L);
        row.put("profile_id", 1L);
        row.put("profile_name", "Primary");
        row.put("name", "Default");
        row.put("raid_template_id", "");
        row.put("scope_type", "both");
        row.put("title_template", "{{event.title}}");
        row.put("description_template", "{{event.description}}");
        row.put("announcement_template", "");
        row.put("payload_template_json", "{\"title\":\"{{event.title}}\",\"date\":\"{{event.date}}\",\"time\":\"{{event.time}}\"}");
        row.put("uses_premium_features", false);
        row.put("is_default", true);
        return row;
    }

    private static Map<String, Object> optionRow() {
        Map<String, Object> row = templateRow();
        row.put("destination_id", 2L);
        row.put("destination_name", "Fleet Ops");
        row.put("destination_default", true);
        row.put("template_id", 3L);
        row.put("template_name", "Default");
        row.put("template_default", true);
        row.put("scope_type", "fleet");
        row.put("channel_id", "54321");
        return row;
    }

    private static Map<String, Object> existingLink(long id, long destinationId, String externalId) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", id);
        row.put("destination_id", destinationId);
        row.put("external_event_id", externalId);
        return row;
    }

    private static Map<String, Object> eventLinkRow() {
        Map<String, Object> row = baseRow();
        row.put("event_id", 10L);
        row.put("destination_id", 2L);
        row.put("destination_name", "Fleet Ops");
        row.put("external_event_id", "evt-1");
        row.put("id", 1L);
        row.put("last_operation", "update");
        row.put("profile_name", "Primary");
        row.put("status", "synced");
        row.put("template_id", 3L);
        row.put("template_name", "Default");
        return row;
    }

    private static Map<String, Object> destinationConfigRow(String leaderId) {
        Map<String, Object> row = destinationRow();
        row.put("default_leader_id", leaderId);
        row.put("timezone", "UTC");
        return row;
    }

    private static Map<String, Object> baseRow() {
        Map<String, Object> row = new HashMap<>();
        row.put("created_at", LocalDateTime.of(2030, 1, 15, 10, 0));
        row.put("updated_at", LocalDateTime.of(2030, 1, 15, 11, 0));
        row.put("is_active", true);
        return row;
    }
}
