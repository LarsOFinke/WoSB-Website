package eu.royalblackwater.api.account;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RegistrationRequestRepository extends JpaRepository<RegistrationRequestEntity, Integer> {
    boolean existsByUsernameAndStatus(String username, String status);
    Optional<RegistrationRequestEntity> findByIdAndStatus(Integer id, String status);
    List<RegistrationRequestEntity> findTop250ByStatusOrderByCreatedAtAscIdAsc(String status);
    List<RegistrationRequestEntity> findTop250ByOrderByCreatedAtDescIdDesc();
}
