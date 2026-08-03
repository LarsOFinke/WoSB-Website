package eu.royalblackwater.api.fleet;

import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/fleets")
public class FleetController {
    private final FleetRepository fleets;
    private final FleetMembershipRepository memberships;

    public FleetController(FleetRepository fleets, FleetMembershipRepository memberships) {
        this.fleets = fleets;
        this.memberships = memberships;
    }

    @GetMapping("/public/official")
    @Transactional(readOnly = true)
    public ResponseEntity<FleetContracts.PublicRead> official() {
        return fleets.findFirstByActiveTrueOrderBySortOrderAscIdAsc()
                .map(fleet -> ResponseEntity.ok(toRead(fleet)))
                .orElseGet(() -> ResponseEntity.status(HttpStatus.NOT_FOUND).build());
    }

    private FleetContracts.PublicRead toRead(FleetEntity fleet) {
        List<FleetContracts.Leader> leaders = memberships
                .findLeaders(fleet.getId(), "active")
                .stream()
                .map(row -> new FleetContracts.Leader(row.getUser().getProfile() == null
                                ? row.getUser().getUsername() : row.getUser().getProfile().getDisplayName(),
                        row.getFleetRole().getCode(), row.getFleetRole().getLabel()))
                .toList();
        return new FleetContracts.PublicRead(fleet.getId(), fleet.getName(), fleet.getSlug(), fleet.getFocus(),
                fleet.getDescription(), fleet.getStandingOrders(),
                memberships.countByFleetIdAndStatus(fleet.getId(), "active"), leaders);
    }
}
