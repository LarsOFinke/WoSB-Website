package eu.royalblackwater.api.files.service;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FileTypePolicyTest {
    @TempDir Path root;

    @Test
    void sanitizesPathControlDirectionLongAndFallbackDisplayNames() {
        assertThat(FileTypePolicy.sanitizeOriginalName("../\\..\\report\u202Efdp.pdf", "fallback.pdf"))
                .isEqualTo("reportfdp.pdf");
        assertThat(FileTypePolicy.sanitizeOriginalName(".hidden.txt", "fallback.txt"))
                .isEqualTo("hidden.txt");
        assertThat(FileTypePolicy.sanitizeOriginalName("\u0000\u200F", "fallback.txt"))
                .isEqualTo("fallback.txt");
        assertThat(FileTypePolicy.sanitizeOriginalName(null, "fallback.txt")).isEqualTo("fallback.txt");
        assertThat(FileTypePolicy.sanitizeOriginalName("   ", "fallback.txt")).isEqualTo("fallback.txt");
        assertThat(FileTypePolicy.sanitizeOriginalName("a".repeat(220) + ".txt", "fallback.txt")).hasSize(180);
    }

    @Test
    void extensionAcceptsKnownTypesAndRejectsMissingOrUnknownTypes() {
        assertThat(FileTypePolicy.extension("PHOTO.JPEG")).isEqualTo(".jpeg");
        assertThat(FileTypePolicy.extension("report.pdf")).isEqualTo(".pdf");
        assertThatThrownBy(() -> FileTypePolicy.extension(null)).isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> FileTypePolicy.extension("README")).isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> FileTypePolicy.extension("payload.exe")).isInstanceOf(ResponseStatusException.class);
    }

    @Test
    void validatesAllSupportedSignaturesAndText() throws Exception {
        assertValidated("a.jpg", ".jpg", "image/jpeg", bytes(0xff, 0xd8, 0xff, 0x00), "image/jpeg");
        assertValidated("a.png", ".png", "image/png", bytes(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a), "image/png");
        assertValidated("a.gif", ".gif", "image/gif", "GIF89a...".getBytes(StandardCharsets.US_ASCII), "image/gif");
        assertValidated("a.webp", ".webp", "image/webp", concat("RIFF".getBytes(StandardCharsets.US_ASCII),
                new byte[]{0,0,0,0}, "WEBP".getBytes(StandardCharsets.US_ASCII)), "image/webp");
        assertValidated("a.pdf", ".pdf", "application/pdf", "%PDF-1.7".getBytes(StandardCharsets.US_ASCII), "application/pdf");
        assertValidated("a.webm", ".webm", "video/webm", bytes(0x1a, 0x45, 0xdf, 0xa3, 0), "video/webm");
        assertValidated("a.mp4", ".mp4", "video/mp4", concat(new byte[]{0,0,0,0}, "ftypisom".getBytes(StandardCharsets.US_ASCII)), "video/mp4");
        assertValidated("a.mov", ".mov", "video/quicktime", concat(new byte[]{0,0,0,0}, "ftypqt  ".getBytes(StandardCharsets.US_ASCII)), "video/quicktime");
        assertValidated("a.txt", ".txt", "text/plain; charset=utf-8", "hello äöü".getBytes(StandardCharsets.UTF_8), "text/plain");
    }

    @Test
    void rejectsDeclaredTypeMismatchContentMismatchBinaryTextAndInvalidUtf8() throws Exception {
        Path png = write("wrong.png", bytes(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a));
        assertThatThrownBy(() -> FileTypePolicy.validate(png, ".png", "image/jpeg"))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("declared content type");

        Path fakePng = write("fake.png", "not-png".getBytes(StandardCharsets.UTF_8));
        assertThatThrownBy(() -> FileTypePolicy.validate(fakePng, ".png", "image/png"))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("contents do not match");

        Path zeroText = write("zero.txt", new byte[]{'a', 0, 'b'});
        assertThatThrownBy(() -> FileTypePolicy.validate(zeroText, ".txt", "text/plain"))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("contents do not match");

        Path invalidUtf8 = write("invalid.txt", new byte[]{(byte) 0xc3, (byte) 0x28});
        assertThatThrownBy(() -> FileTypePolicy.validate(invalidUtf8, ".txt", "text/plain"))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("contents do not match");
    }

    private void assertValidated(String name, String extension, String declared, byte[] content, String expected) throws Exception {
        Path path = write(name, content);
        assertThat(FileTypePolicy.validate(path, extension, declared)).isEqualTo(expected);
    }

    private Path write(String name, byte[] content) throws Exception {
        Path path = root.resolve(name);
        Files.write(path, content);
        return path;
    }

    private static byte[] bytes(int... values) {
        byte[] result = new byte[values.length];
        for (int i = 0; i < values.length; i++) result[i] = (byte) values[i];
        return result;
    }

    private static byte[] concat(byte[]... parts) {
        int size = java.util.Arrays.stream(parts).mapToInt(value -> value.length).sum();
        byte[] result = new byte[size];
        int offset = 0;
        for (byte[] part : parts) {
            System.arraycopy(part, 0, result, offset, part.length);
            offset += part.length;
        }
        return result;
    }
}
