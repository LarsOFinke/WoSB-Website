package eu.royalblackwater.api.security.dto;

import java.security.Principal;
import java.util.Locale;

public record AuthenticatedUser(
        int id,
        String username,
        String role,
        boolean staff,
        boolean canManageSystem,
        boolean bootstrapAdmin) implements Principal {

    @Override
    public String getName() {
        return username;
    }

    public boolean isAdmin() {
        return "admin".equals(role);
    }

    public boolean canGrantAdmin() {
        return isAdmin() && bootstrapAdmin;
    }

    public String authority() {
        return "ROLE_" + role.toUpperCase(Locale.ROOT);
    }
}
