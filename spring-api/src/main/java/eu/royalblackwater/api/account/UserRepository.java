package eu.royalblackwater.api.account;

import java.util.Optional;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface UserRepository extends JpaRepository<UserEntity, Integer> {
    @EntityGraph(attributePaths = {"siteRole"})
    Optional<UserEntity> findByUsername(String username);

    @Override
    @EntityGraph(attributePaths = {"siteRole"})
    Optional<UserEntity> findById(Integer id);

    @Query("select u from UserEntity u join fetch u.siteRole where u.id = :id")
    Optional<UserEntity> findAuthenticatedById(@Param("id") Integer id);

    boolean existsByUsername(String username);
}
