package eu.royalblackwater.api.config;

import java.net.URI;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.legal-notice")
public record LegalNoticeProperties(
        boolean published,
        String providerName,
        String legalForm,
        String representedBy,
        String street,
        String postalCode,
        String city,
        String country,
        String email,
        String phone,
        String registerName,
        String registerCourt,
        String registerNumber,
        String vatId,
        String businessId,
        String supervisoryAuthority,
        String editorialResponsibleName,
        String editorialResponsibleStreet,
        String editorialResponsiblePostalCode,
        String editorialResponsibleCity,
        String editorialResponsibleCountry,
        String disputeResolutionText,
        String additionalInformation,
        String publicRepositoryUrl) {

    public LegalNoticeProperties {
        providerName = value(providerName);
        legalForm = value(legalForm);
        representedBy = value(representedBy);
        street = value(street);
        postalCode = value(postalCode);
        city = value(city);
        country = defaultValue(country, "Deutschland");
        email = value(email);
        phone = value(phone);
        registerName = value(registerName);
        registerCourt = value(registerCourt);
        registerNumber = value(registerNumber);
        vatId = value(vatId);
        businessId = value(businessId);
        supervisoryAuthority = value(supervisoryAuthority);
        editorialResponsibleName = value(editorialResponsibleName);
        editorialResponsibleStreet = value(editorialResponsibleStreet);
        editorialResponsiblePostalCode = value(editorialResponsiblePostalCode);
        editorialResponsibleCity = value(editorialResponsibleCity);
        editorialResponsibleCountry = defaultValue(editorialResponsibleCountry, "Deutschland");
        disputeResolutionText = value(disputeResolutionText);
        additionalInformation = value(additionalInformation);
        publicRepositoryUrl = secureUrl(publicRepositoryUrl);
    }

    private static String value(String value) {
        return value == null ? "" : value.strip();
    }

    private static String defaultValue(String value, String fallback) {
        String normalized = value(value);
        return normalized.isEmpty() ? fallback : normalized;
    }

    private static String secureUrl(String value) {
        String normalized = value(value);
        try {
            URI uri = URI.create(normalized);
            return "https".equalsIgnoreCase(uri.getScheme()) && uri.getHost() != null
                    && uri.getUserInfo() == null ? normalized : "";
        } catch (IllegalArgumentException ignored) {
            return "";
        }
    }
}
