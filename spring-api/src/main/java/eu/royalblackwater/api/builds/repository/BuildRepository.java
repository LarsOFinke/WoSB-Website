package eu.royalblackwater.api.builds.repository;

import eu.royalblackwater.api.builds.model.BuildAggregate;
import eu.royalblackwater.api.builds.model.BuildPageResult;
import eu.royalblackwater.api.builds.model.BuildPayload;
import eu.royalblackwater.api.builds.model.BuildPreparedPayload;
import eu.royalblackwater.api.builds.model.BuildSlotSelection;
import eu.royalblackwater.api.builds.model.BuildStoredSlot;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class BuildRepository {
    private static final String SELECT = """
            select b.*, r.label as build_role_label,
                   (select count(*) from build_votes v where v.build_id=b.id) as upvote_count,
                   exists(select 1 from build_votes v where v.build_id=b.id and v.user_id=:viewer_id) as has_upvoted
              from builds b join build_roles r on r.slug=b.build_type
            """;
    private final JdbcQueryService jdbc;
    private final Clock clock;

    public BuildRepository(JdbcQueryService jdbc, Clock clock) {
        this.jdbc = jdbc;
        this.clock = clock;
    }

    public Optional<BuildAggregate> find(long id, Long viewerId) {
        return jdbc.optional(SELECT + " where b.id=:id", SqlParameters.ofNullable("id", id, "viewer_id", viewerId))
                .map(row -> hydrate(List.of(row)).getFirst());
    }

    public List<BuildAggregate> findAll(List<Long> ids, Long viewerId) {
        List<Long> normalized = ids == null ? List.of() : ids.stream()
                .filter(java.util.Objects::nonNull)
                .filter(id -> id > 0)
                .distinct()
                .toList();
        if (normalized.isEmpty()) return List.of();
        List<BuildAggregate> values = hydrate(jdbc.query(SELECT + " where b.id in (:ids)",
                SqlParameters.ofNullable("ids", normalized, "viewer_id", viewerId)));
        Map<Long, BuildAggregate> byId = new LinkedHashMap<>();
        for (BuildAggregate value : values) {
            byId.put(((Number) value.row().get("id")).longValue(), value);
        }
        return normalized.stream().map(byId::get).filter(java.util.Objects::nonNull).toList();
    }

    public BuildPageResult page(String search, String type, String classification, Long ownerId,
                         Long viewerId, long limit, long offset) {
        Filter filter = filter(search, type, classification, ownerId);
        Map<String, Object> parameters = new LinkedHashMap<>(filter.parameters());
        parameters.put("viewer_id", viewerId);
        parameters.put("limit", limit);
        parameters.put("offset", offset);
        List<Map<String, Object>> rows = jdbc.query(SELECT + filter.joinAndWhere() + """
                 order by upvote_count desc, b.created_at desc, b.id desc
                 limit :limit offset :offset
                """, parameters);
        long total = jdbc.count("select count(*) from builds b" + filter.joinAndWhere(), filter.parameters());
        return new BuildPageResult(hydrate(rows), total, limit, offset);
    }

    public long create(BuildPreparedPayload prepared, long ownerId) {
        BuildPayload value = prepared.payload();
        LocalDateTime now = now();
        long id = jdbc.insertReturningId("""
                insert into builds(build_name,build_type,ship_id,owner_id,is_official_template,
                                   research_upgrade_feature_id,mortar_modification_installed,sailors,soldiers,
                                   musketeers,mercenaries,details,created_at,updated_at)
                values(:name,:type,:shipId,:ownerId,false,:featureId,:mortar,:sailors,:soldiers,
                       :musketeers,:mercenaries,:details,:now,:now) returning id
                """, SqlParameters.ofNullable("name", value.name(), "type", value.type(), "shipId", value.shipId(),
                "ownerId", ownerId, "featureId", prepared.researchFeature() == null ? null : prepared.researchFeature().id(),
                "mortar", value.mortarModification(), "sailors", value.sailors(), "soldiers", value.soldiers(),
                "musketeers", value.musketeers(), "mercenaries", value.mercenaries(), "details", value.details(), "now", now));
        replaceChildren(id, prepared, now);
        return id;
    }

    public boolean updateOwned(long id, long ownerId, BuildPreparedPayload prepared) {
        BuildPayload value = prepared.payload();
        int updated = jdbc.update("""
                update builds set build_name=:name,build_type=:type,ship_id=:shipId,
                       research_upgrade_feature_id=:featureId,mortar_modification_installed=:mortar,
                       sailors=:sailors,soldiers=:soldiers,musketeers=:musketeers,mercenaries=:mercenaries,
                       details=:details,updated_at=:now
                 where id=:id and owner_id=:ownerId and is_official_template=false
                """, SqlParameters.ofNullable("name", value.name(), "type", value.type(), "shipId", value.shipId(),
                "featureId", prepared.researchFeature() == null ? null : prepared.researchFeature().id(),
                "mortar", value.mortarModification(), "sailors", value.sailors(), "soldiers", value.soldiers(),
                "musketeers", value.musketeers(), "mercenaries", value.mercenaries(), "details", value.details(),
                "now", now(), "id", id, "ownerId", ownerId));
        if (updated == 0) return false;
        jdbc.update("delete from build_slots where build_id=:id", Map.of("id", id));
        jdbc.update("delete from build_classifications where build_id=:id", Map.of("id", id));
        replaceChildren(id, prepared, now());
        return true;
    }

    public boolean deleteOwned(long id, long ownerId) {
        return jdbc.update("delete from builds where id=:id and owner_id=:ownerId and is_official_template=false",
                Map.of("id", id, "ownerId", ownerId)) > 0;
    }

    public boolean deleteAny(long id) {
        return jdbc.update("delete from builds where id=:id", Map.of("id", id)) > 0;
    }

    public void assignRole(long id, String role) {
        if (jdbc.update("update builds set build_type=:role,updated_at=:now where id=:id",
                Map.of("role", role, "now", now(), "id", id)) == 0) throw new java.util.NoSuchElementException();
    }

    private void replaceChildren(long id, BuildPreparedPayload prepared, LocalDateTime now) {
        for (String classification : prepared.payload().classifications()) {
            jdbc.update("insert into build_classifications(build_id,tag) values(:id,:tag)",
                    Map.of("id", id, "tag", classification));
        }
        for (BuildSlotSelection slot : prepared.slots()) {
            jdbc.update("""
                    insert into build_slots(build_id,slot_type,slot_index,option_id,quantity,created_at,updated_at)
                    values(:id,:type,:index,:optionId,:quantity,:now,:now)
                    """, Map.of("id", id, "type", slot.type(), "index", slot.index(), "optionId", slot.optionId(),
                    "quantity", slot.quantity(), "now", now));
        }
    }

    private List<BuildAggregate> hydrate(List<Map<String, Object>> rows) {
        if (rows.isEmpty()) return List.of();
        List<Long> ids = rows.stream().map(row -> ((Number) row.get("id")).longValue()).toList();
        Map<Long, List<String>> classifications = new HashMap<>();
        for (Map<String, Object> row : jdbc.query("""
                select build_id,tag from build_classifications where build_id in (:ids) order by tag
                """, Map.of("ids", ids))) {
            classifications.computeIfAbsent(((Number) row.get("build_id")).longValue(), ignored -> new ArrayList<>())
                    .add(String.valueOf(row.get("tag")));
        }
        Map<Long, List<BuildStoredSlot>> slots = new HashMap<>();
        for (Map<String, Object> row : jdbc.query("""
                select s.build_id,s.slot_type,s.slot_index,s.option_id,s.quantity,o.name
                  from build_slots s join build_item_options o on o.id=s.option_id
                 where s.build_id in (:ids) order by s.build_id,s.slot_type,s.slot_index
                """, Map.of("ids", ids))) {
            long buildId = ((Number) row.get("build_id")).longValue();
            slots.computeIfAbsent(buildId, ignored -> new ArrayList<>()).add(new BuildStoredSlot(
                    String.valueOf(row.get("slot_type")), ((Number) row.get("slot_index")).intValue(),
                    ((Number) row.get("option_id")).longValue(), String.valueOf(row.get("name")),
                    row.get("quantity") instanceof Number quantity ? quantity.intValue() : 1));
        }
        return rows.stream().map(row -> {
            long id = ((Number) row.get("id")).longValue();
            return new BuildAggregate(java.util.Collections.unmodifiableMap(new LinkedHashMap<>(row)), List.copyOf(classifications.getOrDefault(id, List.of())),
                    List.copyOf(slots.getOrDefault(id, List.of())));
        }).toList();
    }

    private static Filter filter(String search, String type, String classification, Long ownerId) {
        StringBuilder where = new StringBuilder(" where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (search != null && !search.isBlank()) {
            where.append(" and (b.build_name ilike :search or exists(select 1 from ships s where s.id=b.ship_id and s.name ilike :search) or b.build_type ilike :search)");
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (type != null && !type.isBlank()) { where.append(" and b.build_type=:type"); parameters.put("type", type.strip().toLowerCase()); }
        if (classification != null && !classification.isBlank()) {
            where.append(" and exists(select 1 from build_classifications c where c.build_id=b.id and c.tag=:classification)");
            parameters.put("classification", classification.strip().toLowerCase());
        }
        if (ownerId != null) { where.append(" and b.owner_id=:ownerId"); parameters.put("ownerId", ownerId); }
        return new Filter(where.toString(), Map.copyOf(parameters));
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private record Filter(String joinAndWhere, Map<String, Object> parameters) { }
}
