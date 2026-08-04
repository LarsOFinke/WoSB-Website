package eu.royalblackwater.api.account;

import eu.royalblackwater.api.fleet.FleetMembershipEntity;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "users")
public class UserEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    @Column(nullable = false, unique = true, length = 80)
    private String username;
    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "site_role_id", nullable = false)
    private SiteRoleEntity siteRole;
    @Column(name = "is_active", nullable = false)
    private boolean active;
    @Column(name = "is_bootstrap_admin", nullable = false)
    private boolean bootstrapAdmin;
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    @OneToOne(mappedBy = "user", fetch = FetchType.LAZY, cascade = CascadeType.ALL, orphanRemoval = true)
    private UserProfileEntity profile;
    @OneToMany(mappedBy = "user", fetch = FetchType.LAZY)
    private List<FleetMembershipEntity> fleetMemberships = new ArrayList<>();

    protected UserEntity() { }

    public UserEntity(String username, String passwordHash, SiteRoleEntity siteRole, String displayName,
                      LocalDateTime createdAt) {
        this.username = username;
        this.passwordHash = passwordHash;
        this.siteRole = siteRole;
        this.active = true;
        this.bootstrapAdmin = false;
        this.createdAt = createdAt;
        this.updatedAt = createdAt;
        this.profile = new UserProfileEntity(this, displayName, createdAt);
    }

    public Integer getId() { return id; }
    public String getUsername() { return username; }
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }
    public SiteRoleEntity getSiteRole() { return siteRole; }
    public void setSiteRole(SiteRoleEntity siteRole) { this.siteRole = siteRole; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
    public boolean isBootstrapAdmin() { return bootstrapAdmin; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void touch(LocalDateTime now) { this.updatedAt = now; }
    public UserProfileEntity getProfile() { return profile; }
    public UserProfileEntity ensureProfile(LocalDateTime now) {
        if (profile == null) {
            profile = new UserProfileEntity(this, username, now);
        }
        return profile;
    }
    public List<FleetMembershipEntity> getFleetMemberships() { return fleetMemberships; }
}
