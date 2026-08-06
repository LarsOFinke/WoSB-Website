package eu.royalblackwater.api.fleet.service;

import eu.royalblackwater.api.dto.FleetDetail;
import eu.royalblackwater.api.dto.FleetMemberUserRead;
import eu.royalblackwater.api.dto.FleetMembershipFleetRead;
import eu.royalblackwater.api.dto.FleetMembershipRead;
import eu.royalblackwater.api.dto.FleetMembershipSelfRead;
import eu.royalblackwater.api.dto.FleetPublicLeaderRead;
import eu.royalblackwater.api.dto.FleetPublicRead;
import eu.royalblackwater.api.dto.FleetRead;
import eu.royalblackwater.api.fleet.mapper.FleetDtoMapper;
import eu.royalblackwater.api.fleet.repository.FleetDataRepository;
import eu.royalblackwater.api.fleet.repository.queries.FleetViewQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class FleetViewService {
    private final FleetDataRepository repository;
    private final FleetAccessPolicy policy;
    private final FleetDtoMapper mapper;

    public FleetViewService(FleetDataRepository repository, FleetAccessPolicy policy, FleetDtoMapper mapper) {
        this.repository = repository;
        this.policy = policy;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public FleetPublicRead officialPublic() {
        Map<String, Object> row = official(false);
        List<FleetPublicLeaderRead> leaders = membershipRows(RowValues.longValue(row, "id"), true).stream()
                .map(mapper::publicLeader).toList();
        return mapper.publicFleet(row, leaders);
    }

    @Transactional(readOnly = true)
    public List<FleetRead> list(boolean includeInactive) {
        Map<String, Object> row = official(includeInactive);
        return List.of(fleetRead(row));
    }

    @Transactional(readOnly = true)
    public List<FleetRead> manageable(AuthenticatedUser actor) {
        Map<String, Object> row = official(actor.staff());
        long fleetId = RowValues.longValue(row, "id");
        if (!policy.canManageFleet(actor, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Fleet leadership access required.");
        }
        return List.of(fleetRead(row));
    }

    @Transactional(readOnly = true)
    public List<FleetMembershipSelfRead> membershipsFor(int userId) {
        return repository.query(FleetViewQueries.MEMBERSHIP_SELECT + FleetViewQueries.MEMBERSHIPS_FOR_WHERE_01, Map.of("userId", userId)).stream().map(this::selfMembership).toList();
    }

    @Transactional(readOnly = true)
    public FleetDetail detail(long fleetId, boolean management, AuthenticatedUser actor) {
        Map<String, Object> row = fleet(fleetId, management);
        if (management) policy.requireFleetManager(actor, fleetId);
        List<FleetMembershipRead> memberships = management
                ? membershipRows(fleetId, false).stream().map(item -> membership(item, actor)).toList()
                : List.of();
        List<FleetMembershipRead> leaders = membershipRows(fleetId, true).stream()
                .map(item -> membership(item, null)).toList();
        return mapper.detail(row, leaders, memberships);
    }

    @Transactional(readOnly = true)
    public FleetRead read(long fleetId, boolean includeInactive) {
        return fleetRead(fleet(fleetId, includeInactive));
    }

    @Transactional(readOnly = true)
    public FleetMembershipRead membership(long membershipId, AuthenticatedUser actor) {
        Map<String, Object> row = repository.optional(FleetViewQueries.MEMBERSHIP_SELECT + FleetViewQueries.MEMBERSHIP_WHERE_01, Map.of("id", membershipId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Membership not found."));
        return membership(row, actor);
    }

    private Map<String, Object> official(boolean includeInactive) {
        String active = includeInactive ? "" : FleetViewQueries.OFFICIAL_WHERE_01;
        return repository.optional(FleetViewQueries.FLEET_SELECT + active + FleetViewQueries.OFFICIAL_ORDER_BY_01,
                Map.of()).orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet not found."));
    }

    private Map<String, Object> fleet(long fleetId, boolean includeInactive) {
        String active = includeInactive ? "" : FleetViewQueries.FLEET_AND_01;
        return repository.optional(FleetViewQueries.FLEET_SELECT + FleetViewQueries.FLEET_WHERE_01 + active, Map.of("id", fleetId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet not found."));
    }

    private List<Map<String, Object>> membershipRows(long fleetId, boolean leadersOnly) {
        String filter = leadersOnly ? FleetViewQueries.MEMBERSHIP_ROWS_AND_01 : "";
        return repository.query(FleetViewQueries.MEMBERSHIP_SELECT + FleetViewQueries.MEMBERSHIP_ROWS_WHERE_01 + filter + FleetViewQueries.MEMBERSHIP_ROWS_ORDER_BY_01, Map.of("fleetId", fleetId));
    }

    private FleetRead fleetRead(Map<String, Object> row) {
        long id = RowValues.longValue(row, "id");
        List<FleetMembershipRead> leaders = membershipRows(id, true).stream()
                .map(item -> membership(item, null)).toList();
        return mapper.fleet(row, leaders);
    }

    private FleetMembershipRead membership(Map<String, Object> row, AuthenticatedUser actor) {
        return mapper.membership(row, actor == null ? null : policy.permissions(actor,
                RowValues.longValue(row, "fleet_id"), mapper.membershipTarget(row)));
    }

    private FleetMembershipSelfRead selfMembership(Map<String, Object> row) {
        FleetMembershipRead member = membership(row, null);
        return mapper.selfMembership(row, member);
    }

}
