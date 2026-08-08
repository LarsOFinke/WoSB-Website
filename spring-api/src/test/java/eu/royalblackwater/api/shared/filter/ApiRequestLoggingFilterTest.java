package eu.royalblackwater.api.shared.filter;

import eu.royalblackwater.api.config.ApiDiagnosticsProperties;
import eu.royalblackwater.api.shared.web.ApiRequestAttributes;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.web.servlet.HandlerMapping;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;

@ExtendWith(OutputCaptureExtension.class)
class ApiRequestLoggingFilterTest {
    @Test
    void correlatesAndLogsApiLifecycleWithoutRawIdentifiers(CapturedOutput output) throws Exception {
        ApiRequestLoggingFilter filter = new ApiRequestLoggingFilter(new ApiDiagnosticsProperties(true));
        MockHttpServletRequest request = new MockHttpServletRequest("PUT", "/api/builds/42");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (ignoredRequest, ignoredResponse) -> {
            request.setAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE, "/api/builds/{build_id}");
            response.setStatus(201);
        });

        String requestId = response.getHeader(ApiRequestAttributes.REQUEST_ID_HEADER);
        assertThat(requestId).isNotBlank();
        assertThatCode(() -> UUID.fromString(requestId)).doesNotThrowAnyException();
        assertThat(output).contains("api_request_start request_id=" + requestId + " method=PUT path=/api/builds/{id}");
        assertThat(output).contains("api_request_complete request_id=" + requestId
                + " method=PUT path=/api/builds/{build_id} status=201 duration_ms=");
        assertThat(output.getOut()).doesNotContain("/api/builds/42");
    }

    @Test
    void keepsCorrelationHeaderButSuppressesSuccessfulTelemetryByDefault(CapturedOutput output) throws Exception {
        ApiRequestLoggingFilter filter = new ApiRequestLoggingFilter(new ApiDiagnosticsProperties(false));
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/health");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (ignoredRequest, ignoredResponse) -> response.setStatus(200));

        assertThat(response.getHeader(ApiRequestAttributes.REQUEST_ID_HEADER)).isNotBlank();
        assertThat(output).doesNotContain("api_request_start", "api_request_complete");
    }
}
