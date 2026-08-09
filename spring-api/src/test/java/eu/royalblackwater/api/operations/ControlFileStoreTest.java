package eu.royalblackwater.api.operations;

import eu.royalblackwater.api.config.OperationsProperties;
import eu.royalblackwater.api.operations.repository.ControlFileStore;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ControlFileStoreTest {
    @TempDir
    Path root;

    @Test
    void publishesReadsAndDetectsAtomicRequestConflicts() throws Exception {
        ControlFileStore store = store();
        Map<String, Object> payload = Map.of("operation", "update", "requested_by", "admin");

        store.publishRequest("update.request", payload);

        assertThat(store.requestExists("update.request")).isTrue();
        assertThat(store.readRequest("update.request")).containsAllEntriesOf(payload);
        assertThat(Files.readString(root.resolve("inbox/update.request"))).contains("\"operation\" : \"update\"");
        assertThatThrownBy(() -> store.publishRequest("update.request", payload))
                .isInstanceOf(ControlFileStore.ControlConflictException.class)
                .hasMessageContaining("already queued");
    }

    @Test
    void missingAndMalformedStatusFilesFailClosedToEmptyState() throws Exception {
        ControlFileStore store = store();
        assertThat(store.readStatus("update-status.json")).isEmpty();

        Path status = root.resolve("status/update-status.json");
        Files.createDirectories(status.getParent());
        Files.writeString(status, "{not-json");
        assertThat(store.readStatus("update-status.json")).isEmpty();
    }

    @Test
    void rejectsControlFileNamesThatCouldEscapeTheManagedNamespaces() {
        ControlFileStore store = store();
        assertThatThrownBy(() -> store.readRequest("../update.request"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Invalid control-file name");
        assertThatThrownBy(() -> store.readStatus("UPPER.json"))
                .isInstanceOf(IllegalArgumentException.class);
    }

    private ControlFileStore store() {
        return new ControlFileStore(new OperationsProperties(root), new ObjectMapper());
    }
}
