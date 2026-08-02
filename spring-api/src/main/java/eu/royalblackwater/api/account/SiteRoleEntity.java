package eu.royalblackwater.api.account;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "site_roles")
public class SiteRoleEntity {
    @Id
    private Integer id;
    @Column(nullable = false, length = 40)
    private String code;
    @Column(name = "is_staff", nullable = false)
    private boolean staff;

    public String getCode() { return code; }
    public boolean isStaff() { return staff; }
}
