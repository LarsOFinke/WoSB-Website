package eu.royalblackwater.api.account;

import java.time.LocalDateTime;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuthSessionRepository extends JpaRepository<AuthSessionEntity, Long> {
    Optional<AuthSessionEntity> findByTokenHash(String tokenHash);
    long deleteByTokenHash(String tokenHash);
    long deleteByUserId(Long userId);
    long deleteByExpiresAtBefore(LocalDateTime threshold);
}
