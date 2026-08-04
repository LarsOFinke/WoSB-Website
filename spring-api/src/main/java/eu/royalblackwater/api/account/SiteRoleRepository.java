package eu.royalblackwater.api.account;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SiteRoleRepository extends JpaRepository<SiteRoleEntity, Integer> {
    Optional<SiteRoleEntity> findByCode(String code);
}
