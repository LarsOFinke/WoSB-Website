package eu.royalblackwater.api.privacy;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "cookie_consent_decisions")
public class CookieConsentEntity {
    @Id private Long id;
    @Column(name = "consent_key", nullable = false, length = 64) private String consentKey;
    @Column(name = "policy_version", nullable = false, length = 32) private String policyVersion;
    private boolean necessary;
    private boolean preferences;
    private boolean analytics;
    @Column(name = "external_media") private boolean externalMedia;
    @Column(name = "created_at") private LocalDateTime createdAt;

    public String getPolicyVersion() { return policyVersion; }
    public boolean isNecessary() { return necessary; }
    public boolean isPreferences() { return preferences; }
    public boolean isAnalytics() { return analytics; }
    public boolean isExternalMedia() { return externalMedia; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}
