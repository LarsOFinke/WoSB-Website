package eu.royalblackwater.api.account;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "user_profile_ship_preferences")
public class UserProfileShipPreferenceEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    @ManyToOne(optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private UserProfileEntity profile;
    @Column(name = "ship_id", nullable = false)
    private Integer shipId;
    @Column(name = "sort_order", nullable = false)
    private int sortOrder;

    protected UserProfileShipPreferenceEntity() { }
    UserProfileShipPreferenceEntity(UserProfileEntity profile, Integer shipId, int sortOrder) {
        this.profile = profile;
        this.shipId = shipId;
        this.sortOrder = sortOrder;
    }
    public Integer getShipId() { return shipId; }
}
