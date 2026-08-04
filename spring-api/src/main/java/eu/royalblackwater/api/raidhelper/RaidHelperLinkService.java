package eu.royalblackwater.api.raidhelper;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;

import eu.royalblackwater.api.contract.RaidHelperDispatchSelection;
import eu.royalblackwater.api.contract.RaidHelperEventLinkRead;
import eu.royalblackwater.api.contract.RaidHelperOptionDestination;
import eu.royalblackwater.api.contract.RaidHelperOptionTemplate;
import eu.royalblackwater.api.fleet.FleetAccessPolicy;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.squads.SquadAccessPolicy;
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

@Service
public class RaidHelperLinkService {
    private final JdbcQueryService jdbc;
    private final RaidHelperPolicy policy;
    private final FleetAccessPolicy fleets;
    private final SquadAccessPolicy squads;
    private final Clock clock;

    public RaidHelperLinkService(JdbcQueryService jdbc, RaidHelperPolicy policy,
                                 FleetAccessPolicy fleets, SquadAccessPolicy squads, Clock clock) {
        this.jdbc = jdbc;
        this.policy = policy;
        this.fleets = fleets;
        this.squads = squads;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<RaidHelperOptionDestination> options(
            AuthenticatedUser actor, String rawCategory, Long squadId) {
        String category = policy.category(rawCategory);
        requireScopeManager(actor, squadId);
        String scope = squadId == null ? "fleet" : "squad";
        List<Map<String, Object>> rows = jdbc.query("""
                select d.id destination_id,d.name destination_name,d.profile_id,d.scope_type,d.squad_id,
                       d.is_default destination_default,p.name profile_name,p.default_leader_id,
                       t.id template_id,t.name template_name,t.raid_template_id,t.is_default template_default
                from raid_helper_destinations d
                join raid_helper_profiles p on p.id=d.profile_id and p.is_active=true
                join raid_helper_templates t on t.profile_id=p.id and t.is_active=true
                where d.is_active=true and d.scope_type=:scope
                  and (cast(:squadId as integer) is null and d.squad_id is null or d.squad_id=:squadId)
                  and t.scope_type in ('both',:scope)
                  and (not exists(select 1 from raid_helper_destination_categories dc where dc.destination_id=d.id)
                       or exists(select 1 from raid_helper_destination_categories dc where dc.destination_id=d.id and dc.category=:category))
                  and (not exists(select 1 from raid_helper_template_categories tc where tc.template_id=t.id)
                       or exists(select 1 from raid_helper_template_categories tc where tc.template_id=t.id and tc.category=:category))
                order by d.is_default desc,lower(d.name),d.id,t.is_default desc,lower(t.name),t.id
                """, SqlParameters.ofNullable("scope", scope, "squadId", squadId, "category", category));
        LinkedHashMap<Long, DestinationBuilder> destinations = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            long destinationId = longValue(row, "destination_id");
            DestinationBuilder destination = destinations.computeIfAbsent(destinationId, ignored -> new DestinationBuilder(
                    destinationId, requiredString(row, "destination_name"), longValue(row, "profile_id"),
                    requiredString(row, "profile_name"), requiredString(row, "scope_type"),
                    nullableLong(row, "squad_id"), booleanValue(row, "destination_default"),
                    string(row, "default_leader_id")));
            destination.templates.add(new RaidHelperOptionTemplate(longValue(row, "template_id"),
                    booleanValue(row, "template_default"), requiredString(row, "template_name"),
                    longValue(row, "profile_id"), requiredString(row, "profile_name"),
                    requiredString(row, "raid_template_id")));
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
        for (Map<String, Object> row : jdbc.query(
                "select * from raid_helper_event_links where event_id=:id order by id", Map.of("id", eventId))) {
            existing.put(longValue(row, "destination_id"), row);
        }
        LocalDateTime now = now();
        for (RaidHelperDispatchSelection selection : requested) {
            String leader = policy.numericIdentifier(selection.leaderId(), "Leader ID", false);
            Map<String, Object> row = existing.get(selection.destinationId());
            if (row == null) {
                jdbc.insertReturningId("""
                        insert into raid_helper_event_links
                          (event_id,destination_id,template_id,leader_id_override,status,last_operation,attempts,
                           created_at,updated_at)
                        values (:eventId,:destinationId,:templateId,:leaderId,'queued','create',0,:now,:now)
                        returning id
                        """, SqlParameters.ofNullable("eventId", eventId, "destinationId", selection.destinationId(),
                        "templateId", selection.templateId(), "leaderId", leader, "now", now));
            } else {
                String operation = string(row, "external_event_id") == null ? "create" : "update";
                jdbc.update("""
                        update raid_helper_event_links set template_id=:templateId,leader_id_override=:leaderId,
                          status='queued',last_operation=:operation,error_message=null,updated_at=:now
                        where id=:id
                        """, SqlParameters.ofNullable("templateId", selection.templateId(), "leaderId", leader,
                        "operation", operation, "now", now, "id", longValue(row, "id")));
            }
        }
        for (Map.Entry<Long, Map<String, Object>> entry : existing.entrySet()) {
            if (requestedDestinations.contains(entry.getKey())) continue;
            Map<String, Object> row = entry.getValue();
            if (string(row, "external_event_id") == null) {
                jdbc.update("delete from raid_helper_event_links where id=:id", Map.of("id", longValue(row, "id")));
            } else {
                jdbc.update("""
                        update raid_helper_event_links set status='queued',last_operation='delete',
                          error_message=null,updated_at=:now where id=:id
                        """, Map.of("now", now, "id", longValue(row, "id")));
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
        for (Map<String, Object> row : jdbc.query("""
                select l.*,d.name destination_name,p.name profile_name,t.name template_name
                from raid_helper_event_links l join raid_helper_destinations d on d.id=l.destination_id
                join raid_helper_profiles p on p.id=d.profile_id
                join raid_helper_templates t on t.id=l.template_id
                where l.event_id in (:ids) order by l.event_id,l.id
                """, Map.of("ids", eventIds))) {
            long eventId = longValue(row, "event_id");
            RaidHelperEventLinkRead value = new RaidHelperEventLinkRead(
                    longValue(row, "destination_id"), requiredString(row, "destination_name"),
                    string(row, "error_message"), string(row, "external_event_id"), longValue(row, "id"),
                    requiredString(row, "last_operation"), requiredString(row, "profile_name"),
                    requiredString(row, "status"), nullableDateTime(row, "synced_at"),
                    longValue(row, "template_id"), requiredString(row, "template_name"));
            result.computeIfAbsent(eventId, ignored -> new ArrayList<>()).add(value);
        }
        result.replaceAll((ignored, values) -> List.copyOf(values));
        return Map.copyOf(result);
    }

    @Transactional
    public void queueRetry(long eventId) {
        int updated = jdbc.update("""
                update raid_helper_event_links set status='queued',
                  last_operation=case when external_event_id is null then 'create' else 'update' end,
                  error_message=null,updated_at=:now where event_id=:id
                """, Map.of("now", now(), "id", eventId));
        if (updated == 0) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "This event has no Raid-Helper destinations to retry.");
        }
    }

    @Transactional
    public void queueCancellation(long eventId) {
        jdbc.update("""
                update raid_helper_event_links set status='queued',last_operation='delete',
                  error_message=null,updated_at=:now where event_id=:id
                """, Map.of("now", now(), "id", eventId));
    }

    public boolean canManage(AuthenticatedUser actor, Long squadId) {
        if (squadId == null) {
            long fleetId = officialFleetId();
            return fleets.canManageFleet(actor, fleetId);
        }
        return jdbc.optional("select fleet_id,is_active from squads where id=:id", Map.of("id", squadId))
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
        return jdbc.optional("""
                select id from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end,sort_order,id limit 1
                """, Map.of()).map(row -> longValue(row, "id"))
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST, "Official fleet is not configured."));
    }

    private static String key(long destinationId, long templateId) {
        return destinationId + ":" + templateId;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static final class DestinationBuilder {
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
            return new RaidHelperOptionDestination(defaultLeaderId, id, isDefault, name, profileId,
                    profileName, scopeType, squadId, List.copyOf(templates));
        }
    }
}
