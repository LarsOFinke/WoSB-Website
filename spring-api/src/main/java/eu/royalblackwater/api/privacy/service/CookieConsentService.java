package eu.royalblackwater.api.privacy.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.dto.CookieConsentChoice;
import eu.royalblackwater.api.dto.CookieConsentPolicy;
import eu.royalblackwater.api.dto.CookieConsentRead;
import eu.royalblackwater.api.privacy.entity.CookieConsentEntity;
import eu.royalblackwater.api.privacy.mapper.PrivacyDtoMapper;
import eu.royalblackwater.api.privacy.repository.CookieConsentRepository;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.shared.web.ApiRequestAttributes;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import java.security.SecureRandom;
import java.time.Clock;
import java.util.Base64;
import java.util.List;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;

@Service
public class CookieConsentService {
    private static final Logger LOG = LoggerFactory.getLogger(CookieConsentService.class);
    public static final String COOKIE_NAME = "rbf_cookie_consent";
    public static final String POLICY_VERSION = "2026-07-11";
    private static final Pattern CONSENT_KEY = Pattern.compile("^[A-Za-z0-9_-]{32,64}$");
    private static final List<String> CATEGORIES = List.of(
            "necessary", "preferences", "analytics", "external_media");
    private final CookieConsentRepository repository;
    private final SessionProperties session;
    private final Clock clock;
    private final SecureRandom random = new SecureRandom();

    public CookieConsentService(CookieConsentRepository repository, SessionProperties session, Clock clock) {
        this.repository = repository;
        this.session = session;
        this.clock = clock;
    }

    public CookieConsentPolicy policy() {
        return PrivacyDtoMapper.cookiePolicy(CATEGORIES, POLICY_VERSION);
    }

    @Transactional(readOnly = true)
    public CookieConsentRead state(HttpServletRequest request) {
        String key = key(request);
        boolean cookiePresent = hasCookie(request);
        if (key == null) {
            LOG.info("privacy_cookie_consent_state request_id={} cookie_present={} valid_cookie=false decision_present=false",
                    requestId(request), cookiePresent);
            return empty();
        }
        CookieConsentRead result = repository.findFirstByConsentKeyOrderByCreatedAtDescIdDesc(key)
                .filter(row -> POLICY_VERSION.equals(row.getPolicyVersion()))
                .map(PrivacyDtoMapper::cookieConsent)
                .orElseGet(this::empty);
        LOG.info("privacy_cookie_consent_state request_id={} cookie_present=true valid_cookie=true decision_present={} policy_version={}",
                requestId(request), Boolean.TRUE.equals(result.hasDecision()), POLICY_VERSION);
        return result;
    }

    @Transactional
    public SavedConsent save(CookieConsentChoice choice, HttpServletRequest request, AuthenticatedUser user) {
        boolean necessary = choice.necessary() == null || choice.necessary();
        if (!necessary) {
            throw new ResponseStatusException(UNPROCESSABLE_CONTENT,
                    "Strictly necessary cookies cannot be disabled.");
        }
        String key = key(request);
        boolean existingValidCookie = key != null;
        if (key == null) key = newKey();
        CookieConsentEntity saved = repository.save(new CookieConsentEntity(
                key,
                user == null ? null : user.id(),
                POLICY_VERSION,
                Boolean.TRUE.equals(choice.preferences()),
                Boolean.TRUE.equals(choice.analytics()),
                Boolean.TRUE.equals(choice.externalMedia()),
                UtcDateTimes.now(clock)));
        CookieConsentRead read = PrivacyDtoMapper.cookieConsent(saved);
        LOG.info("privacy_cookie_consent_save request_id={} authenticated={} existing_valid_cookie={} status=accepted",
                requestId(request), user != null, existingValidCookie);
        return new SavedConsent(read, ResponseCookie.from(COOKIE_NAME, key)
                .httpOnly(true).secure(session.secure()).sameSite(session.sameSite()).path("/")
                .maxAge(java.time.Duration.ofDays(365)).build());
    }

    private CookieConsentRead empty() {
        return PrivacyDtoMapper.emptyCookieConsent(POLICY_VERSION);
    }

    private static String key(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) return null;
        for (Cookie cookie : cookies) {
            if (COOKIE_NAME.equals(cookie.getName()) && CONSENT_KEY.matcher(cookie.getValue()).matches()) {
                return cookie.getValue();
            }
        }
        return null;
    }

    private static boolean hasCookie(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) return false;
        for (Cookie cookie : cookies) {
            if (COOKIE_NAME.equals(cookie.getName())) return true;
        }
        return false;
    }

    private static String requestId(HttpServletRequest request) {
        return ApiRequestAttributes.requestId(request);
    }

    private String newKey() {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    public record SavedConsent(CookieConsentRead body, ResponseCookie cookie) { }
}
