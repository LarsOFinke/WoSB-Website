package eu.royalblackwater.api.account.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "user_profile_role_preferences")
public class UserProfileRolePreferenceEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    @ManyToOne(optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private UserProfileEntity profile;
    @Column(name = "fleet_role_id", nullable = false)
    private Integer fleetRoleId;
    @Column(name = "sort_order", nullable = false)
    private int sortOrder;

    protected UserProfileRolePreferenceEntity() { }
    UserProfileRolePreferenceEntity(UserProfileEntity profile, Integer fleetRoleId, int sortOrder) {
        this.profile = profile;
        this.fleetRoleId = fleetRoleId;
        this.sortOrder = sortOrder;
    }
    public Integer getFleetRoleId() { return fleetRoleId; }
}
