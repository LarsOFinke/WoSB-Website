package eu.royalblackwater.api.transport;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

class AbstractApiOperationHandlerTest {
    @Test
    void appliesGeneratedSuccessStatusAndNoContentSemantics() {
        StubHandler handler = new StubHandler("result");

        assertThat(handler.handle("operation", Map.of(), null, null, 201))
                .satisfies(response -> {
                    assertThat(response.getStatusCode().value()).isEqualTo(201);
                    assertThat(response.getBody()).isEqualTo("result");
                });
        assertThat(handler.handle("operation", Map.of(), null, null, 204))
                .satisfies(response -> {
                    assertThat(response.getStatusCode().value()).isEqualTo(204);
                    assertThat(response.getBody()).isNull();
                });
    }

    @Test
    void preservesExplicitResponsesFromDomainHandlers() {
        ResponseEntity<String> explicit = ResponseEntity.accepted().body("queued");

        assertThat(new StubHandler(explicit).handle("operation", Map.of(), null, null, 200))
                .isSameAs(explicit);
    }

    @Test
    void rejectsInvalidRequiredParametersAndBodiesAsClientErrors() {
        assertThatThrownBy(() -> TestParameters.longValue(Map.of(), "fleet_id"))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value())
                        .isEqualTo(400))
                .hasMessageContaining("fleet_id");
        assertThatThrownBy(() -> TestParameters.bodyValue(Map.of(), String.class))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value())
                        .isEqualTo(400));
    }

    @Test
    void omitsNullTransportParametersAndReturnsAnImmutableMap() {
        Map<String, Object> parameters = ApiParameters.of("search", null, "limit", 100L);

        assertThat(parameters).containsExactlyEntriesOf(Map.of("limit", 100L));
        assertThatThrownBy(() -> parameters.put("offset", 1L))
                .isInstanceOf(UnsupportedOperationException.class);
        assertThatThrownBy(() -> ApiParameters.of("unpaired"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("name/value pairs");
    }

    private static final class StubHandler extends AbstractApiOperationHandler {
        private final Object result;

        private StubHandler(Object result) {
            this.result = result;
        }

        @Override
        public Set<String> operations() {
            return Set.of("operation");
        }

        @Override
        protected Object execute(
                String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
            return result;
        }
    }

    private static final class TestParameters extends AbstractApiOperationHandler {
        static long longValue(Map<String, Object> parameters, String name) {
            return longParameter(parameters, name);
        }

        static <T> T bodyValue(Object body, Class<T> type) {
            return body(body, type);
        }

        @Override
        public Set<String> operations() {
            return Set.of();
        }

        @Override
        protected Object execute(
                String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
            throw new UnsupportedOperationException();
        }
    }
}
