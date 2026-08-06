package eu.royalblackwater.api.account.repository;

import eu.royalblackwater.api.account.entity.AuthSessionEntity;
import java.time.LocalDateTime;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuthSessionRepository extends JpaRepository<AuthSessionEntity, Integer> {
    Optional<AuthSessionEntity> findByTokenHash(String tokenHash);
    long deleteByTokenHash(String tokenHash);
    long deleteByUserId(Integer userId);
    long deleteByExpiresAtBefore(LocalDateTime threshold);
}
