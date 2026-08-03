package eu.royalblackwater.api.fleet;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "fleet_roles")
public class FleetRoleEntity {
    @Id private Integer id;
    private String code;
    private String label;
    private int rank;
    @Column(name = "is_leadership")
    private boolean leadership;

    public boolean isLeadership() { return leadership; }
    public int getRank() { return rank; }
    public String getCode() { return code; }
    public String getLabel() { return label; }
}
