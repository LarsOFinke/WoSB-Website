package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.account.mapper.AccountDtoMapper;
import eu.royalblackwater.api.account.service.AuthService;
import eu.royalblackwater.api.account.service.RegistrationService;
import eu.royalblackwater.api.account.service.UserViewService;
import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.dto.LoginRequest;
import eu.royalblackwater.api.dto.LoginResponse;
import eu.royalblackwater.api.dto.PasswordChangeRequest;
import eu.royalblackwater.api.dto.PasswordChangeResponse;
import eu.royalblackwater.api.dto.RegisterRequest;
import eu.royalblackwater.api.dto.RegisterResponse;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.securityops.service.SecuritySignalService;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Optional;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNAUTHORIZED;

@RestController
@Validated
public class AuthController extends ApiControllerSupport {

    private final AuthService auth;
    private final UserViewService users;
    private final RegistrationService registration;
    private final SessionProperties session;
    private final HttpServletRequest request;
    private final SecuritySignalService securitySignals;

    public AuthController(AuthService auth, UserViewService users, RegistrationService registration,
                          SessionProperties session, HttpServletRequest request,
                          SecuritySignalService securitySignals) {
        this.auth = auth;
        this.users = users;
        this.registration = registration;
        this.session = session;
        this.request = request;
        this.securitySignals = securitySignals;
    }

    @PostMapping("/api/auth/change-password")
    public ResponseEntity<PasswordChangeResponse> changePassword(
            @Valid @RequestBody PasswordChangeRequest body
    ) {
        return performPasswordChange(body);
    }

    @PostMapping("/api/auth/login")
    public ResponseEntity<LoginResponse> login(
            @Valid @RequestBody LoginRequest body
    ) {
        return performLogin(body);
    }

    @PostMapping("/api/auth/logout")
    public ResponseEntity<Void> logout() {
        auth.logout(rawToken());
        return ResponseEntity.noContent()
                .header(HttpHeaders.SET_COOKIE, expiredCookie().toString())
                .build();
    }

    @GetMapping("/api/auth/me")
    public ResponseEntity<UserRead> me() {
        Optional<Integer> userId = auth.authenticatedUserId(rawToken());
        return ResponseEntity.ok(userId.map(users::read).orElse(null));
    }

    @PostMapping("/api/auth/register")
    public ResponseEntity<RegisterResponse> register(
            @Valid @RequestBody RegisterRequest body
    ) {
        return ResponseEntity.status(202).body(registration.submit(body));
    }

    private ResponseEntity<LoginResponse> performLogin(LoginRequest payload) {
        AuthService.LoginResult result = auth.login(payload.username(), payload.password()).orElseGet(() -> {
            securitySignals.record(request, "login_failure", "invalid_credentials");
            throw new ResponseStatusException(UNAUTHORIZED, "Invalid username or password.");
        });
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie(result.token()).toString())
                .body(AccountDtoMapper.login(users.read(result.userId())));
    }

    private ResponseEntity<PasswordChangeResponse> performPasswordChange(PasswordChangeRequest payload) {
        if (payload.currentPassword().equals(payload.newPassword())) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "New password must be different from the current password.");
        }
        String rotated = auth.changePassword(rawToken(), payload.currentPassword(), payload.newPassword())
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST,
                        "Current password is incorrect."));
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie(rotated).toString())
                .body(AccountDtoMapper.passwordChanged());
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
        return ResponseCookie.from(session.cookieName(), value)
                .httpOnly(true)
                .secure(session.secure())
                .sameSite(session.sameSite())
                .path("/")
                .maxAge(session.ttl())
                .build();
    }

    private ResponseCookie expiredCookie() {
        return ResponseCookie.from(session.cookieName(), "")
                .httpOnly(true)
                .secure(session.secure())
                .sameSite(session.sameSite())
                .path("/")
                .maxAge(0)
                .build();
    }
}
