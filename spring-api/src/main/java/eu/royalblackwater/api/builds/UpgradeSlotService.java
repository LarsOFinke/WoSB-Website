package eu.royalblackwater.api.builds;

import java.util.List;
import org.springframework.stereotype.Component;

@Component
class UpgradeSlotService {
    UpgradeSlotAccess calculate(BuildShipSnapshot ship, BuildFeatureSnapshot feature,
                                List<BuildSlotSelection> slots) {
        int baseSlots = Math.min(Math.max(ship.upgradeSlots(), 0), 4);
        int research = ship.upgradeSlots() > 0 && feature != null
                ? Math.min(Math.max(feature.grantedSlots(), 0), 8 - baseSlots) : 0;
        int shipExtra = Math.min(Math.max(ship.upgradeSlots() - 5, 0), 8 - baseSlots);
        int preExpansion = Math.min(8, baseSlots + research + shipExtra);
        int expansion = slots.stream()
                .filter(slot -> slot.type().equals("upgrade") && slot.index() <= preExpansion)
                .mapToInt(slot -> Math.max(0, integer(slot.option().effects().get("extra_upgrade_slots"))))
                .sum();
        expansion = ship.upgradeSlots() > 0 ? Math.min(expansion, 8 - baseSlots) : 0;
        int available = Math.min(8, baseSlots + research + shipExtra + expansion);
        return new UpgradeSlotAccess(baseSlots, available >= 5, available >= 6, available >= 7,
                available >= 8, expansion, research, shipExtra, available);
    }

    private static int integer(Number value) { return value == null ? 0 : value.intValue(); }
}
