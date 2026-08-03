package eu.royalblackwater.api.account;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

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
    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "site_role_id", nullable = false)
    private SiteRoleEntity siteRole;
    @Column(name = "is_active", nullable = false)
    private boolean active;
    @Column(name = "is_bootstrap_admin", nullable = false)
    private boolean bootstrapAdmin;
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    @OneToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "id", referencedColumnName = "user_id", insertable = false, updatable = false)
    private UserProfileEntity profile;

    public Integer getId() { return id; }
    public String getUsername() { return username; }
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }
    public SiteRoleEntity getSiteRole() { return siteRole; }
    public boolean isActive() { return active; }
    public boolean isBootstrapAdmin() { return bootstrapAdmin; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public UserProfileEntity getProfile() { return profile; }
}
