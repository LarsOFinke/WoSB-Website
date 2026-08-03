package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.account.UserEntity;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import java.time.LocalDateTime;

@Entity
@Table(name = "fleet_memberships")
public class FleetMembershipEntity {
    @Id private Integer id;
    @Column(name = "fleet_id", nullable = false) private Integer fleetId;
    @ManyToOne(fetch = FetchType.EAGER) @JoinColumn(name = "user_id", nullable = false) private UserEntity user;
    @ManyToOne(fetch = FetchType.EAGER) @JoinColumn(name = "fleet_role_id", nullable = false) private FleetRoleEntity fleetRole;
    private String status;
    @Column(name = "joined_at") private LocalDateTime joinedAt;

    public Integer getId() { return id; }
    public Integer getFleetId() { return fleetId; }
    public LocalDateTime getJoinedAt() { return joinedAt; }

    public UserEntity getUser() { return user; }
    public FleetRoleEntity getFleetRole() { return fleetRole; }
    public String getStatus() { return status; }
}
