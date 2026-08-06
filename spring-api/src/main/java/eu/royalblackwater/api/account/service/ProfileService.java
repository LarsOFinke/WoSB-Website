package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.entity.UserEntity;
import eu.royalblackwater.api.account.entity.UserProfileEntity;
import eu.royalblackwater.api.account.mapper.ProfileDtoMapper;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.UserRepository;
import eu.royalblackwater.api.account.repository.queries.ProfileQueries;
import eu.royalblackwater.api.dto.ProfilePreferenceOptionsRead;
import eu.royalblackwater.api.dto.ProfileUpdate;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.fleet.repository.FleetMembershipRepository;
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
    private final AccountDataRepository repository;
    private final UserViewService views;
    private final Clock clock;
    private final ProfileDtoMapper mapper;

    public ProfileService(UserRepository users, FleetMembershipRepository memberships, AccountDataRepository repository,
                          UserViewService views, Clock clock, ProfileDtoMapper mapper) {
        this.users = users;
        this.memberships = memberships;
        this.repository = repository;
        this.views = views;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional
    public UserRead update(int userId, ProfileUpdate payload) {
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
    public ProfilePreferenceOptionsRead options() {
        return mapper.options(
                repository.query(ProfileQueries.OPTIONS_SELECT_01, Map.of()),
                repository.query(ProfileQueries.OPTIONS_SELECT_02, Map.of()));
    }

    private void validateIds(List<Integer> shipIds, List<Integer> roleIds) {
        if (!shipIds.isEmpty()) {
            long count = repository.count(ProfileQueries.VALIDATE_IDS_SELECT_01, Map.of("ids", shipIds));
            if (count != shipIds.size()) throw invalid("One or more preferred ships are invalid.");
        }
        if (!roleIds.isEmpty()) {
            long count = repository.count(ProfileQueries.VALIDATE_IDS_SELECT_02, Map.of("ids", roleIds));
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
