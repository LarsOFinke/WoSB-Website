package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.filter.UserAdministrationFilter;
import eu.royalblackwater.api.account.mapper.AccountDtoMapper;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.queries.UserDirectoryQueries;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class UserDirectoryService {
    private final AccountDataRepository repository;

    public UserDirectoryService(AccountDataRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<UserRead> list(UserAdministrationFilter filter) {
        StringBuilder sql = new StringBuilder(UserDirectoryQueries.USER_SELECT).append(UserDirectoryQueries.LIST_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (filter.page().search() != null) {
            sql.append(UserDirectoryQueries.LIST_AND_01)
                    .append(UserDirectoryQueries.LIST_OR_01);
            parameters.put("search", "%" + filter.page().search().toLowerCase(Locale.ROOT) + "%");
        }
        if (filter.role() != null) {
            sql.append(UserDirectoryQueries.LIST_AND_02);
            parameters.put("role", filter.role());
        }
        if ("active".equals(filter.status())) sql.append(UserDirectoryQueries.LIST_AND_03);
        else if ("inactive".equals(filter.status())) sql.append(UserDirectoryQueries.LIST_AND_04);
        if (filter.fleetId() != null) {
            sql.append(UserDirectoryQueries.LIST_AND_05);
            parameters.put("fleetId", filter.fleetId());
        }
        sql.append(UserDirectoryQueries.LIST_ORDER_BY_01);
        parameters.put("limit", filter.page().limit());
        parameters.put("offset", filter.page().offset());
        return mapRows(repository.query(sql.toString(), parameters));
    }

    @Transactional(readOnly = true)
    public UserRead read(long userId) {
        Map<String, Object> row = repository.optional(UserDirectoryQueries.USER_SELECT + UserDirectoryQueries.READ_WHERE_01, Map.of("id", userId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "User not found."));
        return mapRows(List.of(row)).getFirst();
    }

    @Transactional(readOnly = true)
    public UserRead readOrNull(Long userId) {
        if (userId == null) return null;
        return repository.optional(UserDirectoryQueries.USER_SELECT + UserDirectoryQueries.READ_WHERE_01, Map.of("id", userId))
                .map(row -> mapRows(List.of(row)).getFirst()).orElse(null);
    }

    @Transactional(readOnly = true)
    public Map<Long, UserRead> readMany(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) return Map.of();
        List<Map<String, Object>> rows = repository.query(UserDirectoryQueries.USER_SELECT + UserDirectoryQueries.READ_MANY_WHERE_01, Map.of("ids", userIds));
        Map<Long, UserRead> result = new LinkedHashMap<>();
        for (UserRead user : mapRows(rows)) result.put(user.id(), user);
        return result;
    }

    private List<UserRead> mapRows(List<Map<String, Object>> rows) {
        if (rows.isEmpty()) return List.of();
        List<Long> ids = rows.stream().map(row -> RowValues.longValue(row, "id")).toList();
        Map<Long, List<Long>> ships = preferences("user_profile_ship_preferences", "ship_id", ids);
        Map<Long, List<Long>> roles = preferences("user_profile_role_preferences", "fleet_role_id", ids);
        return rows.stream().map(row -> AccountDtoMapper.user(row,
                ships.getOrDefault(RowValues.longValue(row, "id"), List.of()),
                roles.getOrDefault(RowValues.longValue(row, "id"), List.of()))).toList();
    }

    private Map<Long, List<Long>> preferences(String table, String valueColumn, List<Long> userIds) {
        Map<Long, List<Long>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(
                UserDirectoryQueries.PREFERENCES_SELECT_01 + valueColumn + " value from " + table
                        + UserDirectoryQueries.PREFERENCES_WHERE_01,
                Map.of("ids", userIds))) {
            result.computeIfAbsent(RowValues.longValue(row, "user_id"), ignored -> new ArrayList<>())
                    .add(RowValues.longValue(row, "value"));
        }
        return result;
    }


}
