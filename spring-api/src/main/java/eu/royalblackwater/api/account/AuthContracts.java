package eu.royalblackwater.api.account;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public final class AuthContracts {
    private AuthContracts() { }

    public record LoginRequest(@NotBlank @Size(max = 80) String username,
                               @NotBlank @Size(max = 200) String password) { }
    public record LoginResponse(UserRead user) { }
    public record PasswordChangeRequest(@NotBlank @Size(max = 200) String currentPassword,
                                        @Size(min = 12, max = 200) String newPassword) {
        @AssertTrue(message = "New password must be different from the current password.")
        public boolean isDifferent() { return !currentPassword.equals(newPassword); }
    }
    public record PasswordChangeResponse(boolean changed) { }
    public record UserRead(Long id, String username, String displayName, String role,
                           boolean isActive, boolean isBootstrapAdmin, boolean canGrantAdmin,
                           String fleetName, Long fleetId, Long fleetMembershipId,
                           String fleetMembershipStatus, String fleetMembershipRole,
                           String preferredFocus, String availability, String timezone,
                           String discordHandle, List<Long> preferredShipIds,
                           List<Long> preferredRoleIds, String note, LocalDateTime createdAt) { }
}
