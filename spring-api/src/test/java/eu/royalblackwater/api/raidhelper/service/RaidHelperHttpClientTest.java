package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.raidhelper.dto.RaidHelperConnectionDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperJsonPayloadDto;
import eu.royalblackwater.api.security.service.FernetSecretBox;
import eu.royalblackwater.api.security.service.SecretBoxException;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class RaidHelperHttpClientTest {
    private final RaidHelperHttpClient client = new RaidHelperHttpClient(
            mock(HttpClient.class), new ObjectMapper(), mock(FernetSecretBox.class),
            new RaidHelperPolicy(new ObjectMapper()));

    @Test
    void rejectsTraversalBeforeCredentialsOrTransportAreTouched() {
        RaidHelperConnectionDto connection = new RaidHelperConnectionDto(
                RaidHelperPolicy.DEFAULT_API_URL, "encrypted", "12345");
        assertThatThrownBy(() -> client.request(connection, "GET", "../events", null))
                .isInstanceOf(RaidHelperHttpClient.RaidHelperTransportException.class)
                .hasMessageContaining("Invalid Raid-Helper request path");
    }

    @Test
    void extractsNestedExternalIdsAndBuildsBoundedFailureMessages() {
        assertThat(client.externalId(Map.of("id", 7))).isEqualTo("7");
        assertThat(client.externalId(Map.of("eventId", 8))).isEqualTo("8");
        assertThat(client.externalId(Map.of("event_id", 42L))).isEqualTo("42");
        assertThat(client.externalId(Map.of("messageId", 9))).isEqualTo("9");
        assertThat(client.externalId(Map.of("message_id", 10))).isEqualTo("10");
        assertThat(client.externalId(Map.of("event", Map.of("event_id", 42L)))).isEqualTo("42");
        assertThat(client.externalId(Map.of("other", "value"))).isNull();
        assertThat(client.externalId("not-a-map")).isNull();

        RaidHelperHttpClient.Response unauthorized = new RaidHelperHttpClient.Response(401,
                Map.of("message", "  invalid   API key  "));
        assertThat(unauthorized.successful()).isFalse();
        assertThat(client.failureMessage(unauthorized))
                .contains("HTTP 401", "invalid API key")
                .doesNotContain("   ");
        assertThat(client.failureMessage(new RaidHelperHttpClient.Response(500, Map.of("error", "boom"))))
                .contains("HTTP 500", "boom");
        assertThat(client.failureMessage(new RaidHelperHttpClient.Response(503, "plain")))
                .isEqualTo("Raid-Helper returned HTTP 503.");
        assertThat(new RaidHelperHttpClient.Response(204, null).successful()).isTrue();
        assertThat(new RaidHelperHttpClient.Response(300, null).successful()).isFalse();
    }

    @Test
    void requestNormalizesBearerQuotesSerializesPayloadAndParsesJson() throws Exception {
        HttpClient transport = mock(HttpClient.class);
        FernetSecretBox secrets = mock(FernetSecretBox.class);
        when(secrets.decrypt("encrypted")).thenReturn(" Bearer \"abcdefgh123\" ");
        @SuppressWarnings("unchecked") HttpResponse<java.io.InputStream> response = mock(HttpResponse.class);
        when(response.statusCode()).thenReturn(201);
        when(response.body()).thenReturn(new ByteArrayInputStream("{\"event_id\":42}".getBytes(StandardCharsets.UTF_8)));
        when(transport.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenReturn(response);
        RaidHelperHttpClient subject = new RaidHelperHttpClient(transport, new ObjectMapper(), secrets,
                new RaidHelperPolicy(new ObjectMapper()));
        RaidHelperConnectionDto connection = new RaidHelperConnectionDto(RaidHelperPolicy.DEFAULT_API_URL, "encrypted", "12345");

        RaidHelperHttpClient.Response result = subject.request(connection, "post", "/events",
                RaidHelperJsonPayloadDto.of(Map.of("title", "Test")));

        assertThat(result.statusCode()).isEqualTo(201);
        assertThat(subject.externalId(result.body())).isEqualTo("42");
    }

    @Test
    void requestHandlesBlankInvalidOversizedIoInterruptedAndSecretFailures() throws Exception {
        RaidHelperConnectionDto connection = new RaidHelperConnectionDto(RaidHelperPolicy.DEFAULT_API_URL, "encrypted", "12345");

        assertThat(requestWithBody("   ").body()).isNull();
        Object invalid = requestWithBody("not-json").body();
        assertThat(invalid).isEqualTo("not-json");
        assertThat(String.valueOf(requestWithBody("x".repeat(1200)).body())).hasSize(1000);

        HttpClient oversizedTransport = mock(HttpClient.class);
        FernetSecretBox oversizedSecrets = mock(FernetSecretBox.class);
        when(oversizedSecrets.decrypt("encrypted")).thenReturn("abcdefgh123");
        @SuppressWarnings("unchecked") HttpResponse<java.io.InputStream> oversizedResponse = mock(HttpResponse.class);
        when(oversizedResponse.statusCode()).thenReturn(200);
        when(oversizedResponse.body()).thenReturn(new ByteArrayInputStream(new byte[1_048_577]));
        when(oversizedTransport.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenReturn(oversizedResponse);
        RaidHelperHttpClient oversized = new RaidHelperHttpClient(oversizedTransport, new ObjectMapper(), oversizedSecrets,
                new RaidHelperPolicy(new ObjectMapper()));
        assertThatThrownBy(() -> oversized.request(connection, "GET", "/events", null))
                .isInstanceOf(RaidHelperHttpClient.RaidHelperTransportException.class)
                .hasMessageContaining("safety limit");

        HttpClient ioTransport = mock(HttpClient.class);
        FernetSecretBox ioSecrets = mock(FernetSecretBox.class);
        when(ioSecrets.decrypt("encrypted")).thenReturn("abcdefgh123");
        when(ioTransport.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenThrow(new IOException("down"));
        RaidHelperHttpClient io = new RaidHelperHttpClient(ioTransport, new ObjectMapper(), ioSecrets,
                new RaidHelperPolicy(new ObjectMapper()));
        assertThatThrownBy(() -> io.request(connection, "GET", "/events", null))
                .isInstanceOf(RaidHelperHttpClient.RaidHelperTransportException.class)
                .hasMessageContaining("connection failed");

        HttpClient interruptedTransport = mock(HttpClient.class);
        FernetSecretBox interruptedSecrets = mock(FernetSecretBox.class);
        when(interruptedSecrets.decrypt("encrypted")).thenReturn("abcdefgh123");
        when(interruptedTransport.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenThrow(new InterruptedException("stop"));
        RaidHelperHttpClient interrupted = new RaidHelperHttpClient(interruptedTransport, new ObjectMapper(), interruptedSecrets,
                new RaidHelperPolicy(new ObjectMapper()));
        try {
            assertThatThrownBy(() -> interrupted.request(connection, "GET", "/events", null))
                    .isInstanceOf(RaidHelperHttpClient.RaidHelperTransportException.class)
                    .hasMessageContaining("interrupted");
            assertThat(Thread.currentThread().isInterrupted()).isTrue();
        } finally {
            Thread.interrupted();
        }

        FernetSecretBox brokenSecrets = mock(FernetSecretBox.class);
        when(brokenSecrets.decrypt("encrypted")).thenThrow(new SecretBoxException("broken"));
        RaidHelperHttpClient broken = new RaidHelperHttpClient(mock(HttpClient.class), new ObjectMapper(), brokenSecrets,
                new RaidHelperPolicy(new ObjectMapper()));
        assertThatThrownBy(() -> broken.request(connection, "GET", "/events", null))
                .isInstanceOf(RaidHelperHttpClient.RaidHelperTransportException.class)
                .hasMessageContaining("could not be decrypted");

        FernetSecretBox malformedSecrets = mock(FernetSecretBox.class);
        when(malformedSecrets.decrypt("encrypted")).thenReturn("  \n ");
        RaidHelperHttpClient malformed = new RaidHelperHttpClient(mock(HttpClient.class), new ObjectMapper(), malformedSecrets,
                new RaidHelperPolicy(new ObjectMapper()));
        assertThatThrownBy(() -> malformed.request(connection, "GET", "/events", null))
                .isInstanceOf(RaidHelperHttpClient.RaidHelperTransportException.class)
                .hasMessageContaining("malformed");
    }

    private static RaidHelperHttpClient.Response requestWithBody(String body) throws Exception {
        HttpClient transport = mock(HttpClient.class);
        FernetSecretBox secrets = mock(FernetSecretBox.class);
        when(secrets.decrypt("encrypted")).thenReturn("abcdefgh123");
        @SuppressWarnings("unchecked") HttpResponse<java.io.InputStream> response = mock(HttpResponse.class);
        when(response.statusCode()).thenReturn(200);
        when(response.body()).thenReturn(new ByteArrayInputStream(body.getBytes(StandardCharsets.UTF_8)));
        when(transport.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenReturn(response);
        RaidHelperHttpClient subject = new RaidHelperHttpClient(transport, new ObjectMapper(), secrets,
                new RaidHelperPolicy(new ObjectMapper()));
        return subject.request(new RaidHelperConnectionDto(RaidHelperPolicy.DEFAULT_API_URL, "encrypted", "12345"),
                "GET", "/events", null);
    }
}
