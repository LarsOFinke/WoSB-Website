package eu.royalblackwater.api.account;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "user_profiles")
public class UserProfileEntity {
    @Id
    @Column(name = "user_id")
    private Integer userId;
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

    public String getDisplayName() { return displayName; }
    public String getExternalFleetName() { return externalFleetName; }
    public String getPreferredFocus() { return preferredFocus; }
    public String getAvailability() { return availability; }
    public String getTimezone() { return timezone; }
    public String getDiscordHandle() { return discordHandle; }
    public String getNote() { return note; }
}
