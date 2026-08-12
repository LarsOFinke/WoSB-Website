package eu.royalblackwater.api.builds.filter;

import java.util.Set;

/** Shared weapon-kind compatibility rules used by catalog filtering and build validation. */
public final class WeaponOptionCompatibility {
    private static final Set<String> MORTAR_KINDS = Set.of("mortar", "mortar_launcher", "mortar_universal");

    private WeaponOptionCompatibility() { }

    public static boolean isMortarKind(String kind) {
        return MORTAR_KINDS.contains(kind);
    }

    public static boolean isMortarCompatible(String kind, Double caliber, Double maximumCaliber) {
        if (!isMortarKind(kind)) return false;
        if ("mortar_launcher".equals(kind) || "mortar_universal".equals(kind)) return true;
        return caliber == null || maximumCaliber != null && caliber <= maximumCaliber;
    }
}
