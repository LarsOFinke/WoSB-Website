package eu.royalblackwater.api.account.mapper;

import eu.royalblackwater.api.dto.LoginResponse;
import eu.royalblackwater.api.dto.ModeratorCreateResponse;
import eu.royalblackwater.api.dto.PasswordChangeResponse;
import eu.royalblackwater.api.dto.RegisterResponse;
import eu.royalblackwater.api.dto.RegistrationRequestPublic;
import eu.royalblackwater.api.dto.RegistrationRequestRead;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class AccountDtoMapper {
    private AccountDtoMapper() { }

    public static UserRead user(Map<String, Object> row, List<Long> ships, List<Long> roles) {
        String role = RowValues.requiredString(row, "role");
        boolean bootstrap = RowValues.booleanValue(row, "is_bootstrap_admin");
        String displayName = RowValues.string(row, "display_name");
        if (displayName == null || displayName.isBlank()) displayName = RowValues.requiredString(row, "username");
        String fleetName = RowValues.string(row, "fleet_name");
        if (fleetName == null) fleetName = RowValues.string(row, "external_fleet_name");
        return new UserRead(RowValues.string(row, "availability"), bootstrap && "admin".equals(role),
                RowValues.dateTime(row, "created_at"), RowValues.string(row, "discord_handle"), displayName,
                RowValues.nullableLong(row, "fleet_id"), RowValues.nullableLong(row, "membership_id"),
                RowValues.string(row, "membership_role"), RowValues.string(row, "membership_status"), fleetName,
                RowValues.longValue(row, "id"), RowValues.booleanValue(row, "is_active"), bootstrap,
                RowValues.string(row, "note"), RowValues.string(row, "preferred_focus"), roles, ships, role,
                RowValues.string(row, "timezone"), RowValues.requiredString(row, "username"));
    }

    public static UserReferenceRead userReference(Map<String, Object> row) {
        long id = RowValues.longValue(row, "id");
        return new UserReferenceRead(RowValues.requiredString(row, "display_name"), id);
    }

    public static RegistrationRequestRead registrationRequest(
            Map<String, Object> row, UserRead createdUser, UserRead reviewedBy) {
        return new RegistrationRequestRead(RowValues.dateTime(row, "created_at"), createdUser,
                RowValues.string(row, "decision_note"), RowValues.requiredString(row, "display_name"),
                RowValues.string(row, "fleet_application_note"), RowValues.nullableLong(row, "fleet_id"),
                RowValues.longValue(row, "id"), RowValues.nullableDateTime(row, "reviewed_at"), reviewedBy,
                RowValues.requiredString(row, "status"), RowValues.dateTime(row, "updated_at"),
                RowValues.requiredString(row, "username"),
                RowValues.booleanValue(row, "wants_fleet_membership"));
    }
    public static LoginResponse login(UserRead user) {
        return new LoginResponse(user);
    }

    public static PasswordChangeResponse passwordChanged() {
        return new PasswordChangeResponse(true);
    }

    public static ModeratorCreateResponse moderatorCreated(UserRead user) {
        return new ModeratorCreateResponse(user);
    }

    public static RegisterResponse registrationSubmitted(RegistrationRequestPublic request) {
        return new RegisterResponse("Registration request submitted for admin review.", request);
    }

}
