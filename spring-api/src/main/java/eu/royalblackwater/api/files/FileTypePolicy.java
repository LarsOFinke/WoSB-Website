package eu.royalblackwater.api.files;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.springframework.http.MediaType;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;

final class FileTypePolicy {
    private static final Map<String, Set<String>> ALLOWED = Map.of(
            ".jpg", Set.of("image/jpeg"),
            ".jpeg", Set.of("image/jpeg"),
            ".png", Set.of("image/png"),
            ".gif", Set.of("image/gif"),
            ".webp", Set.of("image/webp"),
            ".mp4", Set.of("video/mp4"),
            ".webm", Set.of("video/webm"),
            ".mov", Set.of("video/quicktime"),
            ".pdf", Set.of("application/pdf"),
            ".txt", Set.of(MediaType.TEXT_PLAIN_VALUE));

    private FileTypePolicy() { }

    static String extension(String filename) {
        String name = filename == null ? "" : filename.toLowerCase(java.util.Locale.ROOT);
        int dot = name.lastIndexOf('.');
        String extension = dot < 0 ? "" : name.substring(dot);
        if (!ALLOWED.containsKey(extension)) throw bad("Unsupported file type.");
        return extension;
    }

    static String validate(Path path, String extension, String declaredType) throws IOException {
        String normalized = declaredType == null ? "" : declaredType.split(";", 2)[0].strip().toLowerCase();
        if (!ALLOWED.getOrDefault(extension, Set.of()).contains(normalized)) {
            throw bad("File extension and declared content type do not match.");
        }
        byte[] content = ".txt".equals(extension) ? Files.readAllBytes(path) : readHeader(path);
        String detected = detect(content, extension);
        if (!ALLOWED.get(extension).contains(detected)) {
            throw bad("File contents do not match the declared extension and content type.");
        }
        return detected;
    }

    private static byte[] readHeader(Path path) throws IOException {
        try (java.io.InputStream input = Files.newInputStream(path)) {
            return input.readNBytes(64);
        }
    }

    private static String detect(byte[] bytes, String extension) {
        if (starts(bytes, 0xff, 0xd8, 0xff)) return "image/jpeg";
        if (starts(bytes, 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)) return "image/png";
        if (ascii(bytes, "GIF87a") || ascii(bytes, "GIF89a")) return "image/gif";
        if (bytes.length >= 12 && ascii(bytes, 0, "RIFF") && ascii(bytes, 8, "WEBP")) return "image/webp";
        if (ascii(bytes, "%PDF-")) return "application/pdf";
        if (starts(bytes, 0x1a, 0x45, 0xdf, 0xa3)) return "video/webm";
        if (bytes.length >= 12 && ascii(bytes, 4, "ftyp")) return ascii(bytes, 8, "qt  ") ? "video/quicktime" : "video/mp4";
        if (".txt".equals(extension) && text(bytes)) return MediaType.TEXT_PLAIN_VALUE;
        return "";
    }

    private static boolean starts(byte[] bytes, int... expected) {
        if (bytes.length < expected.length) return false;
        for (int index = 0; index < expected.length; index++) if ((bytes[index] & 0xff) != expected[index]) return false;
        return true;
    }

    private static boolean ascii(byte[] bytes, String expected) { return ascii(bytes, 0, expected); }
    private static boolean ascii(byte[] bytes, int offset, String expected) {
        byte[] value = expected.getBytes(StandardCharsets.US_ASCII);
        if (bytes.length < offset + value.length) return false;
        for (int index = 0; index < value.length; index++) if (bytes[offset + index] != value[index]) return false;
        return true;
    }

    private static boolean text(byte[] bytes) {
        for (byte value : bytes) if (value == 0) return false;
        try { StandardCharsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)); return true; }
        catch (java.nio.charset.CharacterCodingException ignored) { return false; }
    }

    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
