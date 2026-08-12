package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.builds.dto.BuildCatalogOption;
import eu.royalblackwater.api.builds.filter.WeaponOptionCompatibility;
import eu.royalblackwater.api.builds.dto.BuildEffects;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.builds.dto.BuildPreparedPayload;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.builds.dto.BuildSlotSelection;
import eu.royalblackwater.api.builds.dto.UpgradeSlotAccess;
import eu.royalblackwater.api.builds.repository.BuildCatalogRepository;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.queries.BuildValidationQueries;
import eu.royalblackwater.api.dto.InventorySlot;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

@Service
public class BuildValidationService {
    private static final List<String> WEAPON_SLOTS = List.of(
            "weapon_front", "weapon_rear", "weapon_port", "weapon_starboard", "weapon_mortar", "weapon_special");
    private final BuildCatalogRepository catalog;
    private final BuildDataRepository repository;
    private final BuildEffectService effects;
    private final UpgradeSlotService upgradeSlots;

    public BuildValidationService(BuildCatalogRepository catalog, BuildDataRepository repository, BuildEffectService effects,
                           UpgradeSlotService upgradeSlots) {
        this.catalog = catalog;
        this.repository = repository;
        this.effects = effects;
        this.upgradeSlots = upgradeSlots;
    }

    public BuildPreparedPayload prepare(BuildPayload payload) {
        if (repository.count(BuildValidationQueries.PREPARE_SELECT_01, Map.of("slug", payload.type())) == 0) {
            reject("The selected build role does not exist.");
        }
        BuildShipSnapshot ship = catalog.ship(payload.shipId()).orElseThrow(
                () -> new ResponseStatusException(BAD_REQUEST, "The selected ship does not exist."));
        if (payload.mortarModification() && ship.mortarModification() == null) {
            reject("The selected ship does not support the Mortar Modification.");
        }
        BuildFeatureSnapshot feature = payload.researchSlot() ? catalog.researchFeature().orElseThrow(
                () -> new ResponseStatusException(BAD_REQUEST, "The upgrade add-on slot rule is unavailable.")) : null;
        List<BuildCatalogOption> options = catalog.options(payload.shipId());
        Map<String, BuildCatalogOption> byCategoryAndName = new HashMap<>();
        for (BuildCatalogOption option : options) {
            byCategoryAndName.put(key(option.category(), option.name()), option);
        }
        List<BuildSlotSelection> slots = createSlots(payload, ship, byCategoryAndName);
        UpgradeSlotAccess access = validateUpgrades(payload, ship, feature, slots);
        BuildEffects resolvedEffects = effects.resolve(payload, ship, feature, slots);
        validateCrew(payload, ship, resolvedEffects.sets(), resolvedEffects.totals());
        return new BuildPreparedPayload(payload, ship, feature, List.copyOf(slots), resolvedEffects.sets(),
                resolvedEffects.totals(), access);
    }

    private List<BuildSlotSelection> createSlots(BuildPayload payload, BuildShipSnapshot ship,
                                                  Map<String, BuildCatalogOption> options) {
        List<BuildSlotSelection> slots = new ArrayList<>();
        if (payload.sails() != null) slots.add(single(options, "sail", payload.sails(), "sail", 1));
        if (payload.lantern() != null) {
            if (!ship.hasLantern()) reject("The selected ship has no lantern slot.");
            slots.add(single(options, "lantern", payload.lantern(), "lantern", 1));
        }
        Set<String> upgradeNames = new HashSet<>();
        for (int index = 0; index < payload.upgrades().size(); index++) {
            String name = payload.upgrades().get(index);
            if (name == null) continue;
            if (!upgradeNames.add(name.toLowerCase(Locale.ROOT))) reject("Upgrades: each upgrade can only be selected once.");
            slots.add(single(options, "upgrade", name, "upgrade", index + 1));
        }
        for (String slotType : WEAPON_SLOTS) appendInventory(slots, options, payload.slots(slotType),
                "weapon", slotType, ship, payload.mortarModification());
        appendInventory(slots, options, payload.specialCrew(), "special_crew", "special_crew", ship, payload.mortarModification());
        appendInventory(slots, options, payload.ammunition(), "ammunition", "ammunition", ship, payload.mortarModification());
        appendInventory(slots, options, payload.consumables(), "consumable", "consumable", ship, payload.mortarModification());
        appendInventory(slots, options, payload.hold(), "hold", "hold", ship, payload.mortarModification());
        validateInventory(payload);
        return slots;
    }

    private BuildSlotSelection single(Map<String, BuildCatalogOption> options, String category, String name,
                                      String slotType, int index) {
        BuildCatalogOption option = require(options, category, name, category);
        return new BuildSlotSelection(slotType, index, option.id(), option.name(), 1, option);
    }

    private void appendInventory(List<BuildSlotSelection> target, Map<String, BuildCatalogOption> options,
                                 List<InventorySlot> values, String category, String slotType,
                                 BuildShipSnapshot ship, boolean mortarModified) {
        requireUnique(values, slotType);
        int total = 0;
        for (int index = 0; index < values.size(); index++) {
            InventorySlot value = values.get(index);
            BuildCatalogOption option = require(options, category, value.item(), slotType);
            int quantity = Math.toIntExact(value.quantity() == null ? 1 : value.quantity());
            if (slotType.startsWith("weapon_")) {
                if (!option.allowedSlots().contains(slotType)) reject(slotType + ": '" + option.name() + "' is not compatible with this mount.");
                total += quantity;
                validateWeapon(option, ship, slotType, mortarModified);
            }
            target.add(new BuildSlotSelection(slotType, index + 1, option.id(), option.name(), quantity, option));
        }
        if (slotType.startsWith("weapon_")) {
            int rowLimit = List.of("weapon_mortar", "weapon_special").contains(slotType) ? 8 : 12;
            if (values.size() > rowLimit) reject(slotType + " is limited to " + rowLimit + " item rows.");
            int capacity = ship.capacity(slotType, mortarModified);
            if (total > capacity) reject(slotType + ": selected quantity exceeds this ship's capacity (" + capacity + ").");
            int special = target.stream().filter(slot -> slot.type().equals(slotType))
                    .filter(slot -> "special_weapon".equals(slot.option().kind())).mapToInt(BuildSlotSelection::quantity).sum();
            if (special > ship.specialCapacity(slotType)) reject(slotType + ": special-weapon capacity exceeded.");
        }
    }

    private void validateWeapon(BuildCatalogOption option, BuildShipSnapshot ship, String slotType, boolean mortarModified) {
        if ("weapon_mortar".equals(slotType)) {
            Double max = ship.mortarCaliber(mortarModified);
            if (!WeaponOptionCompatibility.isMortarKind(option.kind())) reject("Mortar slots only accept mortars.");
            if (!WeaponOptionCompatibility.isMortarCompatible(option.kind(), option.caliber(), max)) {
                reject("Mortar caliber exceeds this ship's limit.");
            }
        } else if ("weapon_special".equals(slotType) && !"special_weapon".equals(option.kind())) {
            reject("Dedicated special slots only accept special weapons.");
        }
    }

    private UpgradeSlotAccess validateUpgrades(BuildPayload payload, BuildShipSnapshot ship,
                                                BuildFeatureSnapshot feature, List<BuildSlotSelection> slots) {
        if (ship.upgradeSlots() == 0 && slots.stream().anyMatch(slot -> slot.type().equals("upgrade"))) {
            reject("The selected ship has no upgrade rack.");
        }
        UpgradeSlotAccess access = upgradeSlots.calculate(ship, feature, slots);
        for (BuildSlotSelection slot : slots) {
            if (slot.type().equals("upgrade") && slot.index() > access.availableSlots()) {
                reject("Upgrade slot " + slot.index() + " is locked for this build.");
            }
        }
        return access;
    }

    private static void validateCrew(BuildPayload payload, BuildShipSnapshot ship,
                                     List<Map<String, Number>> effectSets, Map<String, Number> totals) {
        double multiplier = 1;
        for (Map<String, Number> set : effectSets) multiplier *= 1 + decimal(set.get("crew_capacity_pct")) / 100.0;
        long effectiveCapacity = Math.max(0, BuildStatCalculator.roundWhole(
                ship.crewCapacity() * multiplier + decimal(totals.get("crew_capacity"))));
        long minimum = Math.max(0, ship.sailorMinimum() + integer(totals.get("sailor_minimum")));
        if (payload.sailors() < minimum) reject("Sailors are below this build's required minimum (" + minimum + ").");
        long total = payload.sailors() + payload.soldiers() + payload.musketeers() + payload.mercenaries();
        if (total > effectiveCapacity) reject("The crew distribution exceeds the effective ship capacity (" + effectiveCapacity + ").");
    }

    private static void validateInventory(BuildPayload payload) {
        long regular = payload.specialCrew().stream().filter(slot -> !slot.item().equalsIgnoreCase("Ginger")).count();
        if (regular > 4) reject("Special crew is limited to 4 regular specialists. Ginger uses an extra slot.");
        if (payload.specialCrew().size() > 5) reject("Special crew is limited to 5 rows.");
        if (payload.consumables().size() > 3) reject("Consumables are limited to 3 slots.");
    }

    private static void requireUnique(List<InventorySlot> values, String label) {
        Set<String> names = new HashSet<>();
        for (InventorySlot value : values) if (!names.add(value.item().toLowerCase(Locale.ROOT))) {
            reject(label + ": an item can only be selected once.");
        }
    }
    private static BuildCatalogOption require(Map<String, BuildCatalogOption> options, String category,
                                              String name, String label) {
        BuildCatalogOption option = options.get(key(category, name));
        if (option == null) reject(label + ": '" + name + "' is not a valid option.");
        return option;
    }
    private static String key(String category, String name) { return category + "\u0000" + name.strip().toLowerCase(Locale.ROOT); }
    private static int integer(Number value) { return value == null ? 0 : value.intValue(); }
    private static double decimal(Number value) { return value == null ? 0 : value.doubleValue(); }
    private static void reject(String message) { throw new ResponseStatusException(BAD_REQUEST, message); }
}
