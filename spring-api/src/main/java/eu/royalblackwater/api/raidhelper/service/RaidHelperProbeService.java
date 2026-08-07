package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.dto.RaidHelperDestinationTestRequest;
import eu.royalblackwater.api.dto.RaidHelperProfileTestResult;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperConnectionDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperDestinationConfigDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperEventDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperJsonPayloadDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperTemplateConfigDto;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperPayloadRenderer;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperProbeQueries;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.springframework.stereotype.Service;

import static eu.royalblackwater.api.persistence.RowValues.requiredString;

@Service
public class RaidHelperProbeService {
    private final RaidHelperRepository repository;
    private final RaidHelperProfileService profiles;
    private final RaidHelperTemplateService templates;
    private final RaidHelperHttpClient client;
    private final RaidHelperPayloadRenderer renderer;
    private final RaidHelperDtoMapper mapper;
    private final Clock clock;

    public RaidHelperProbeService(RaidHelperRepository repository, RaidHelperProfileService profiles,
                                  RaidHelperTemplateService templates, RaidHelperHttpClient client,
                                  RaidHelperPayloadRenderer renderer, RaidHelperDtoMapper mapper, Clock clock) {
        this.repository = repository;
        this.profiles = profiles;
        this.templates = templates;
        this.client = client;
        this.renderer = renderer;
        this.mapper = mapper;
        this.clock = clock;
    }

    public RaidHelperProfileTestResult profile(AuthenticatedUser actor, long profileId) {
        RaidHelperProfileService.requireAdmin(actor);
        RaidHelperConnectionDto connection = profiles.connection(profileId);
        try {
            RaidHelperHttpClient.Response response = client.request(connection, "GET",
                    "/servers/" + connection.serverId() + "/events", null);
            String message = response.successful()
                    ? "Raid-Helper server read access succeeded. Test the exact channel destination to verify event creation."
                    : "Raid-Helper rejected the saved profile or server configuration.";
            return mapper.profileTestResult(response.successful(), response.statusCode(), message);
        } catch (RuntimeException exception) {
            return mapper.profileTestResult(false, null, "Raid-Helper connection failed.");
        }
    }

    public RaidHelperProfileTestResult destination(
            AuthenticatedUser actor, long destinationId, RaidHelperDestinationTestRequest request) {
        RaidHelperProfileService.requireAdmin(actor);
        RaidHelperDestinationConfigDto destination = destinationWithProfile(destinationId);
        if (destination.defaultLeaderId() == null) {
            return mapper.profileTestResult(false, null, "Configure a default leader ID before testing this destination.");
        }
        boolean minimal = request != null && Boolean.TRUE.equals(request.useMinimalPayload());
        RaidHelperTemplateConfigDto template = minimal
                ? null : testTemplate(destination, request == null ? null : request.templateId());
        RaidHelperJsonPayloadDto payload = minimal
                ? minimalPayload(destination.defaultLeaderId())
                : renderer.render(testEvent(destination, template), template, destination.defaultLeaderId());
        String path = "/servers/" + destination.connection().serverId()
                + "/channels/" + destination.channelId() + "/event";
        try {
            RaidHelperHttpClient.Response create = client.request(destination.connection(), "POST", path, payload);
            if (!create.successful()) {
                return mapper.profileTestResult(false, create.statusCode(), client.failureMessage(create));
            }
            String externalId = client.externalId(create.body());
            if (externalId == null) {
                return mapper.profileTestResult(false, create.statusCode(),
                        "The temporary event was created, but Raid-Helper returned no event ID for cleanup.");
            }
            RaidHelperHttpClient.Response delete = client.request(
                    destination.connection(), "DELETE", "/events/" + externalId, null);
            if (!delete.successful()) {
                return mapper.profileTestResult(false, delete.statusCode(),
                        "The temporary event was created, but automatic cleanup failed. " + client.failureMessage(delete));
            }
            String label = minimal ? "minimal default payload" : "selected application template";
            return mapper.profileTestResult(true, create.statusCode(),
                    "Raid-Helper event creation and cleanup succeeded for " + label + ".");
        } catch (RuntimeException exception) {
            return mapper.profileTestResult(false, null, "Raid-Helper destination test failed.");
        }
    }

    private RaidHelperDestinationConfigDto destinationWithProfile(long id) {
        return mapper.destinationConfig(repository.required(
                RaidHelperProbeQueries.DESTINATION_WITH_PROFILE_SELECT_01, Map.of("id", id)));
    }

    private RaidHelperTemplateConfigDto testTemplate(
            RaidHelperDestinationConfigDto destination, Long requestedId) {
        RaidHelperTemplateConfigDto template;
        if (requestedId == null) {
            template = repository.optional(RaidHelperProbeQueries.TEST_TEMPLATE_SELECT_01,
                            Map.of("profileId", destination.profileId()))
                    .map(row -> mapper.templateConfig(row, destination.timezone()))
                    .orElseThrow(() -> new IllegalArgumentException(
                            "No active Raid-Helper template is configured for this profile."));
        } else {
            template = templates.configuration(requestedId, destination.timezone());
            if (template.profileId() != destination.profileId() || !template.active()) {
                throw new IllegalArgumentException(
                        "The selected Raid-Helper template is inactive or belongs to another profile.");
            }
        }
        return template;
    }

    private RaidHelperEventDto testEvent(
            RaidHelperDestinationConfigDto destination, RaidHelperTemplateConfigDto template) {
        LocalDateTime start = LocalDateTime.ofInstant(clock.instant().plusSeconds(900), ZoneOffset.UTC);
        String category = repository.optional(RaidHelperProbeQueries.TEST_EVENT_SELECT_01,
                        Map.of("id", template.id()))
                .map(row -> requiredString(row, "category"))
                .orElseGet(() -> repository.optional(RaidHelperProbeQueries.TEST_EVENT_SELECT_02,
                                Map.of("id", destination.id()))
                        .map(row -> requiredString(row, "category")).orElse("meeting"));
        return new RaidHelperEventDto(0L, "Royal Blackwater Fleet connection test", category,
                "Temporary API verification event. It should be removed automatically.",
                "Raid-Helper API test", start, start.plusHours(1), false,
                destination.squadId(), destination.squadName());
    }

    private RaidHelperJsonPayloadDto minimalPayload(String leaderId) {
        java.time.ZonedDateTime start = clock.instant().plusSeconds(900).atZone(ZoneOffset.UTC);
        return RaidHelperJsonPayloadDto.of(Map.of("leaderId", leaderId, "title", "Royal Blackwater Fleet connection test",
                "description", "Temporary API verification event. It should be removed automatically.",
                "date", java.time.format.DateTimeFormatter.ofPattern("dd.MM.uuuu").format(start),
                "time", java.time.format.DateTimeFormatter.ofPattern("HH:mm").format(start)));
    }

}
