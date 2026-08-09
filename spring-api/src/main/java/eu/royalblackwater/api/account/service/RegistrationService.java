package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.entity.RegistrationRequestEntity;
import eu.royalblackwater.api.account.mapper.AccountDtoMapper;
import eu.royalblackwater.api.account.mapper.RegistrationRequestMapper;
import eu.royalblackwater.api.account.repository.RegistrationRequestRepository;
import eu.royalblackwater.api.account.repository.UserRepository;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.RegisterRequest;
import eu.royalblackwater.api.dto.RegisterResponse;
import eu.royalblackwater.api.fleet.entity.FleetEntity;
import eu.royalblackwater.api.fleet.repository.FleetRepository;
import eu.royalblackwater.api.security.service.PasswordHasher;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Locale;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.CONFLICT;

@Service
public class RegistrationService {
    private final RegistrationRequestRepository requests;
    private final RegistrationRequestMapper mapper;
    private final UserRepository users;
    private final FleetRepository fleets;
    private final PasswordHasher passwords;
    private final Clock clock;
    private final AuditService audit;

    public RegistrationService(RegistrationRequestRepository requests, RegistrationRequestMapper mapper,
                               UserRepository users, FleetRepository fleets, PasswordHasher passwords, Clock clock,
                               AuditService audit) {
        this.requests = requests;
        this.mapper = mapper;
        this.users = users;
        this.fleets = fleets;
        this.passwords = passwords;
        this.clock = clock;
        this.audit = audit;
    }

    @Transactional
    public RegisterResponse submit(RegisterRequest payload) {
        String username = payload.username().strip().toLowerCase(Locale.ROOT);
        String displayName = payload.displayName().strip();
        boolean wantsFleet = Boolean.TRUE.equals(payload.wantsFleetMembership());
        String note = normalized(payload.fleetApplicationNote());
        if (!wantsFleet && (payload.fleetId() != null || note != null)) {
            throw new ResponseStatusException(CONFLICT, "Fleet application details require wants_fleet_membership=true.");
        }
        if (users.existsByUsername(username) || requests.existsByUsernameAndStatus(username, "pending")) {
            throw new ResponseStatusException(CONFLICT, "Username already exists or is waiting for review.");
        }
        Integer fleetId = null;
        if (wantsFleet) {
            FleetEntity official = fleets.findFirstByActiveTrueOrderBySortOrderAscIdAsc()
                    .orElseThrow(() -> new ResponseStatusException(CONFLICT, "Official fleet not found."));
            if (payload.fleetId() != null && payload.fleetId().intValue() != official.getId()) {
                throw new ResponseStatusException(CONFLICT, "Only the official fleet can be joined.");
            }
            fleetId = official.getId();
        }
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        RegistrationRequestEntity saved = requests.save(new RegistrationRequestEntity(
                username, passwords.hash(payload.password()), displayName, wantsFleet, fleetId, note, now));
        audit.record(null, "registration_request", saved.getId(), "create",
                "A new access request was submitted.", java.util.List.of("status"));
        return AccountDtoMapper.registrationSubmitted(mapper.toPublic(saved));
    }

    private static String normalized(String value) {
        if (value == null) return null;
        String stripped = value.strip();
        return stripped.isEmpty() ? null : stripped;
    }
}
