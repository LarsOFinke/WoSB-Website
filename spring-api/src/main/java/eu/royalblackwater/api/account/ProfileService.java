package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.ProfileUpdate;
import eu.royalblackwater.api.fleet.FleetMembershipRepository;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_ENTITY;

@Service
public class ProfileService {
    private static final Set<String> FOCUS_VALUES = Set.of(
            "pve_farming", "pve_imp_hunting", "pve_general", "pvp_open_world",
            "pvp_arena", "pvp_general", "trading", "other");

    private final UserRepository users;
    private final FleetMembershipRepository memberships;
    private final JdbcQueryService jdbc;
    private final UserViewService views;
    private final Clock clock;

    public ProfileService(UserRepository users, FleetMembershipRepository memberships, JdbcQueryService jdbc,
                          UserViewService views, Clock clock) {
        this.users = users;
        this.memberships = memberships;
        this.jdbc = jdbc;
        this.views = views;
        this.clock = clock;
    }

    @Transactional
    public AuthContracts.UserRead update(int userId, ProfileUpdate payload) {
        UserEntity user = users.findById(userId)
                .orElseThrow(() -> new IllegalStateException("Authenticated user no longer exists."));
        List<Integer> shipIds = normalizedIds(payload.preferredShipIds(), 20);
        List<Integer> roleIds = normalizedIds(payload.preferredRoleIds(), 10);
        validateIds(shipIds, roleIds);
        String focus = normalized(payload.preferredFocus());
        if (focus != null && !FOCUS_VALUES.contains(focus)) {
            throw invalid("Invalid preferred focus.");
        }
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        UserProfileEntity profile = user.ensureProfile(now);
        String externalFleet = memberships.existsByUser_Id(userId) ? profile.getExternalFleetName() : normalized(payload.fleetName());
        profile.update(payload.displayName().strip(), externalFleet, focus, normalized(payload.availability()),
                normalized(payload.timezone()), normalized(payload.discordHandle()), normalized(payload.note()), now);
        profile.replaceShipPreferences(shipIds);
        profile.replaceRolePreferences(roleIds);
        user.touch(now);
        users.save(user);
        return views.read(userId);
    }

    @Transactional(readOnly = true)
    public Map<String, Object> options() {
        return Map.of(
                "ships", jdbc.query("""
                        select id, name, rate
                          from ships
                         where is_active = true
                         order by rate, name, id
                        """, Map.of()),
                "roles", jdbc.query("""
                        select id, code, label
                          from fleet_roles
                         order by rank desc, label, id
                        """, Map.of()));
    }

    private void validateIds(List<Integer> shipIds, List<Integer> roleIds) {
        if (!shipIds.isEmpty()) {
            long count = jdbc.count("select count(*) from ships where is_active = true and id in (:ids)", Map.of("ids", shipIds));
            if (count != shipIds.size()) throw invalid("One or more preferred ships are invalid.");
        }
        if (!roleIds.isEmpty()) {
            long count = jdbc.count("select count(*) from fleet_roles where id in (:ids)", Map.of("ids", roleIds));
            if (count != roleIds.size()) throw invalid("One or more preferred roles are invalid.");
        }
    }

    private static List<Integer> normalizedIds(List<Long> values, int maximum) {
        if (values == null || values.isEmpty()) return List.of();
        LinkedHashSet<Integer> ids = new LinkedHashSet<>();
        for (Long value : values) {
            if (value == null || value < 1 || value > Integer.MAX_VALUE) throw invalid("Invalid preference identifier.");
            ids.add(value.intValue());
        }
        if (ids.size() > maximum) throw invalid("Too many preferences.");
        return List.copyOf(ids);
    }

    private static String normalized(String value) {
        if (value == null) return null;
        String stripped = value.strip();
        return stripped.isEmpty() ? null : stripped;
    }

    private static ResponseStatusException invalid(String detail) {
        return new ResponseStatusException(UNPROCESSABLE_ENTITY, detail);
    }
}
