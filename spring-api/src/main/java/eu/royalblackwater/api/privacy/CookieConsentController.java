package eu.royalblackwater.api.privacy;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import java.util.regex.Pattern;
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

    public CookieConsentController(CookieConsentRepository repository) {
        this.repository = repository;
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
}
