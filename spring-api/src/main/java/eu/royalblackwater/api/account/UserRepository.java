package eu.royalblackwater.api.account;

import java.util.Optional;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<UserEntity, Integer> {
    @EntityGraph(attributePaths = {"siteRole"})
    Optional<UserEntity> findByUsername(String username);

    @Override
    @EntityGraph(attributePaths = {"siteRole"})
    Optional<UserEntity> findById(Integer id);

    boolean existsByUsername(String username);
}
