package eu.royalblackwater.api.fleet.repository;

import eu.royalblackwater.api.fleet.entity.FleetEntity;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FleetRepository extends JpaRepository<FleetEntity, Integer> {
    Optional<FleetEntity> findFirstByActiveTrueOrderBySortOrderAscIdAsc();
}
