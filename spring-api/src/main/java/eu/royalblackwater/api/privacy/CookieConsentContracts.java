package eu.royalblackwater.api.privacy;

import java.time.LocalDateTime;
import java.util.List;

public final class CookieConsentContracts {
    public static final String POLICY_VERSION = "2026-07-11";
    public static final List<String> CATEGORIES = List.of("necessary", "preferences", "analytics", "external_media");

    private CookieConsentContracts() { }

    public record Policy(String version, List<String> categories) { }
    public record Read(boolean hasDecision, String policyVersion, boolean necessary, boolean preferences,
                       boolean analytics, boolean externalMedia, LocalDateTime decidedAt) { }
}
