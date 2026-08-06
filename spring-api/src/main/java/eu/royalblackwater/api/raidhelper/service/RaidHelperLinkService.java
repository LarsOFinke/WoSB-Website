package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.dto.RaidHelperDispatchSelection;
import eu.royalblackwater.api.dto.RaidHelperEventLinkRead;
import eu.royalblackwater.api.dto.RaidHelperOptionDestination;
import eu.royalblackwater.api.dto.RaidHelperOptionTemplate;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperLinkQueries;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.squads.service.SquadAccessPolicy;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class RaidHelperLinkService {
    private final RaidHelperRepository repository;
    private final RaidHelperPolicy policy;
    private final FleetAccessPolicy fleets;
    private final SquadAccessPolicy squads;
    private final Clock clock;
    private final RaidHelperDtoMapper mapper;

    public RaidHelperLinkService(RaidHelperRepository repository, RaidHelperPolicy policy,
                                 FleetAccessPolicy fleets, SquadAccessPolicy squads, Clock clock,
                                 RaidHelperDtoMapper mapper) {
        this.repository = repository;
        this.policy = policy;
        this.fleets = fleets;
        this.squads = squads;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public List<RaidHelperOptionDestination> options(
            AuthenticatedUser actor, String rawCategory, Long squadId) {
        String category = policy.category(rawCategory);
        requireScopeManager(actor, squadId);
        String scope = squadId == null ? "fleet" : "squad";
        List<Map<String, Object>> rows = repository.query(RaidHelperLinkQueries.OPTIONS_SELECT_01, SqlParameters.ofNullable("scope", scope, "squadId", squadId, "category", category));
        LinkedHashMap<Long, DestinationBuilder> destinations = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            long destinationId = longValue(row, "destination_id");
            DestinationBuilder destination = destinations.computeIfAbsent(destinationId, ignored -> new DestinationBuilder(
                    destinationId, requiredString(row, "destination_name"), longValue(row, "profile_id"),
                    requiredString(row, "profile_name"), requiredString(row, "scope_type"),
                    nullableLong(row, "squad_id"), booleanValue(row, "destination_default"),
                    string(row, "default_leader_id")));
            destination.templates.add(mapper.optionTemplate(row));
        }
        return destinations.values().stream().map(DestinationBuilder::build).toList();
    }

    @Transactional
    public void configure(long eventId, String category, Long squadId,
                          List<RaidHelperDispatchSelection> selections, AuthenticatedUser actor) {
        List<RaidHelperDispatchSelection> requested = selections == null ? List.of() : selections;
        List<RaidHelperOptionDestination> available = options(actor, category, squadId);
        Map<String, RaidHelperOptionDestination> allowed = new LinkedHashMap<>();
        for (RaidHelperOptionDestination destination : available) {
            for (RaidHelperOptionTemplate template : destination.templates()) {
                allowed.put(key(destination.id(), template.id()), destination);
            }
        }
        Set<Long> requestedDestinations = new LinkedHashSet<>();
        for (RaidHelperDispatchSelection selection : requested) {
            if (selection == null || !requestedDestinations.add(selection.destinationId())) {
                throw new ResponseStatusException(BAD_REQUEST,
                        "Each Raid-Helper destination can be selected at most once.");
            }
            RaidHelperOptionDestination destination = allowed.get(key(selection.destinationId(), selection.templateId()));
            if (destination == null) {
                throw new ResponseStatusException(BAD_REQUEST,
                        "One or more Raid-Helper destinations or templates are not valid for this event.");
            }
            String leader = policy.numericIdentifier(selection.leaderId(), "Leader ID", false);
            if (leader == null && destination.defaultLeaderId() == null) {
                throw new ResponseStatusException(BAD_REQUEST,
                        "Raid-Helper destination “" + destination.name() + "” requires a leader ID.");
            }
        }
        Map<Long, Map<String, Object>> existing = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(
                RaidHelperLinkQueries.CONFIGURE_SELECT_01, Map.of("id", eventId))) {
            existing.put(longValue(row, "destination_id"), row);
        }
        LocalDateTime now = now();
        for (RaidHelperDispatchSelection selection : requested) {
            String leader = policy.numericIdentifier(selection.leaderId(), "Leader ID", false);
            Map<String, Object> row = existing.get(selection.destinationId());
            if (row == null) {
                repository.insertReturningId(RaidHelperLinkQueries.CONFIGURE_INSERT_01, SqlParameters.ofNullable("eventId", eventId, "destinationId", selection.destinationId(),
                        "templateId", selection.templateId(), "leaderId", leader, "now", now));
            } else {
                String operation = string(row, "external_event_id") == null ? "create" : "update";
                repository.update(RaidHelperLinkQueries.CONFIGURE_UPDATE_01, SqlParameters.ofNullable("templateId", selection.templateId(), "leaderId", leader,
                        "operation", operation, "now", now, "id", longValue(row, "id")));
            }
        }
        for (Map.Entry<Long, Map<String, Object>> entry : existing.entrySet()) {
            if (requestedDestinations.contains(entry.getKey())) continue;
            Map<String, Object> row = entry.getValue();
            if (string(row, "external_event_id") == null) {
                repository.update(RaidHelperLinkQueries.CONFIGURE_DELETE_01, Map.of("id", longValue(row, "id")));
            } else {
                repository.update(RaidHelperLinkQueries.CONFIGURE_UPDATE_02, Map.of("now", now, "id", longValue(row, "id")));
            }
        }
    }

    @Transactional(readOnly = true)
    public List<RaidHelperEventLinkRead> links(long eventId) {
        return linksByEventIds(List.of(eventId)).getOrDefault(eventId, List.of());
    }

    @Transactional(readOnly = true)
    public Map<Long, List<RaidHelperEventLinkRead>> linksByEventIds(java.util.Collection<Long> eventIds) {
        if (eventIds == null || eventIds.isEmpty()) return Map.of();
        Map<Long, List<RaidHelperEventLinkRead>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(RaidHelperLinkQueries.LINKS_BY_EVENT_IDS_SELECT_01, Map.of("ids", eventIds))) {
            long eventId = longValue(row, "event_id");
            RaidHelperEventLinkRead value = mapper.eventLink(row);
            result.computeIfAbsent(eventId, ignored -> new ArrayList<>()).add(value);
        }
        result.replaceAll((ignored, values) -> List.copyOf(values));
        return Map.copyOf(result);
    }

    @Transactional
    public void queueRetry(long eventId) {
        int updated = repository.update(RaidHelperLinkQueries.QUEUE_RETRY_UPDATE_01, Map.of("now", now(), "id", eventId));
        if (updated == 0) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "This event has no Raid-Helper destinations to retry.");
        }
    }

    @Transactional
    public void queueCancellation(long eventId) {
        repository.update(RaidHelperLinkQueries.QUEUE_CANCELLATION_UPDATE_01, Map.of("now", now(), "id", eventId));
    }

    public boolean canManage(AuthenticatedUser actor, Long squadId) {
        if (squadId == null) {
            long fleetId = officialFleetId();
            return fleets.canManageFleet(actor, fleetId);
        }
        return repository.optional(RaidHelperLinkQueries.CAN_MANAGE_SELECT_01, Map.of("id", squadId))
                .filter(row -> booleanValue(row, "is_active"))
                .map(row -> squads.canManage(actor, squadId, longValue(row, "fleet_id")))
                .orElse(false);
    }

    public void requireScopeManager(AuthenticatedUser actor, Long squadId) {
        if (!canManage(actor, squadId)) {
            throw new ResponseStatusException(FORBIDDEN, "Event management access required.");
        }
    }

    public long officialFleetId() {
        return repository.optional(RaidHelperLinkQueries.OFFICIAL_FLEET_ID_SELECT_01, Map.of()).map(row -> longValue(row, "id"))
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST, "Official fleet is not configured."));
    }

    private static String key(long destinationId, long templateId) {
        return destinationId + ":" + templateId;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private final class DestinationBuilder {
        private final long id;
        private final String name;
        private final long profileId;
        private final String profileName;
        private final String scopeType;
        private final Long squadId;
        private final boolean isDefault;
        private final String defaultLeaderId;
        private final List<RaidHelperOptionTemplate> templates = new ArrayList<>();

        private DestinationBuilder(long id, String name, long profileId, String profileName,
                                   String scopeType, Long squadId, boolean isDefault, String defaultLeaderId) {
            this.id=id; this.name=name; this.profileId=profileId; this.profileName=profileName;
            this.scopeType=scopeType; this.squadId=squadId; this.isDefault=isDefault;
            this.defaultLeaderId=defaultLeaderId;
        }

        private RaidHelperOptionDestination build() {
            return mapper.optionDestination(id, name, profileId, profileName, scopeType, squadId,
                    isDefault, defaultLeaderId, templates);
        }
    }
}
