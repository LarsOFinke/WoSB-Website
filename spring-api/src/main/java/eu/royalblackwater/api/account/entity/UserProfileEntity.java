package eu.royalblackwater.api.account.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.MapsId;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "user_profiles")
public class UserProfileEntity {
    @Id
    @Column(name = "user_id")
    private Integer userId;
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @MapsId
    @JoinColumn(name = "user_id")
    private UserEntity user;
    @Column(name = "display_name", nullable = false, length = 120)
    private String displayName;
    @Column(name = "external_fleet_name", length = 120)
    private String externalFleetName;
    @Column(name = "preferred_focus", length = 80)
    private String preferredFocus;
    @Column(length = 240)
    private String availability;
    @Column(length = 80)
    private String timezone;
    @Column(name = "discord_handle", length = 120)
    private String discordHandle;
    @Column(columnDefinition = "TEXT")
    private String note;
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    @OneToMany(mappedBy = "profile", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("sortOrder ASC, id ASC")
    private List<UserProfileShipPreferenceEntity> shipPreferences = new ArrayList<>();
    @OneToMany(mappedBy = "profile", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("sortOrder ASC, id ASC")
    private List<UserProfileRolePreferenceEntity> rolePreferences = new ArrayList<>();

    protected UserProfileEntity() { }

    UserProfileEntity(UserEntity user, String displayName, LocalDateTime now) {
        this.user = user;
        this.displayName = displayName;
        this.createdAt = now;
        this.updatedAt = now;
    }

    public Integer getUserId() { return userId; }
    public String getDisplayName() { return displayName; }
    public String getExternalFleetName() { return externalFleetName; }
    public String getPreferredFocus() { return preferredFocus; }
    public String getAvailability() { return availability; }
    public String getTimezone() { return timezone; }
    public String getDiscordHandle() { return discordHandle; }
    public String getNote() { return note; }
    public List<UserProfileShipPreferenceEntity> getShipPreferences() { return shipPreferences; }
    public List<UserProfileRolePreferenceEntity> getRolePreferences() { return rolePreferences; }

    public void update(String displayName, String externalFleetName, String preferredFocus, String availability,
                       String timezone, String discordHandle, String note, LocalDateTime now) {
        this.displayName = displayName;
        this.externalFleetName = externalFleetName;
        this.preferredFocus = preferredFocus;
        this.availability = availability;
        this.timezone = timezone;
        this.discordHandle = discordHandle;
        this.note = note;
        this.updatedAt = now;
    }

    public void replaceShipPreferences(List<Integer> ids) {
        shipPreferences.clear();
        for (int index = 0; index < ids.size(); index++) {
            shipPreferences.add(new UserProfileShipPreferenceEntity(this, ids.get(index), (index + 1) * 10));
        }
    }

    public void replaceRolePreferences(List<Integer> ids) {
        rolePreferences.clear();
        for (int index = 0; index < ids.size(); index++) {
            rolePreferences.add(new UserProfileRolePreferenceEntity(this, ids.get(index), (index + 1) * 10));
        }
    }
}
