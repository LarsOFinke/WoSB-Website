package eu.royalblackwater.api.account;

import eu.royalblackwater.api.config.SessionProperties;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.node.NullNode;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Optional;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNAUTHORIZED;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService auth;
    private final UserMapper mapper;
    private final SessionProperties session;

    public AuthController(AuthService auth, UserMapper mapper, SessionProperties session) {
        this.auth = auth;
        this.mapper = mapper;
        this.session = session;
    }

    @PostMapping("/login")
    public ResponseEntity<AuthContracts.LoginResponse> login(@Valid @RequestBody AuthContracts.LoginRequest request) {
        AuthService.LoginResult result = auth.login(request.username(), request.password())
                .orElseThrow(() -> new ResponseStatusException(UNAUTHORIZED, "Invalid username or password."));
        return ResponseEntity.ok().header(HttpHeaders.SET_COOKIE, cookie(result.token()).toString())
                .body(new AuthContracts.LoginResponse(mapper.toRead(result.user())));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest request) {
        auth.logout(rawToken(request));
        return ResponseEntity.noContent().header(HttpHeaders.SET_COOKIE, expiredCookie().toString()).build();
    }

    @GetMapping("/me")
    public ResponseEntity<JsonNode> me(HttpServletRequest request, ObjectMapper json) {
        Optional<UserEntity> user = auth.authenticatedUser(rawToken(request));
        JsonNode body = user.<JsonNode>map(value -> json.valueToTree(mapper.toRead(value)))
                .orElseGet(NullNode::getInstance);
        return ResponseEntity.ok(body);
    }

    @PostMapping("/change-password")
    public ResponseEntity<AuthContracts.PasswordChangeResponse> changePassword(
            HttpServletRequest servletRequest,
            @Valid @RequestBody AuthContracts.PasswordChangeRequest request) {
        String rotated = auth.changePassword(rawToken(servletRequest), request.currentPassword(), request.newPassword())
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST, "Current password is incorrect."));
        return ResponseEntity.ok().header(HttpHeaders.SET_COOKIE, cookie(rotated).toString())
                .body(new AuthContracts.PasswordChangeResponse(true));
    }

    private String rawToken(HttpServletRequest request) {
        if (request.getCookies() == null) return null;
        for (var cookie : request.getCookies()) {
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
