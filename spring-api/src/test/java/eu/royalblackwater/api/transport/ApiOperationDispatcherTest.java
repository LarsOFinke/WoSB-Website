package eu.royalblackwater.api.transport;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;

class ApiOperationDispatcherTest {
    @TestFactory
    Stream<DynamicTest> dispatchesEveryContractOperationWithItsTransportContext() {
        RecordingHandler handler = new RecordingHandler(ApiOperationCatalog.ALL);
        ApiOperationDispatcher dispatcher = initialized(handler);

        return ApiOperationCatalog.ALL.stream().sorted().map(operationId -> DynamicTest.dynamicTest(
                operationId,
                () -> {
                    Map<String, Object> parameters = Map.of("operation", operationId);
                    Object body = new Object();

                    ResponseEntity<?> response = dispatcher.dispatch(
                            operationId, parameters, body, null, 202);

                    assertThat(response.getStatusCode().value()).as("status for %s", operationId).isEqualTo(202);
                    assertThat(response.getBody()).as("body for %s", operationId).isEqualTo(operationId);
                    assertThat(handler.lastCall).as("delegation context for %s", operationId)
                            .isEqualTo(new Call(operationId, parameters, body, null));
                }));
    }

    @Test
    void reportsMissingAndUnknownOperationsTogether() {
        String missing = ApiOperationCatalog.ALL.stream().sorted().findFirst().orElseThrow();
        Set<String> incomplete = new HashSet<>(ApiOperationCatalog.ALL);
        incomplete.remove(missing);
        incomplete.add("unknown_contract_operation");
        ApiOperationDispatcher dispatcher = new ApiOperationDispatcher(
                List.of(new RecordingHandler(Set.copyOf(incomplete))));

        assertThatThrownBy(dispatcher::verifyCoverage)
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("missing=[" + missing + "]")
                .hasMessageContaining("unknown=[unknown_contract_operation]");
    }

    @Test
    void reportsDuplicateOperationAndRejectsDispatchBeforeVerification() {
        String operation = ApiOperationCatalog.ALL.stream().sorted().findFirst().orElseThrow();
        ApiOperationDispatcher duplicate = new ApiOperationDispatcher(List.of(
                new RecordingHandler(ApiOperationCatalog.ALL),
                new RecordingHandler(Set.of(operation))));

        assertThatThrownBy(duplicate::verifyCoverage)
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Duplicate API operation handler: " + operation);

        ApiOperationDispatcher uninitialized = new ApiOperationDispatcher(List.of());
        assertThatThrownBy(() -> uninitialized.dispatch(operation, Map.of(), null, null, 200))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("No API operation handler: " + operation);
    }

    private static ApiOperationDispatcher initialized(ApiOperationHandler handler) {
        ApiOperationDispatcher dispatcher = new ApiOperationDispatcher(List.of(handler));
        dispatcher.verifyCoverage();
        return dispatcher;
    }

    private static final class RecordingHandler implements ApiOperationHandler {
        private final Set<String> operations;
        private Call lastCall;

        private RecordingHandler(Set<String> operations) {
            this.operations = operations;
        }

        @Override
        public Set<String> operations() {
            return operations;
        }

        @Override
        public ResponseEntity<?> handle(
                String operationId,
                Map<String, Object> parameters,
                Object body,
                MultipartFile upload,
                int successStatus) {
            lastCall = new Call(operationId, parameters, body, upload);
            return ResponseEntity.status(successStatus).body(operationId);
        }
    }

    private record Call(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) { }
}
