package eu.royalblackwater.api.warehouse.service;

import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class WarehouseResourceService {
    private final WarehouseRepository repository;

    public WarehouseResourceService(WarehouseRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<String> active(AuthenticatedUser actor) {
        if (actor == null) {
            throw new ResponseStatusException(FORBIDDEN, "Warehouse access requires authentication.");
        }
        return repository.query(WarehouseQueries.ACTIVE_RESOURCES_SELECT_01, Map.of()).stream()
                .map(row -> RowValues.requiredString(row, "name"))
                .toList();
    }

    @Transactional(readOnly = true)
    public String requireActiveName(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new ResponseStatusException(BAD_REQUEST, "Resource is required.");
        }
        String requested = raw.strip();
        return repository.optional(WarehouseQueries.ACTIVE_RESOURCE_BY_NAME_SELECT_01, Map.of("name", requested))
                .map(row -> RowValues.requiredString(row, "name"))
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST,
                        "Select an active warehouse resource."));
    }
}
