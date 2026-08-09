package eu.royalblackwater.api.webhooks.service;

import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class WebhookHttpClientTest {
    @Test
    void sendReturnsBoundedSuccessfulResponse() throws Exception {
        HttpClient transport = mock(HttpClient.class);
        @SuppressWarnings("unchecked")
        HttpResponse<String> response = mock(HttpResponse.class);
        when(response.statusCode()).thenReturn(204);
        when(response.body()).thenReturn("x".repeat(5000));
        when(transport.send(any(), any(HttpResponse.BodyHandler.class))).thenReturn(response);

        WebhookHttpClient.Result result = new WebhookHttpClient(transport)
                .send("https://discord.com/api/webhooks/1/token", "{}");

        assertThat(result.success()).isTrue();
        assertThat(result.status()).isEqualTo(204);
        assertThat(result.body()).hasSize(4096);
        assertThat(result.error()).isNull();
    }

    @Test
    void sendConvertsIoFailuresIntoBoundedFailureResult() throws Exception {
        HttpClient transport = mock(HttpClient.class);
        when(transport.send(any(), any(HttpResponse.BodyHandler.class))).thenThrow(new IOException("secret detail"));

        WebhookHttpClient.Result result = new WebhookHttpClient(transport)
                .send("https://discord.com/api/webhooks/1/token", "{}");

        assertThat(result.success()).isFalse();
        assertThat(result.status()).isNull();
        assertThat(result.error()).isEqualTo("Webhook delivery failed: IOException")
                .doesNotContain("secret detail");
    }
}
