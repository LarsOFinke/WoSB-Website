package eu.royalblackwater.api.privacy.repository;

import eu.royalblackwater.api.privacy.entity.CookieConsentEntity;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CookieConsentRepository extends JpaRepository<CookieConsentEntity, Integer> {
    Optional<CookieConsentEntity> findFirstByConsentKeyOrderByCreatedAtDescIdDesc(String consentKey);
}
