package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.privacy.entity.CookieConsentEntity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class CookieConsentEntityTest {
    @Test
    void consentRowsUseTheDatabaseIdentityColumn() throws NoSuchFieldException {
        GeneratedValue generated = CookieConsentEntity.class.getDeclaredField("id")
                .getAnnotation(GeneratedValue.class);

        assertEquals(GenerationType.IDENTITY, generated.strategy());
    }
}
