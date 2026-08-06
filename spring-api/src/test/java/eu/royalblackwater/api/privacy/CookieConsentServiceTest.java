package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.dto.CookieConsentChoice;
import eu.royalblackwater.api.privacy.entity.CookieConsentEntity;
import eu.royalblackwater.api.privacy.repository.CookieConsentRepository;
import eu.royalblackwater.api.privacy.service.CookieConsentService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import jakarta.servlet.http.Cookie;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.server.ResponseStatusException;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class CookieConsentServiceTest {
    private static final Clock CLOCK = Clock.fixed(
            Instant.parse("2026-08-05T12:00:00Z"), ZoneOffset.UTC);

    @Test
    void rejectsDisablingNecessaryCookiesWithoutPersistingAnything() {
        CookieConsentRepository repository = mock(CookieConsentRepository.class);
        CookieConsentService service = service(repository);

        assertThatThrownBy(() -> service.save(
                new CookieConsentChoice(false, false, false, false),
                new MockHttpServletRequest(),
                null))
                .isInstanceOfSatisfying(ResponseStatusException.class,
                        exception -> assertThat(exception.getStatusCode().value()).isEqualTo(422));
        verify(repository, never()).save(any());
    }

    @Test
    void savesAnAuthenticatedChoiceWithAProtectedCookieAndReusesAValidConsentKey() {
        CookieConsentRepository repository = mock(CookieConsentRepository.class);
        when(repository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        CookieConsentService service = service(repository);
        MockHttpServletRequest request = new MockHttpServletRequest();
        String key = "abcdefghijklmnopqrstuvwxyz_ABCDE-123456";
        request.setCookies(new Cookie(CookieConsentService.COOKIE_NAME, key));
        AuthenticatedUser user = new AuthenticatedUser(42, "member", "user", false, false, false);

        CookieConsentService.SavedConsent saved = service.save(
                new CookieConsentChoice(true, false, true, true), request, user);

        ArgumentCaptor<CookieConsentEntity> row = ArgumentCaptor.forClass(CookieConsentEntity.class);
        verify(repository).save(row.capture());
        assertThat(row.getValue().getConsentKey()).isEqualTo(key);
        assertThat(row.getValue().getUserId()).isEqualTo(42);
        assertThat(row.getValue().isNecessary()).isTrue();
        assertThat(row.getValue().isPreferences()).isTrue();
        assertThat(row.getValue().isAnalytics()).isTrue();
        assertThat(row.getValue().isExternalMedia()).isFalse();
        assertThat(row.getValue().getCreatedAt()).isEqualTo(LocalDateTime.of(2026, 8, 5, 12, 0));
        assertThat(saved.cookie().getValue()).isEqualTo(key);
        assertThat(saved.cookie().toString())
                .contains("HttpOnly", "Secure", "SameSite=Strict", "Path=/", "Max-Age=31536000")
                .doesNotContain("Domain=");
    }

    @Test
    void ignoresMalformedCookieKeysInsteadOfLookingThemUpOrReusingThem() {
        CookieConsentRepository repository = mock(CookieConsentRepository.class);
        when(repository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        CookieConsentService service = service(repository);
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setCookies(new Cookie(CookieConsentService.COOKIE_NAME, "bad key"));

        CookieConsentService.SavedConsent saved = service.save(
                new CookieConsentChoice(false, false, true, false), request, null);

        assertThat(saved.cookie().getValue()).matches("^[A-Za-z0-9_-]{43}$").isNotEqualTo("bad key");
        verify(repository, never()).findFirstByConsentKeyOrderByCreatedAtDescIdDesc(any());
    }

    @Test
    void treatsAStoredDecisionForAnOldPolicyAsUndecided() {
        CookieConsentRepository repository = mock(CookieConsentRepository.class);
        String key = "abcdefghijklmnopqrstuvwxyz_ABCDE-123456";
        when(repository.findFirstByConsentKeyOrderByCreatedAtDescIdDesc(key)).thenReturn(Optional.of(
                new CookieConsentEntity(key, null, "old-policy", true, true, true,
                        LocalDateTime.of(2025, 1, 1, 0, 0))));
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setCookies(new Cookie(CookieConsentService.COOKIE_NAME, key));

        var state = service(repository).state(request);

        assertThat(state.hasDecision()).isFalse();
        assertThat(state.necessary()).isTrue();
        assertThat(state.preferences()).isFalse();
        assertThat(state.analytics()).isFalse();
        assertThat(state.externalMedia()).isFalse();
        assertThat(state.policyVersion()).isEqualTo(CookieConsentService.POLICY_VERSION);
    }

    private static CookieConsentService service(CookieConsentRepository repository) {
        return new CookieConsentService(
                repository,
                new SessionProperties("rbf_hub_session", true, "Strict", Duration.ofHours(24)),
                CLOCK);
    }
}
