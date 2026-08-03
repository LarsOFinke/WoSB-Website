package eu.royalblackwater.api.privacy;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CookieConsentRepository extends JpaRepository<CookieConsentEntity, Long> {
    Optional<CookieConsentEntity> findFirstByConsentKeyOrderByCreatedAtDescIdDesc(String consentKey);
}
