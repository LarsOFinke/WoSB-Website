package eu.royalblackwater.api.privacy;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "cookie_consent_decisions")
public class CookieConsentEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    @Column(name = "consent_key", nullable = false, length = 64) private String consentKey;
    @Column(name = "user_id") private Integer userId;
    @Column(name = "policy_version", nullable = false, length = 32) private String policyVersion;
    private boolean necessary;
    private boolean preferences;
    private boolean analytics;
    @Column(name = "external_media") private boolean externalMedia;
    @Column(name = "created_at") private LocalDateTime createdAt;

    public String getPolicyVersion() { return policyVersion; }
    String getConsentKey() { return consentKey; }
    Integer getUserId() { return userId; }
    public boolean isNecessary() { return necessary; }
    public boolean isPreferences() { return preferences; }
    public boolean isAnalytics() { return analytics; }
    public boolean isExternalMedia() { return externalMedia; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public CookieConsentEntity() { }
    public CookieConsentEntity(String consentKey, Integer userId, String policyVersion, boolean preferences,
                               boolean analytics, boolean externalMedia, LocalDateTime createdAt) {
        this.consentKey = consentKey;
        this.userId = userId;
        this.policyVersion = policyVersion;
        this.necessary = true;
        this.preferences = preferences;
        this.analytics = analytics;
        this.externalMedia = externalMedia;
        this.createdAt = createdAt;
    }
}
