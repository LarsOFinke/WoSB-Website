package eu.royalblackwater.api.fleet.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "fleet_roles")
public class FleetRoleEntity {
    @Id private Integer id;
    @Column(nullable = false, unique = true, length = 40) private String code;
    @Column(nullable = false, length = 80) private String label;
    @Column(nullable = false) private int rank;
    @Column(name = "is_leadership", nullable = false) private boolean leadership;
    @Column(name = "can_manage_fleet", nullable = false) private boolean canManageFleet;
    @Column(name = "can_manage_members", nullable = false) private boolean canManageMembers;
    @Column(name = "is_system", nullable = false) private boolean system;
    @Column(name = "is_active", nullable = false) private boolean active;
    @Column(name = "created_at", nullable = false) private LocalDateTime createdAt;
    @Column(name = "updated_at", nullable = false) private LocalDateTime updatedAt;

    protected FleetRoleEntity() { }
    public Integer getId() { return id; }
    public boolean isLeadership() { return leadership; }
    public int getRank() { return rank; }
    public String getCode() { return code; }
    public String getLabel() { return label; }
    public boolean canManageFleet() { return canManageFleet; }
    public boolean canManageMembers() { return canManageMembers; }
    public boolean isSystem() { return system; }
    public boolean isActive() { return active; }
}
