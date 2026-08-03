package eu.royalblackwater.api.fleet;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FleetRepository extends JpaRepository<FleetEntity, Integer> {
    Optional<FleetEntity> findFirstByActiveTrueOrderBySortOrderAscIdAsc();
}
