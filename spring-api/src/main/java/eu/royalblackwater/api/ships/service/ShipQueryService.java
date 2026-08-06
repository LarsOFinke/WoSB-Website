package eu.royalblackwater.api.ships.service;

import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.ships.filter.ShipListFilter;
import eu.royalblackwater.api.ships.mapper.ShipMapper;
import eu.royalblackwater.api.ships.repository.ShipRepository;
import eu.royalblackwater.api.ships.repository.queries.ShipQueryQueries;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ShipQueryService {
    private final ShipRepository repository;
    private final ShipMapper mapper;

    public ShipQueryService(ShipRepository repository, ShipMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public List<ShipRead> activeShips(ShipListFilter filter) {
        StringBuilder sql = new StringBuilder(ShipRepository.SHIP_QUERY).append(ShipQueryQueries.ACTIVE_SHIPS_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (filter.page().search() != null) {
            sql.append(ShipQueryQueries.ACTIVE_SHIPS_AND_01);
            parameters.put("search", "%" + filter.page().search().toLowerCase(Locale.ROOT) + "%");
        }
        if (filter.rate() != null) {
            sql.append(ShipQueryQueries.ACTIVE_SHIPS_AND_02);
            parameters.put("rate", filter.rate());
        }
        if (filter.shipType() != null) {
            sql.append(ShipQueryQueries.ACTIVE_SHIPS_AND_03);
            parameters.put("shipType", filter.shipType().toLowerCase(Locale.ROOT));
        }
        sql.append(ShipQueryQueries.ACTIVE_SHIPS_ORDER_BY_01);
        parameters.put("limit", filter.page().limit());
        parameters.put("offset", filter.page().offset());
        return repository.query(sql.toString(), parameters).stream().map(mapper::toRead).toList();
    }

    @Transactional(readOnly = true)
    public ShipRead activeShip(long shipId) {
        return repository.findActive(shipId).map(mapper::toRead).orElse(null);
    }
}
