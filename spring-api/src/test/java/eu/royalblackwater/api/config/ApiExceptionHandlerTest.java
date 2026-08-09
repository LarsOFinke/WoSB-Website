package eu.royalblackwater.api.config;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.MultipartException;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;

class ApiExceptionHandlerTest {
    private final ApiExceptionHandler handler = new ApiExceptionHandler();
    private final MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/test/42");

    @Test
    void statusPreservesBoundedDomainReasonAndSuppliesFallback() {
        var rejected = handler.status(new ResponseStatusException(HttpStatus.CONFLICT, "state conflict"), request);
        assertThat(rejected.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(rejected.getBody()).containsEntry("detail", "state conflict");

        var fallback = handler.status(new ResponseStatusException(HttpStatus.BAD_REQUEST), request);
        assertThat(fallback.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(fallback.getBody()).containsEntry("detail", "Request rejected.");
    }

    @Test
    void uploadAndMultipartFailuresReturnSafeClientMessages() {
        var tooLarge = handler.uploadTooLarge(new MaxUploadSizeExceededException(1024), request);
        assertThat(tooLarge.getStatusCode().value()).isEqualTo(413);
        assertThat(tooLarge.getBody()).containsEntry("detail", "Request body is too large.");

        var multipart = handler.multipart(new MultipartException("broken\r\nsecret"), request);
        assertThat(multipart.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(multipart.getBody()).containsEntry("detail", "Multipart request is invalid.");
    }

    @Test
    void unexpectedServerFailureNeverLeaksExceptionDetail() {
        var response = handler.unexpected(new IllegalStateException("database password=secret"), request);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
        assertThat(response.getBody()).containsEntry("detail", "Internal server error.");
        assertThat(response.getBody().toString()).doesNotContain("password", "secret");
    }
}
