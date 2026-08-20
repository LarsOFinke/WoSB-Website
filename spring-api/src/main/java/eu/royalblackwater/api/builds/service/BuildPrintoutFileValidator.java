package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.files.service.ImageAssetOptimizer;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.springframework.http.MediaType;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

final class BuildPrintoutFileValidator {
    private static final byte[] PNG = {(byte) 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a};

    private BuildPrintoutFileValidator() { }

    static Result copyAndValidate(
            MultipartFile upload, Path target, long maximum, ImageAssetOptimizer optimizer) throws IOException {
        byte[] header = new byte[24];
        int headerSize = 0;
        long size = 0;
        try (InputStream input = upload.getInputStream(); OutputStream output = Files.newOutputStream(target,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            byte[] buffer = new byte[1024 * 1024];
            int count;
            while ((count = input.read(buffer)) >= 0) {
                if (count == 0) continue;
                if (headerSize < header.length) {
                    int copy = Math.min(count, header.length - headerSize);
                    System.arraycopy(buffer, 0, header, headerSize, copy);
                    headerSize += copy;
                }
                size += count;
                if (size > maximum) throw bad("Build printout exceeds the configured image/storage limit.");
                output.write(buffer, 0, count);
            }
        }
        validateHeader(header, headerSize);
        optimizer.optimize(target, MediaType.IMAGE_PNG_VALUE);
        long optimizedSize = Files.size(target);
        if (optimizedSize > maximum) throw bad("Optimized build printout exceeds the configured storage limit.");
        MessageDigest digest = sha256();
        try (InputStream input = Files.newInputStream(target)) {
            byte[] buffer = new byte[1024 * 1024];
            int count;
            while ((count = input.read(buffer)) >= 0) {
                if (count > 0) digest.update(buffer, 0, count);
            }
        }
        return new Result(HexFormat.of().formatHex(digest.digest()), optimizedSize);
    }

    private static void validateHeader(byte[] header, int size) {
        if (size < 24) throw bad("Build printout content is not a valid PNG image.");
        for (int index = 0; index < PNG.length; index++) {
            if (header[index] != PNG[index]) throw bad("Build printout content is not a valid PNG image.");
        }
        if (header[12] != 'I' || header[13] != 'H' || header[14] != 'D' || header[15] != 'R') {
            throw bad("Build printout content is not a valid PNG image.");
        }
        ByteBuffer values = ByteBuffer.wrap(header, 16, 8).order(ByteOrder.BIG_ENDIAN);
        int width = values.getInt();
        int height = values.getInt();
        if (width < 1 || width > 10_000 || height < 1 || height > 20_000) {
            throw bad("Build printout dimensions are invalid.");
        }
    }

    private static MessageDigest sha256() {
        try {
            return MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }

    record Result(String checksum, long size) { }
}
