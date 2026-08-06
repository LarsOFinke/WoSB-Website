package eu.royalblackwater.api.fleet.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "fleets")
public class FleetEntity {
    @Id private Integer id;
    private String name;
    private String slug;
    private String focus;
    @Column(columnDefinition = "TEXT") private String description;
    @Column(name = "standing_orders", columnDefinition = "TEXT") private String standingOrders;
    @Column(name = "sort_order") private int sortOrder;
    @Column(name = "is_active") private boolean active;

    public Integer getId() { return id; }
    public String getName() { return name; }
    public String getSlug() { return slug; }
    public String getFocus() { return focus; }
    public String getDescription() { return description; }
    public String getStandingOrders() { return standingOrders; }
}
