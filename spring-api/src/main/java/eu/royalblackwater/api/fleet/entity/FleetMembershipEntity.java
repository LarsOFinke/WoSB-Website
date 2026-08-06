package eu.royalblackwater.api.fleet.entity;

import eu.royalblackwater.api.account.entity.UserEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "fleet_memberships")
public class FleetMembershipEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "fleet_id", nullable = false)
    private FleetEntity fleet;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private UserEntity user;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "fleet_role_id", nullable = false)
    private FleetRoleEntity fleetRole;
    @Column(nullable = false, length = 40)
    private String status;
    @Column(columnDefinition = "TEXT")
    private String note;
    @Column(length = 120)
    private String assignment;
    @Column(name = "admin_note", columnDefinition = "TEXT")
    private String adminNote;
    @Column(name = "joined_at", nullable = false)
    private LocalDateTime joinedAt;
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected FleetMembershipEntity() { }
    public Integer getId() { return id; }
    public Integer getFleetId() { return fleet.getId(); }
    public FleetEntity getFleet() { return fleet; }
    public UserEntity getUser() { return user; }
    public FleetRoleEntity getFleetRole() { return fleetRole; }
    public String getStatus() { return status; }
    public String getNote() { return note; }
    public String getAssignment() { return assignment; }
    public String getAdminNote() { return adminNote; }
    public LocalDateTime getJoinedAt() { return joinedAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
