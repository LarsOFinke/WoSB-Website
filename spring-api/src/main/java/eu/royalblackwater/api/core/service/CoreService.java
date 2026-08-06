package eu.royalblackwater.api.core.service;

import eu.royalblackwater.api.core.mapper.CoreDtoMapper;
import eu.royalblackwater.api.core.repository.CoreRepository;
import eu.royalblackwater.api.dto.HealthStatusRead;
import eu.royalblackwater.api.dto.HomeRead;
import org.flywaydb.core.Flyway;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE;

@Service
public class CoreService {
    private final CoreRepository repository;
    private final Flyway flyway;
    private final CoreDtoMapper mapper;

    public CoreService(CoreRepository repository, Flyway flyway, CoreDtoMapper mapper) {
        this.repository = repository;
        this.flyway = flyway;
        this.mapper = mapper;
    }

    public HealthStatusRead health() {
        return mapper.health("ok");
    }

    public HealthStatusRead readiness() {
        try {
            repository.verifyDatabaseConnection();
            if (flyway.info().pending().length != 0) {
                throw new IllegalStateException("Database migrations are pending.");
            }
            flyway.validate();
            return mapper.health("ready");
        } catch (RuntimeException exception) {
            throw new ResponseStatusException(SERVICE_UNAVAILABLE, "Database is not ready.", exception);
        }
    }

    public HomeRead home() {
        return mapper.home();
    }
}
