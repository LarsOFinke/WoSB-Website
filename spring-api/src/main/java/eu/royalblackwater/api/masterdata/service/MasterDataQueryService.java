package eu.royalblackwater.api.masterdata.service;

import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.dto.MasterDataOptionRead;
import eu.royalblackwater.api.dto.MasterDataOverview;
import eu.royalblackwater.api.dto.MasterDataShipRead;
import eu.royalblackwater.api.dto.MasterDataTaxonomyRead;
import eu.royalblackwater.api.masterdata.mapper.MasterDataDtoMapper;
import eu.royalblackwater.api.masterdata.repository.MasterDataRepository;
import eu.royalblackwater.api.masterdata.repository.queries.MasterDataQueryQueries;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class MasterDataQueryService {
    private final MasterDataRepository repository;
    private final MasterDataDtoMapper mapper;

    public MasterDataQueryService(MasterDataRepository repository, MasterDataDtoMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public MasterDataOverview overview() {
        return mapper.overview(
                repository.count(MasterDataQueryQueries.OVERVIEW_SELECT_01, Map.of()),
                repository.count(MasterDataQueryQueries.OVERVIEW_SELECT_02, Map.of()),
                repository.count(MasterDataQueryQueries.OVERVIEW_SELECT_03, Map.of()),
                repository.count(MasterDataQueryQueries.OVERVIEW_SELECT_04, Map.of()),
                repository.count(MasterDataQueryQueries.OVERVIEW_SELECT_05, Map.of()));
    }

    @Transactional(readOnly = true)
    public List<MasterDataCategoryRead> categories() {
        return repository.query(MasterDataQueryQueries.CATEGORIES_SELECT_01, Map.of()).stream()
                .map(mapper::category).toList();
    }

    @Transactional(readOnly = true)
    public List<MasterDataOptionRead> options() {
        List<Map<String, Object>> rows = optionRows(null);
        Map<Long, List<String>> slots = groupedStrings(MasterDataQueryQueries.OPTIONS_SELECT_01, Map.of());
        Map<Long, Map<String, Double>> effects = groupedEffects(
                MasterDataQueryQueries.OPTIONS_SELECT_02, Map.of());
        return rows.stream().map(row -> mapper.option(row, slots, effects)).toList();
    }

    @Transactional(readOnly = true)
    public List<MasterDataShipRead> ships() {
        return assembleShips(repository.query(MasterDataQueryQueries.SHIPS_SELECT_01, Map.of()));
    }

    @Transactional(readOnly = true)
    public MasterDataCategoryRead category(long id) {
        return mapper.category(repository.optional(MasterDataQueryQueries.CATEGORY_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> notFound("Category")));
    }

    @Transactional(readOnly = true)
    public MasterDataOptionRead option(long id) {
        List<Map<String, Object>> rows = optionRows(id);
        if (rows.isEmpty()) {
            throw notFound("Option");
        }
        Map<String, Object> parameters = Map.of("ids", List.of(id));
        Map<Long, List<String>> slots = groupedStrings(MasterDataQueryQueries.OPTION_SELECT_01, parameters);
        Map<Long, Map<String, Double>> effects = groupedEffects(MasterDataQueryQueries.OPTION_SELECT_02, parameters);
        return mapper.option(rows.getFirst(), slots, effects);
    }

    @Transactional(readOnly = true)
    public MasterDataShipRead ship(long id) {
        List<MasterDataShipRead> result = assembleShips(
                repository.query(MasterDataQueryQueries.SHIP_SELECT_01, Map.of("id", id)));
        if (result.isEmpty()) {
            throw notFound("Ship");
        }
        return result.getFirst();
    }

    @Transactional(readOnly = true)
    public MasterDataTaxonomyRead taxonomy() {
        return mapper.taxonomy(
                repository.query(MasterDataQueryQueries.TAXONOMY_SELECT_01, Map.of()),
                repository.query(MasterDataQueryQueries.TAXONOMY_SELECT_02, Map.of()),
                repository.query(MasterDataQueryQueries.TAXONOMY_SELECT_03, Map.of()));
    }

    private List<Map<String, Object>> optionRows(Long id) {
        String predicate = id == null ? "" : MasterDataQueryQueries.OPTION_ROWS_WHERE_01;
        return repository.query(MasterDataQueryQueries.OPTION_ROWS_SELECT_01 + predicate + MasterDataQueryQueries.OPTION_ROWS_ORDER_BY_01,
                id == null ? Map.of() : Map.of("id", id));
    }

    private List<MasterDataShipRead> assembleShips(List<Map<String, Object>> rows) {
        if (rows.isEmpty()) {
            return List.of();
        }
        List<Long> ids = rows.stream().map(row -> longValue(row, "id")).toList();
        Map<String, Object> parameters = Map.of("ids", ids);
        Map<Long, List<Map<String, Object>>> mounts = groupedRows(MasterDataQueryQueries.ASSEMBLE_SHIPS_SELECT_01, parameters, "ship_id");
        Map<Long, Map<String, Object>> mortars = indexedRows(
                MasterDataQueryQueries.ASSEMBLE_SHIPS_SELECT_02, parameters, "ship_id");
        Map<Long, Map<String, Double>> baseEffects = groupedEffects(
                MasterDataQueryQueries.OPTIONS_SELECT_02, Map.of());
        Map<Long, List<Map<String, Object>>> overrides = groupedRows(MasterDataQueryQueries.ASSEMBLE_SHIPS_SELECT_03, parameters, "ship_id");
        return rows.stream().map(row -> mapper.ship(row,
                mounts.getOrDefault(longValue(row, "id"), List.of()),
                mortars.get(longValue(row, "id")),
                overrides.getOrDefault(longValue(row, "id"), List.of()),
                baseEffects)).toList();
    }

    private Map<Long, List<String>> groupedStrings(String sql, Map<String, ?> parameters) {
        Map<Long, List<String>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(sql, parameters)) {
            result.computeIfAbsent(longValue(row, "option_id"), ignored -> new ArrayList<>())
                    .add(requiredString(row, "code"));
        }
        return result;
    }

    private Map<Long, Map<String, Double>> groupedEffects(String sql, Map<String, ?> parameters) {
        Map<Long, Map<String, Double>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(sql, parameters)) {
            result.computeIfAbsent(longValue(row, "option_id"), ignored -> new LinkedHashMap<>())
                    .put(requiredString(row, "effect_key"), ((Number) row.get("effect_value")).doubleValue());
        }
        return result;
    }

    private Map<Long, List<Map<String, Object>>> groupedRows(String sql, Map<String, ?> parameters, String key) {
        Map<Long, List<Map<String, Object>>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(sql, parameters)) {
            result.computeIfAbsent(longValue(row, key), ignored -> new ArrayList<>()).add(row);
        }
        return result;
    }

    private Map<Long, Map<String, Object>> indexedRows(String sql, Map<String, ?> parameters, String key) {
        Map<Long, Map<String, Object>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(sql, parameters)) {
            result.put(longValue(row, key), row);
        }
        return result;
    }

    private static ResponseStatusException notFound(String subject) {
        return new ResponseStatusException(NOT_FOUND, subject + " not found.");
    }
}
