package eu.royalblackwater.api.builds.mapper;

import eu.royalblackwater.api.builds.dto.BuildAggregate;
import eu.royalblackwater.api.builds.dto.BuildCatalogOption;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildPageResult;
import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.builds.dto.BuildSlotSelection;
import eu.royalblackwater.api.builds.service.BuildStatCatalog;
import eu.royalblackwater.api.builds.dto.BuildStoredSlot;
import eu.royalblackwater.api.builds.dto.UpgradeSlotAccess;
import eu.royalblackwater.api.builds.repository.BuildCatalogRepository;
import eu.royalblackwater.api.builds.service.BuildStatsService;
import eu.royalblackwater.api.builds.service.UpgradeSlotService;
import eu.royalblackwater.api.dto.BuildItemCategoryRead;
import eu.royalblackwater.api.dto.BuildItemOptionRead;
import eu.royalblackwater.api.dto.BuildListMetrics;
import eu.royalblackwater.api.dto.BuildOptionsCatalog;
import eu.royalblackwater.api.dto.BuildPage;
import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildStatDefinitionRead;
import eu.royalblackwater.api.dto.BuildSummaryRead;
import eu.royalblackwater.api.dto.InventorySlot;
import eu.royalblackwater.api.dto.ShipStats;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class BuildAssembler {
    private final BuildCatalogRepository catalog;
    private final BuildStatsService stats;

    public BuildAssembler(BuildCatalogRepository catalog, BuildStatsService stats) {
        this.catalog = catalog;
        this.stats = stats;
    }

    public BuildPage page(BuildPageResult result) {
        RuntimeCache cache = new RuntimeCache();
        return new BuildPage(result.items().stream().map(item -> summary(item, cache)).toList(),
                result.limit(), result.offset(), result.total());
    }

    public BuildRead detail(BuildAggregate aggregate) {
        return detail(aggregate, new RuntimeCache());
    }

    public List<BuildRead> details(List<BuildAggregate> aggregates) {
        RuntimeCache cache = new RuntimeCache();
        return aggregates.stream().map(value -> detail(value, cache)).toList();
    }

    private BuildRead detail(BuildAggregate aggregate, RuntimeCache cache) {
        BuildRuntime runtime = runtime(aggregate, cache);
        Map<String, Object> row = aggregate.row();
        ShipStats shipStats = stats.calculate(runtime.payload(), runtime.ship(), runtime.feature(), runtime.selections());
        String printoutCacheKey = RowValues.string(row, "printout_cache_key");
        String printoutChecksum = RowValues.string(row, "printout_checksum");
        java.time.LocalDateTime printoutSourceUpdatedAt = RowValues.nullableDateTime(row, "printout_source_updated_at");
        java.time.LocalDateTime buildUpdatedAt = RowValues.dateTime(row, "updated_at");
        boolean currentPrintout = printoutCacheKey != null && printoutChecksum != null
                && printoutSourceUpdatedAt != null && printoutSourceUpdatedAt.equals(buildUpdatedAt);
        return new BuildRead(
                slots(aggregate, "ammunition"), RowValues.requiredString(row, "build_name"),
                RowValues.requiredString(row, "build_role_label"), RowValues.requiredString(row, "build_type"),
                aggregate.classifications(), slots(aggregate, "consumable"), RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "details"), slots(aggregate, "weapon_front"), bool(row, "has_upvoted"),
                slots(aggregate, "hold"), RowValues.longValue(row, "id"), bool(row, "is_official_template"),
                single(aggregate, "lantern"), longValue(row, "mercenaries"), bool(row, "mortar_modification_installed"),
                slots(aggregate, "weapon_mortar"), longValue(row, "musketeers"), RowValues.nullableLong(row, "owner_id"),
                slots(aggregate, "weapon_port"), currentPrintout ? printoutCacheKey : null,
                currentPrintout ? printoutChecksum : null,
                currentPrintout ? printoutUrl(RowValues.longValue(row, "id"), printoutCacheKey) : null,
                currentPrintout ? printoutSourceUpdatedAt : null,
                slots(aggregate, "weapon_rear"), row.get("research_upgrade_feature_id") != null,
                longValue(row, "sailors"), single(aggregate, "sail"), runtime.ship().read(),
                RowValues.longValue(row, "ship_id"), shipStats, longValue(row, "soldiers"),
                slots(aggregate, "special_crew"), slots(aggregate, "weapon_special"),
                slots(aggregate, "weapon_starboard"), buildUpdatedAt,
                upgrade(aggregate, 1), upgrade(aggregate, 2), upgrade(aggregate, 3), upgrade(aggregate, 4),
                upgrade(aggregate, 5), upgrade(aggregate, 6), upgrade(aggregate, 7), upgrade(aggregate, 8),
                longValue(row, "upvote_count"));
    }

    public BuildSummaryRead summary(BuildAggregate aggregate) {
        return summary(aggregate, new RuntimeCache());
    }

    private BuildSummaryRead summary(BuildAggregate aggregate, RuntimeCache cache) {
        BuildRuntime runtime = runtime(aggregate, cache);
        Map<String, Object> row = aggregate.row();
        UpgradeSlotAccess access = runtime.access();
        BuildListMetrics metrics = new BuildListMetrics(
                countRows(aggregate, "ammunition"), countRows(aggregate, "consumable"),
                (long) runtime.ship().crewCapacity(), crewTotal(row), countRows(aggregate, "hold"),
                countRows(aggregate, "special_crew"), (long) access.availableSlots(),
                countRows(aggregate, "upgrade"), weaponTotal(aggregate));
        return new BuildSummaryRead(slots(aggregate, "ammunition"), RowValues.requiredString(row, "build_name"),
                RowValues.requiredString(row, "build_role_label"), RowValues.requiredString(row, "build_type"),
                aggregate.classifications(), RowValues.dateTime(row, "created_at"), bool(row, "has_upvoted"),
                slots(aggregate, "hold"), RowValues.longValue(row, "id"), bool(row, "is_official_template"),
                metrics, RowValues.nullableLong(row, "owner_id"), runtime.ship().read(), RowValues.dateTime(row, "updated_at"),
                longValue(row, "upvote_count"));
    }

    public BuildOptionsCatalog options(Long shipId) {
        List<Map<String, Object>> categories = catalog.categories();
        List<BuildCatalogOption> values = catalog.options(shipId);
        Map<String, List<BuildItemOptionRead>> grouped = new LinkedHashMap<>();
        for (Map<String, Object> category : categories) {
            grouped.put(RowValues.requiredString(category, "key"), new ArrayList<>());
        }
        for (BuildCatalogOption option : values) {
            grouped.computeIfAbsent(option.category(), ignored -> new ArrayList<>()).add(option(option));
        }
        Map<String, List<BuildItemOptionRead>> immutable = new LinkedHashMap<>();
        grouped.forEach((key, value) -> immutable.put(key, List.copyOf(value)));
        BuildFeatureSnapshot research = catalog.researchFeature().orElse(null);
        return new BuildOptionsCatalog(roles(), categories.stream().map(BuildAssembler::category).toList(),
                Map.of("classification_limit", 6L, "consumable_slots", 3L, "special_crew_slots", 5L,
                        "upgrade_slots", 8L, "weapon_rows", 12L),
                Map.copyOf(immutable), research == null ? Map.of() : research.effects(),
                research == null ? 0L : (long) research.grantedSlots(), statDefinitions());
    }

    public List<BuildRoleRead> roles() {
        return catalog.roles().stream().map(row -> new BuildRoleRead(RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "description"), RowValues.requiredString(row, "label"),
                RowValues.requiredString(row, "slug"), RowValues.longValue(row, "sort_order"),
                RowValues.dateTime(row, "updated_at"))).toList();
    }

    private BuildRuntime runtime(BuildAggregate aggregate, RuntimeCache cache) {
        Map<String, Object> row = aggregate.row();
        long shipId = RowValues.longValue(row, "ship_id");
        BuildShipSnapshot ship = cache.ships.computeIfAbsent(shipId, id -> catalog.ship(id)
                .orElseThrow(() -> new IllegalStateException("Build references an inactive or missing ship.")));
        Long featureId = RowValues.nullableLong(row, "research_upgrade_feature_id");
        BuildFeatureSnapshot feature = featureId == null ? null : cache.features.computeIfAbsent(
                featureId, id -> catalog.feature(id).orElse(null));
        Map<Long, BuildCatalogOption> byId = cache.options.computeIfAbsent(shipId, ignored -> {
            Map<Long, BuildCatalogOption> loaded = new LinkedHashMap<>();
            for (BuildCatalogOption option : catalog.options(shipId)) loaded.put(option.id(), option);
            return Map.copyOf(loaded);
        });
        List<BuildSlotSelection> selections = aggregate.slots().stream().map(slot -> {
            BuildCatalogOption option = byId.get(slot.optionId());
            if (option == null) throw new IllegalStateException("Build references a missing option: " + slot.optionId());
            return new BuildSlotSelection(slot.type(), slot.index(), slot.optionId(), slot.optionName(), slot.quantity(), option);
        }).toList();
        BuildPayload payload = storedPayload(aggregate);
        UpgradeSlotAccess access = new UpgradeSlotService().calculate(ship, feature, selections);
        return new BuildRuntime(payload, ship, feature, selections, access);
    }

    private static BuildPayload storedPayload(BuildAggregate aggregate) {
        Map<String, Object> row = aggregate.row();
        List<String> upgrades = new ArrayList<>(8);
        for (int index = 1; index <= 8; index++) upgrades.add(upgrade(aggregate, index));
        return new BuildPayload(RowValues.requiredString(row, "build_name"), RowValues.requiredString(row, "build_type"),
                RowValues.longValue(row, "ship_id"), aggregate.classifications(), single(aggregate, "sail"),
                Collections.unmodifiableList(upgrades), single(aggregate, "lantern"),
                row.get("research_upgrade_feature_id") != null,
                bool(row, "mortar_modification_installed"), longValue(row, "sailors"), longValue(row, "soldiers"),
                longValue(row, "musketeers"), longValue(row, "mercenaries"), slots(aggregate, "weapon_front"),
                slots(aggregate, "weapon_rear"), slots(aggregate, "weapon_port"), slots(aggregate, "weapon_starboard"),
                slots(aggregate, "weapon_mortar"), slots(aggregate, "weapon_special"), slots(aggregate, "special_crew"),
                slots(aggregate, "ammunition"), slots(aggregate, "consumable"), slots(aggregate, "hold"),
                RowValues.string(row, "details"));
    }

    private static BuildItemCategoryRead category(Map<String, Object> row) {
        return new BuildItemCategoryRead(RowValues.longValue(row, "id"), RowValues.requiredString(row, "key"),
                RowValues.requiredString(row, "label"), RowValues.longValue(row, "sort_order"));
    }

    private static BuildItemOptionRead option(BuildCatalogOption option) {
        return new BuildItemOptionRead(option.allowedSlots(), option.baseEffects(), option.category(), option.createdAt(),
                option.id(), option.imageUrl(), option.shipSpecific(), option.name(), option.notes(), option.kind(),
                (long) option.sortOrder(), option.source(), option.effects(), option.updatedAt(), option.caliber(),
                option.weaponClass(), option.performance());
    }

    private static List<BuildStatDefinitionRead> statDefinitions() {
        return BuildStatCatalog.ALL.stream().map(value -> new BuildStatDefinitionRead(value.baseField(),
                value.calculationFlatEffect(), value.category(), value.flatEffect(), value.key(), value.label(),
                value.pctBaseField(), value.pctEffect(), value.positiveIsGood(), (long) value.precision(),
                value.source(), value.unit())).toList();
    }

    private static List<InventorySlot> slots(BuildAggregate aggregate, String type) {
        return aggregate.slots().stream().filter(slot -> slot.type().equals(type))
                .sorted(java.util.Comparator.comparingInt(BuildStoredSlot::index))
                .map(slot -> new InventorySlot(slot.optionName(), (long) slot.quantity())).toList();
    }

    private static String single(BuildAggregate aggregate, String type) {
        return aggregate.slots().stream().filter(slot -> slot.type().equals(type)).findFirst()
                .map(BuildStoredSlot::optionName).orElse(null);
    }

    private static String upgrade(BuildAggregate aggregate, int index) {
        return aggregate.slots().stream().filter(slot -> slot.type().equals("upgrade") && slot.index() == index)
                .findFirst().map(BuildStoredSlot::optionName).orElse(null);
    }

    private static long countRows(BuildAggregate aggregate, String type) {
        return aggregate.slots().stream().filter(slot -> slot.type().equals(type)).count();
    }

    private static long weaponTotal(BuildAggregate aggregate) {
        return aggregate.slots().stream().filter(slot -> slot.type().startsWith("weapon_"))
                .mapToLong(BuildStoredSlot::quantity).sum();
    }

    private static long crewTotal(Map<String, Object> row) {
        return Arrays.stream(new String[]{"sailors", "soldiers", "musketeers", "mercenaries"})
                .mapToLong(key -> longValue(row, key)).sum();
    }

    private static long longValue(Map<String, Object> row, String key) {
        Object value = row.get(key); return value instanceof Number number ? number.longValue() : 0L;
    }

    private static boolean bool(Map<String, Object> row, String key) {
        return Boolean.TRUE.equals(row.get(key));
    }

    private static String printoutUrl(long id, String cacheKey) {
        return "/api/builds/" + id + "/printout?cache_key="
                + java.net.URLEncoder.encode(cacheKey, java.nio.charset.StandardCharsets.UTF_8);
    }

    private record BuildRuntime(BuildPayload payload, BuildShipSnapshot ship, BuildFeatureSnapshot feature,
                                List<BuildSlotSelection> selections, UpgradeSlotAccess access) { }

    private static final class RuntimeCache {
        private final Map<Long, BuildShipSnapshot> ships = new LinkedHashMap<>();
        private final Map<Long, BuildFeatureSnapshot> features = new LinkedHashMap<>();
        private final Map<Long, Map<Long, BuildCatalogOption>> options = new LinkedHashMap<>();
    }
}
