package eu.royalblackwater.api.shared.web;

import eu.royalblackwater.api.shared.dto.BinaryDownloadDto;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.CacheControl;
import org.springframework.http.ContentDisposition;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ApiControllerSupportTest {
    private final Probe probe = new Probe();

    @Test
    void respondBuildsTypedStatusAndRejectsAccidental204Bodies() {
        ResponseEntity<String> response = probe.respondPublic("created", 201);
        assertThat(response.getStatusCode().value()).isEqualTo(201);
        assertThat(response.getBody()).isEqualTo("created");
        assertThatThrownBy(() -> probe.respondPublic("invalid", 204))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Use noContent");
    }

    @Test
    void noContentProducesBodyless204() {
        ResponseEntity<Void> response = probe.noContentPublic();
        assertThat(response.getStatusCode().value()).isEqualTo(204);
        assertThat(response.getBody()).isNull();
    }

    @Test
    void downloadAppliesSecurityAndOptionalMetadataHeaders() {
        byte[] content = "png".getBytes(StandardCharsets.UTF_8);
        BinaryDownloadDto download = new BinaryDownloadDto(
                new ByteArrayResource(content), MediaType.IMAGE_PNG, content.length,
                ContentDisposition.attachment().filename("build.png").build(),
                CacheControl.noCache(), "\"etag-1\"");

        ResponseEntity<?> response = probe.downloadPublic(download);
        assertThat(response.getStatusCode().value()).isEqualTo(200);
        assertThat(response.getHeaders().getContentType()).isEqualTo(MediaType.IMAGE_PNG);
        assertThat(response.getHeaders().getContentLength()).isEqualTo(content.length);
        assertThat(response.getHeaders().getContentDisposition().getFilename()).isEqualTo("build.png");
        assertThat(response.getHeaders().getCacheControl()).contains("no-cache");
        assertThat(response.getHeaders().getETag()).isEqualTo("\"etag-1\"");
        assertThat(response.getHeaders().getFirst("X-Content-Type-Options")).isEqualTo("nosniff");
    }

    @Test
    void downloadLeavesOptionalHeadersAbsentWhenNotProvided() {
        BinaryDownloadDto download = new BinaryDownloadDto(
                new ByteArrayResource(new byte[0]), MediaType.APPLICATION_OCTET_STREAM, 0, null, null, null);
        ResponseEntity<?> response = probe.downloadPublic(download);
        assertThat(response.getHeaders().getContentDisposition().getFilename()).isNull();
        assertThat(response.getHeaders().getETag()).isNull();
        assertThat(response.getHeaders().getFirst("X-Content-Type-Options")).isEqualTo("nosniff");
    }

    private static final class Probe extends ApiControllerSupport {
        <T> ResponseEntity<T> respondPublic(T value, int status) { return respond(value, status); }
        ResponseEntity<Void> noContentPublic() { return noContent(); }
        ResponseEntity<?> downloadPublic(BinaryDownloadDto value) { return download(value); }
    }
}
