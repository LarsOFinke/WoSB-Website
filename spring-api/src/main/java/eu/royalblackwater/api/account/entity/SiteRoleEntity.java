package eu.royalblackwater.api.account.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "site_roles")
public class SiteRoleEntity {
    @Id
    private Integer id;
    @Column(nullable = false, unique = true, length = 32)
    private String code;
    @Column(nullable = false, length = 80)
    private String label;
    @Column(nullable = false)
    private int rank;
    @Column(name = "is_staff", nullable = false)
    private boolean staff;
    @Column(name = "can_manage_system", nullable = false)
    private boolean canManageSystem;
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    protected SiteRoleEntity() { }

    public Integer getId() { return id; }
    public String getCode() { return code; }
    public String getLabel() { return label; }
    public int getRank() { return rank; }
    public boolean isStaff() { return staff; }
    public boolean canManageSystem() { return canManageSystem; }
}
