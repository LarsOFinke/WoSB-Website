package eu.royalblackwater.api.account;

import eu.royalblackwater.api.account.entity.UserEntity;
import eu.royalblackwater.api.account.mapper.ProfileDtoMapper;
import eu.royalblackwater.api.account.mapper.RegistrationRequestMapper;
import eu.royalblackwater.api.account.mapper.UserMapper;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.RegistrationRequestRepository;
import eu.royalblackwater.api.account.repository.UserRepository;
import eu.royalblackwater.api.account.service.ProfileService;
import eu.royalblackwater.api.account.service.RegistrationService;
import eu.royalblackwater.api.account.service.UserAdministrationService;
import eu.royalblackwater.api.account.service.UserDirectoryService;
import eu.royalblackwater.api.account.service.UserViewService;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.ModeratorCreate;
import eu.royalblackwater.api.dto.ProfileUpdate;
import eu.royalblackwater.api.dto.RegisterRequest;
import eu.royalblackwater.api.dto.UserAdministrationUpdate;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.fleet.repository.FleetMembershipRepository;
import eu.royalblackwater.api.fleet.repository.FleetRepository;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.PasswordHasher;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AccountServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);

    @Test
    void profileServiceRejectsInvalidPreferenceIdsBeforePersistingChanges() {
        UserRepository users = mock(UserRepository.class);
        UserEntity user = mock(UserEntity.class);
        when(users.findById(7)).thenReturn(Optional.of(user));
        ProfileService service = new ProfileService(users, mock(FleetMembershipRepository.class),
                mock(AccountDataRepository.class), mock(UserViewService.class), CLOCK, mock(ProfileDtoMapper.class));
        ProfileUpdate payload = new ProfileUpdate(null, null, "Captain", null, null, null,
                List.of(), List.of(0L), null);

        assertThatThrownBy(() -> service.update(7, payload))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(422))
                .hasMessageContaining("Invalid preference identifier");
        verify(users, never()).save(user);
    }

    @Test
    void registrationServiceRejectsFleetDetailsWhenFleetMembershipWasNotRequested() {
        RegistrationRequestRepository requests = mock(RegistrationRequestRepository.class);
        UserRepository users = mock(UserRepository.class);
        RegistrationService service = new RegistrationService(requests, mock(RegistrationRequestMapper.class), users,
                mock(FleetRepository.class), mock(PasswordHasher.class), CLOCK, mock(AuditService.class));
        RegisterRequest payload = new RegisterRequest("Captain", "Please accept", 3L,
                "correct-horse-battery", " Captain ", false);

        assertThatThrownBy(() -> service.submit(payload))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(409))
                .hasMessageContaining("wants_fleet_membership=true");
        verify(users, never()).existsByUsername(anyString());
        verify(requests, never()).save(org.mockito.ArgumentMatchers.any());
    }

    @Test
    void registrationServiceNormalizesUsernamesBeforeDuplicateDetection() {
        RegistrationRequestRepository requests = mock(RegistrationRequestRepository.class);
        UserRepository users = mock(UserRepository.class);
        when(users.existsByUsername("captain")).thenReturn(true);
        RegistrationService service = new RegistrationService(requests, mock(RegistrationRequestMapper.class), users,
                mock(FleetRepository.class), mock(PasswordHasher.class), CLOCK, mock(AuditService.class));
        RegisterRequest payload = new RegisterRequest("Captain", null, null,
                "correct-horse-battery", "  CAPTAIN  ", false);

        assertThatThrownBy(() -> service.submit(payload))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("already exists");
        verify(users).existsByUsername("captain");
    }

    @Test
    void userAdministrationServiceRejectsSelfDeactivationAndNonAdminModeratorCreation() {
        AccountDataRepository repository = mock(AccountDataRepository.class);
        UserDirectoryService directory = mock(UserDirectoryService.class);
        UserAdministrationService service = new UserAdministrationService(repository, directory,
                mock(PasswordHasher.class), mock(AuditService.class), CLOCK);
        AuthenticatedUser actor = new AuthenticatedUser(7, "captain", "admin", true, true, true);
        Map<String, Object> self = Map.of(
                "id", 7L, "role", "admin", "is_active", true, "is_bootstrap_admin", true,
                "role_rank", 100, "username", "captain");
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(self), Optional.of(self));

        assertThatThrownBy(() -> service.update(7, new UserAdministrationUpdate(false, null), actor))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("deactivate your own account");

        AuthenticatedUser moderator = new AuthenticatedUser(9, "mod", "moderator", true, false, false);
        assertThatThrownBy(() -> service.createModerator(
                new ModeratorCreate("Moderator", "strong-password-123", "newmod"), moderator))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Only administrators");
    }

    @Test
    void userViewServiceMapsAUserWithoutProfilePreferencesAndRejectsMissingUsers() {
        UserRepository users = mock(UserRepository.class);
        FleetMembershipRepository memberships = mock(FleetMembershipRepository.class);
        UserMapper mapper = mock(UserMapper.class);
        UserEntity user = mock(UserEntity.class);
        UserRead expected = mock(UserRead.class);
        when(users.findById(4)).thenReturn(Optional.of(user));
        when(memberships.findProfileMemberships(4)).thenReturn(List.of());
        when(mapper.toRead(user, null, List.of(), List.of())).thenReturn(expected);
        UserViewService service = new UserViewService(users, memberships, mapper);

        assertThat(service.read(4)).isSameAs(expected);
        verify(mapper).toRead(user, null, List.of(), List.of());

        when(users.findById(99)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.read(99))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("User not found");
    }
}
