package eu.royalblackwater.api.fleet.repository;

import eu.royalblackwater.api.fleet.entity.FleetMembershipEntity;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface FleetMembershipRepository extends JpaRepository<FleetMembershipEntity, Integer> {
    long countByFleet_IdAndStatus(Integer fleetId, String status);

    @EntityGraph(attributePaths = {"user", "user.profile", "fleetRole", "fleet"})
    @Query("select m from FleetMembershipEntity m where m.fleet.id = :fleetId and m.status = :status "
            + "and m.fleetRole.leadership = true order by m.fleetRole.rank desc, m.joinedAt asc, m.id asc")
    List<FleetMembershipEntity> findLeaders(@Param("fleetId") Integer fleetId, @Param("status") String status);

    @EntityGraph(attributePaths = {"fleet", "fleetRole", "user", "user.profile"})
    @Query("select m from FleetMembershipEntity m where m.user.id = :userId and m.status in ('active', 'pending') "
            + "order by case when m.status = 'active' then 0 else 1 end, m.fleetRole.rank desc, m.id asc")
    List<FleetMembershipEntity> findProfileMemberships(@Param("userId") Integer userId);

    @EntityGraph(attributePaths = {"fleet", "fleetRole", "user", "user.profile"})
    Optional<FleetMembershipEntity> findByUser_Id(Integer userId);

    boolean existsByUser_Id(Integer userId);
}
