package eu.royalblackwater.api.account;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "registration_requests")
public class RegistrationRequestEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    @Column(nullable = false, length = 80)
    private String username;
    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;
    @Column(name = "display_name", nullable = false, length = 120)
    private String displayName;
    @Column(name = "wants_fleet_membership", nullable = false)
    private boolean wantsFleetMembership;
    @Column(name = "fleet_id")
    private Integer fleetId;
    @Column(name = "fleet_application_note", columnDefinition = "TEXT")
    private String fleetApplicationNote;
    @Column(nullable = false, length = 24)
    private String status;
    @Column(name = "decision_note", columnDefinition = "TEXT")
    private String decisionNote;
    @Column(name = "reviewed_by_id")
    private Integer reviewedById;
    @Column(name = "created_user_id")
    private Integer createdUserId;
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    @Column(name = "reviewed_at")
    private LocalDateTime reviewedAt;

    protected RegistrationRequestEntity() { }

    public RegistrationRequestEntity(String username, String passwordHash, String displayName,
                                     boolean wantsFleetMembership, Integer fleetId, String fleetApplicationNote,
                                     LocalDateTime now) {
        this.username = username;
        this.passwordHash = passwordHash;
        this.displayName = displayName;
        this.wantsFleetMembership = wantsFleetMembership;
        this.fleetId = fleetId;
        this.fleetApplicationNote = fleetApplicationNote;
        this.status = "pending";
        this.createdAt = now;
        this.updatedAt = now;
    }

    public Integer getId() { return id; }
    public String getUsername() { return username; }
    public String getPasswordHash() { return passwordHash; }
    public String getDisplayName() { return displayName; }
    public boolean isWantsFleetMembership() { return wantsFleetMembership; }
    public Integer getFleetId() { return fleetId; }
    public String getFleetApplicationNote() { return fleetApplicationNote; }
    public String getStatus() { return status; }
    public String getDecisionNote() { return decisionNote; }
    public Integer getReviewedById() { return reviewedById; }
    public Integer getCreatedUserId() { return createdUserId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public LocalDateTime getReviewedAt() { return reviewedAt; }

    public void approve(int reviewerId, int createdUserId, String note, LocalDateTime now) {
        this.status = "approved";
        this.decisionNote = note;
        this.reviewedById = reviewerId;
        this.createdUserId = createdUserId;
        this.passwordHash = "!reviewed-registration-secret-removed!";
        this.reviewedAt = now;
        this.updatedAt = now;
    }

    public void reject(int reviewerId, String note, LocalDateTime now) {
        this.status = "rejected";
        this.decisionNote = note;
        this.reviewedById = reviewerId;
        this.passwordHash = "!reviewed-registration-secret-removed!";
        this.reviewedAt = now;
        this.updatedAt = now;
    }
}
