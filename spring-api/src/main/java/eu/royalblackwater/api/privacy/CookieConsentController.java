package eu.royalblackwater.api.privacy;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import eu.royalblackwater.api.account.AuthService;
import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.account.UserEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import java.util.regex.Pattern;
import java.security.SecureRandom;
import java.util.Base64;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Optional;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/privacy")
public class CookieConsentController {
    private static final String COOKIE_NAME = "rbf_cookie_consent";
    private static final Pattern CONSENT_KEY = Pattern.compile("^[A-Za-z0-9_-]{32,64}$");
    private final CookieConsentRepository repository;
    private final AuthService auth;
    private final SessionProperties session;
    private final SecureRandom random = new SecureRandom();

    public CookieConsentController(CookieConsentRepository repository, AuthService auth, SessionProperties session) {
        this.repository = repository;
        this.auth = auth;
        this.session = session;
    }

    @GetMapping("/cookie-policy")
    public ResponseEntity<CookieConsentContracts.Policy> policy() {
        return ResponseEntity.ok(new CookieConsentContracts.Policy(
                CookieConsentContracts.POLICY_VERSION, CookieConsentContracts.CATEGORIES));
    }

    @GetMapping("/cookie-consent")
    @Transactional(readOnly = true)
    public ResponseEntity<CookieConsentContracts.Read> consent(HttpServletRequest request) {
        String key = consentKey(request);
        if (key == null) return ResponseEntity.ok(empty());
        return ResponseEntity.ok(repository.findFirstByConsentKeyOrderByCreatedAtDescIdDesc(key)
                .filter(row -> CookieConsentContracts.POLICY_VERSION.equals(row.getPolicyVersion()))
                .map(row -> new CookieConsentContracts.Read(true, row.getPolicyVersion(), row.isNecessary(),
                        row.isPreferences(), row.isAnalytics(), row.isExternalMedia(), row.getCreatedAt()))
                .orElseGet(this::empty));
    }

    @PostMapping("/cookie-consent")
    @Transactional
    public ResponseEntity<CookieConsentContracts.Read> save(
            @Valid @RequestBody CookieConsentContracts.Choice choice,
            HttpServletRequest request,
            HttpServletResponse response) {
        String key = consentKey(request);
        if (key == null) key = newConsentKey();
        Optional<UserEntity> user = auth.authenticatedUser(sessionToken(request));
        CookieConsentEntity saved = repository.save(new CookieConsentEntity(key, user.map(UserEntity::getId).orElse(null),
                CookieConsentContracts.POLICY_VERSION, choice.preferences(), choice.analytics(),
                choice.externalMedia(), LocalDateTime.now(ZoneOffset.UTC)));
        response.addHeader(HttpHeaders.SET_COOKIE, ResponseCookie.from(COOKIE_NAME, key)
                .httpOnly(true).secure(session.secure()).sameSite(session.sameSite()).path("/")
                .maxAge(java.time.Duration.ofDays(365)).build().toString());
        return ResponseEntity.ok(new CookieConsentContracts.Read(true, saved.getPolicyVersion(), true,
                saved.isPreferences(), saved.isAnalytics(), saved.isExternalMedia(), saved.getCreatedAt()));
    }

    private CookieConsentContracts.Read empty() {
        return new CookieConsentContracts.Read(false, CookieConsentContracts.POLICY_VERSION, true,
                false, false, false, null);
    }

    private static String consentKey(HttpServletRequest request) {
        if (request.getCookies() == null) return null;
        for (Cookie cookie : request.getCookies()) {
            if (COOKIE_NAME.equals(cookie.getName()) && CONSENT_KEY.matcher(cookie.getValue()).matches()) {
                return cookie.getValue();
            }
        }
        return null;
    }

    private String sessionToken(HttpServletRequest request) {
        if (request.getCookies() == null) return null;
        for (Cookie cookie : request.getCookies()) {
            if (session.cookieName().equals(cookie.getName())) return cookie.getValue();
        }
        return null;
    }

    private String newConsentKey() {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
}
