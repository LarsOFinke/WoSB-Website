package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.UserRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class UserDirectoryService {
    private static final String USER_SELECT = """
            select u.id,u.username,u.is_active,u.is_bootstrap_admin,u.created_at,
                   sr.code role,up.display_name,up.external_fleet_name,up.preferred_focus,
                   up.availability,up.timezone,up.discord_handle,up.note,
                   fm.fleet_id,fm.fleet_name,fm.membership_id,fm.membership_status,fm.membership_role
            from users u join site_roles sr on sr.id=u.site_role_id
            left join user_profiles up on up.user_id=u.id
            left join lateral (
                select f.id fleet_id,f.name fleet_name,m.id membership_id,m.status membership_status,
                       fr.code membership_role
                from fleet_memberships m join fleets f on f.id=m.fleet_id
                join fleet_roles fr on fr.id=m.fleet_role_id
                where m.user_id=u.id and m.status in ('active','pending')
                order by case when m.status='active' then 0 else 1 end,fr.rank desc,m.id asc limit 1
            ) fm on true
            """;
    private final JdbcQueryService jdbc;

    public UserDirectoryService(JdbcQueryService jdbc) {
        this.jdbc = jdbc;
    }

    @Transactional(readOnly = true)
    public List<UserRead> list(UserAdministrationFilter filter) {
        StringBuilder sql = new StringBuilder(USER_SELECT).append(" where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (filter.page().search() != null) {
            sql.append(" and (lower(u.username) like :search or lower(coalesce(up.display_name,'')) like :search")
                    .append(" or lower(coalesce(fm.fleet_name,'')) like :search)");
            parameters.put("search", "%" + filter.page().search().toLowerCase(Locale.ROOT) + "%");
        }
        if (filter.role() != null) {
            sql.append(" and sr.code=:role");
            parameters.put("role", filter.role());
        }
        if ("active".equals(filter.status())) sql.append(" and u.is_active=true");
        else if ("inactive".equals(filter.status())) sql.append(" and u.is_active=false");
        if (filter.fleetId() != null) {
            sql.append(" and fm.fleet_id=:fleetId");
            parameters.put("fleetId", filter.fleetId());
        }
        sql.append(" order by u.created_at desc,u.id desc limit :limit offset :offset");
        parameters.put("limit", filter.page().limit());
        parameters.put("offset", filter.page().offset());
        return mapRows(jdbc.query(sql.toString(), parameters));
    }

    @Transactional(readOnly = true)
    public UserRead read(long userId) {
        Map<String, Object> row = jdbc.optional(USER_SELECT + " where u.id=:id", Map.of("id", userId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "User not found."));
        return mapRows(List.of(row)).getFirst();
    }

    @Transactional(readOnly = true)
    public UserRead readOrNull(Long userId) {
        if (userId == null) return null;
        return jdbc.optional(USER_SELECT + " where u.id=:id", Map.of("id", userId))
                .map(row -> mapRows(List.of(row)).getFirst()).orElse(null);
    }

    @Transactional(readOnly = true)
    public Map<Long, UserRead> readMany(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) return Map.of();
        List<Map<String, Object>> rows = jdbc.query(USER_SELECT + " where u.id in (:ids)", Map.of("ids", userIds));
        Map<Long, UserRead> result = new LinkedHashMap<>();
        for (UserRead user : mapRows(rows)) result.put(user.id(), user);
        return result;
    }

    private List<UserRead> mapRows(List<Map<String, Object>> rows) {
        if (rows.isEmpty()) return List.of();
        List<Long> ids = rows.stream().map(row -> RowValues.longValue(row, "id")).toList();
        Map<Long, List<Long>> ships = preferences("user_profile_ship_preferences", "ship_id", ids);
        Map<Long, List<Long>> roles = preferences("user_profile_role_preferences", "fleet_role_id", ids);
        return rows.stream().map(row -> read(row,
                ships.getOrDefault(RowValues.longValue(row, "id"), List.of()),
                roles.getOrDefault(RowValues.longValue(row, "id"), List.of()))).toList();
    }

    private Map<Long, List<Long>> preferences(String table, String valueColumn, List<Long> userIds) {
        Map<Long, List<Long>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : jdbc.query(
                "select user_id," + valueColumn + " value from " + table
                        + " where user_id in (:ids) order by user_id,sort_order,id",
                Map.of("ids", userIds))) {
            result.computeIfAbsent(RowValues.longValue(row, "user_id"), ignored -> new ArrayList<>())
                    .add(RowValues.longValue(row, "value"));
        }
        return result;
    }

    private static UserRead read(Map<String, Object> row, List<Long> ships, List<Long> roles) {
        String role = RowValues.requiredString(row, "role");
        boolean bootstrap = RowValues.booleanValue(row, "is_bootstrap_admin");
        String displayName = RowValues.string(row, "display_name");
        if (displayName == null || displayName.isBlank()) displayName = RowValues.requiredString(row, "username");
        String fleetName = RowValues.string(row, "fleet_name");
        if (fleetName == null) fleetName = RowValues.string(row, "external_fleet_name");
        return new UserRead(RowValues.string(row,"availability"), bootstrap && "admin".equals(role),
                RowValues.dateTime(row,"created_at"),RowValues.string(row,"discord_handle"),displayName,
                RowValues.nullableLong(row,"fleet_id"),RowValues.nullableLong(row,"membership_id"),
                RowValues.string(row,"membership_role"),RowValues.string(row,"membership_status"),fleetName,
                RowValues.longValue(row,"id"),RowValues.booleanValue(row,"is_active"),bootstrap,
                RowValues.string(row,"note"),RowValues.string(row,"preferred_focus"),roles,ships,role,
                RowValues.string(row,"timezone"),RowValues.requiredString(row,"username"));
    }
}
