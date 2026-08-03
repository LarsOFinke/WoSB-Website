package eu.royalblackwater.api.legal;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "legal_notices")
public class LegalNoticeEntity {
    @Id private Long id;
    private boolean published;
    @Column(name = "provider_name", length = 200) private String providerName;
    @Column(name = "legal_form", length = 120) private String legalForm;
    @Column(name = "represented_by", length = 300) private String representedBy;
    @Column(length = 200) private String street;
    @Column(name = "postal_code", length = 32) private String postalCode;
    @Column(length = 120) private String city;
    @Column(length = 120) private String country;
    @Column(length = 254) private String email;
    @Column(length = 80) private String phone;
    @Column(name = "register_name", length = 160) private String registerName;
    @Column(name = "register_court", length = 200) private String registerCourt;
    @Column(name = "register_number", length = 120) private String registerNumber;
    @Column(name = "vat_id", length = 80) private String vatId;
    @Column(name = "business_id", length = 120) private String businessId;
    @Column(name = "supervisory_authority", length = 500) private String supervisoryAuthority;
    @Column(name = "editorial_responsible_name", length = 200) private String editorialResponsibleName;
    @Column(name = "editorial_responsible_street", length = 200) private String editorialResponsibleStreet;
    @Column(name = "editorial_responsible_postal_code", length = 32) private String editorialResponsiblePostalCode;
    @Column(name = "editorial_responsible_city", length = 120) private String editorialResponsibleCity;
    @Column(name = "editorial_responsible_country", length = 120) private String editorialResponsibleCountry;
    @Column(name = "dispute_resolution_text", columnDefinition = "TEXT") private String disputeResolutionText;
    @Column(name = "additional_information", columnDefinition = "TEXT") private String additionalInformation;
    @Column(name = "updated_at") private LocalDateTime updatedAt;

    public boolean isPublished() { return published; }
    public String getProviderName() { return providerName; }
    public String getLegalForm() { return legalForm; }
    public String getRepresentedBy() { return representedBy; }
    public String getStreet() { return street; }
    public String getPostalCode() { return postalCode; }
    public String getCity() { return city; }
    public String getCountry() { return country; }
    public String getEmail() { return email; }
    public String getPhone() { return phone; }
    public String getRegisterName() { return registerName; }
    public String getRegisterCourt() { return registerCourt; }
    public String getRegisterNumber() { return registerNumber; }
    public String getVatId() { return vatId; }
    public String getBusinessId() { return businessId; }
    public String getSupervisoryAuthority() { return supervisoryAuthority; }
    public String getEditorialResponsibleName() { return editorialResponsibleName; }
    public String getEditorialResponsibleStreet() { return editorialResponsibleStreet; }
    public String getEditorialResponsiblePostalCode() { return editorialResponsiblePostalCode; }
    public String getEditorialResponsibleCity() { return editorialResponsibleCity; }
    public String getEditorialResponsibleCountry() { return editorialResponsibleCountry; }
    public String getDisputeResolutionText() { return disputeResolutionText; }
    public String getAdditionalInformation() { return additionalInformation; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
