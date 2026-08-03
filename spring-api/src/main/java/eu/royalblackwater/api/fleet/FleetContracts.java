package eu.royalblackwater.api.fleet;

import java.util.List;

public final class FleetContracts {
    private FleetContracts() { }
    public record Leader(String displayName, String role, String roleLabel) { }
    public record PublicRead(Long id, String name, String slug, String focus, String description,
                             String standingOrders, long activeMembersCount, List<Leader> leaders) { }
}
