package eu.royalblackwater.api.fleet;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface FleetMembershipRepository extends JpaRepository<FleetMembershipEntity, Long> {
    long countByFleetIdAndStatus(Long fleetId, String status);
    @Query("select m from FleetMembershipEntity m where m.fleetId = :fleetId and m.status = :status "
            + "and m.fleetRole.leadership = true order by m.fleetRole.rank desc, m.joinedAt asc, m.id asc")
    List<FleetMembershipEntity> findLeaders(@Param("fleetId") Long fleetId, @Param("status") String status);
}
