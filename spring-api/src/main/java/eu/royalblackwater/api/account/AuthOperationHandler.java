package eu.royalblackwater.api.account;

import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.contract.LoginRequest;
import eu.royalblackwater.api.contract.PasswordChangeRequest;
import eu.royalblackwater.api.contract.RegisterRequest;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.securityops.SecuritySignalService;
import eu.royalblackwater.api.transport.ApiOperationHandler;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.node.NullNode;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNAUTHORIZED;

@Component
public class AuthOperationHandler implements ApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "change_password_api_auth_change_password_post",
            "login_api_auth_login_post",
            "logout_api_auth_logout_post",
            "me_api_auth_me_get",
            "register_api_auth_register_post");

    private final AuthService auth;
    private final UserViewService users;
    private final RegistrationService registration;
    private final SessionProperties session;
    private final HttpServletRequest request;
    private final SecuritySignalService securitySignals;

    public AuthOperationHandler(AuthService auth, UserViewService users, RegistrationService registration,
                                SessionProperties session, HttpServletRequest request, SecuritySignalService securitySignals) {
        this.auth = auth;
        this.users = users;
        this.registration = registration;
        this.session = session;
        this.request = request;
        this.securitySignals = securitySignals;
    }

    @Override
    public Set<String> operations() {
        return OPERATIONS;
    }

    @Override
    public ResponseEntity<?> handle(String operationId, Map<String, Object> parameters, Object body,
                                    MultipartFile upload, int successStatus) {
        return switch (operationId) {
            case "login_api_auth_login_post" -> login((LoginRequest) body);
            case "logout_api_auth_logout_post" -> logout();
            case "me_api_auth_me_get" -> me();
            case "change_password_api_auth_change_password_post" -> changePassword((PasswordChangeRequest) body);
            case "register_api_auth_register_post" -> ResponseEntity.status(successStatus)
                    .body(registration.submit((RegisterRequest) body));
            default -> throw new IllegalStateException("Unsupported auth operation: " + operationId);
        };
    }

    private ResponseEntity<?> login(LoginRequest payload) {
        AuthService.LoginResult result = auth.login(payload.username(), payload.password()).orElseGet(() -> {
            securitySignals.record(request, "login_failure", "invalid_credentials");
            throw new ResponseStatusException(UNAUTHORIZED, "Invalid username or password.");
        });
        return ResponseEntity.ok().header(HttpHeaders.SET_COOKIE, cookie(result.token()).toString())
                .body(Map.of("user", users.read(result.user().getId())));
    }

    private ResponseEntity<?> logout() {
        auth.logout(rawToken());
        return ResponseEntity.noContent().header(HttpHeaders.SET_COOKIE, expiredCookie().toString()).build();
    }

    private ResponseEntity<?> me() {
        Optional<UserEntity> user = auth.authenticatedUser(rawToken());
        Object result = user.<Object>map(value -> users.read(value.getId())).orElseGet(NullNode::getInstance);
        return ResponseEntity.ok(result);
    }

    private ResponseEntity<?> changePassword(PasswordChangeRequest payload) {
        if (payload.currentPassword().equals(payload.newPassword())) {
            throw new ResponseStatusException(BAD_REQUEST, "New password must be different from the current password.");
        }
        String rotated = auth.changePassword(rawToken(), payload.currentPassword(), payload.newPassword())
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST, "Current password is incorrect."));
        return ResponseEntity.ok().header(HttpHeaders.SET_COOKIE, cookie(rotated).toString())
                .body(Map.of("changed", true));
    }

    private String rawToken() {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) return null;
        for (Cookie cookie : cookies) {
            if (session.cookieName().equals(cookie.getName())) return cookie.getValue();
        }
        return null;
    }

    private ResponseCookie cookie(String value) {
        return ResponseCookie.from(session.cookieName(), value).httpOnly(true).secure(session.secure())
                .sameSite(session.sameSite()).path("/").maxAge(session.ttl()).build();
    }

    private ResponseCookie expiredCookie() {
        return ResponseCookie.from(session.cookieName(), "").httpOnly(true).secure(session.secure())
                .sameSite(session.sameSite()).path("/").maxAge(0).build();
    }
}
