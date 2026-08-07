package eu.royalblackwater.api.operations.mapper;

import eu.royalblackwater.api.dto.BackupControlRequestResult;
import eu.royalblackwater.api.dto.BackupControlStatus;
import eu.royalblackwater.api.dto.SystemUpdateRequestResult;
import eu.royalblackwater.api.dto.SystemUpdateStatus;
import java.util.Map;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

@Component
public class OperationsDtoMapper {
    private final ObjectMapper json;

    public OperationsDtoMapper(ObjectMapper json) {
        this.json = json;
    }

    public BackupControlStatus backupStatus(Map<String, Object> values) {
        return json.convertValue(values, BackupControlStatus.class);
    }

    public BackupControlRequestResult backupRequest(boolean accepted, BackupControlStatus status) {
        return new BackupControlRequestResult(accepted, status);
    }

    public SystemUpdateStatus systemUpdateStatus(String finishedAt, String message, String operation,
            boolean requestAvailable, String requestedAt, String startedAt, String state) {
        return new SystemUpdateStatus(finishedAt, message, operation, requestAvailable,
                requestedAt, startedAt, state);
    }

    public SystemUpdateRequestResult systemUpdateRequest(boolean accepted, SystemUpdateStatus status) {
        return new SystemUpdateRequestResult(accepted, status);
    }
}
