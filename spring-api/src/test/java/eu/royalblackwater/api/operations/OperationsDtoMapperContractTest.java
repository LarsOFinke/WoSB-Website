package eu.royalblackwater.api.operations;

import eu.royalblackwater.api.dto.BackupControlStatus;
import eu.royalblackwater.api.operations.mapper.OperationsDtoMapper;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;

class OperationsDtoMapperContractTest {
    @Test
    void mapsEveryPullControllerStatusFieldProducedByTheHostRunner() {
        BackupControlStatus status = new OperationsDtoMapper(new ObjectMapper()).backupStatus(Map.of(
                "state", "succeeded",
                "operation", "backup",
                "message", "Verified export acknowledged.",
                "progress_percent", 100,
                "age_recipient_configured", true,
                "connection", Map.of(
                        "configured", true,
                        "mode", "recovery-controller-pull",
                        "managedServer", true,
                        "username", "rbf-backup-controller-test",
                        "remoteDirectory", "/exports"),
                "artifacts", List.of(Map.of(
                        "artifactType", "postgresql",
                        "filename", "rbf-postgres.dump",
                        "sizeBytes", 42,
                        "sha256", "a".repeat(64),
                        "remotePath", "/exports/rbf-postgres.dump"))));

        assertThat(status.connection().mode()).isEqualTo("recovery-controller-pull");
        assertThat(status.artifacts()).singleElement()
                .satisfies(artifact -> assertThat(artifact.remotePath()).isEqualTo("/exports/rbf-postgres.dump"));
    }
}
