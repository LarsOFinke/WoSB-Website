package eu.royalblackwater.api.files.service;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.DataInputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Iterator;
import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.IIOException;
import javax.imageio.ImageReadParam;
import javax.imageio.ImageReader;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageInputStream;
import javax.imageio.stream.ImageOutputStream;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

/** Loss-aware optimization for uploaded still images and derived PNG assets. */
@Service
public class ImageAssetOptimizer {
    static final int MAX_DIMENSION = 4096;
    static final long MAX_DECODE_PIXELS = 24_000_000L;
    static final long MAX_SOURCE_PIXELS = 100_000_000L;
    private static final float JPEG_QUALITY = 0.82f;
    private static final float PNG_COMPRESSION_QUALITY = 0.1f;

    public void optimize(Path source, String mimeType) throws IOException {
        String format = format(mimeType);
        if (format == null) return;
        Path candidate = source.resolveSibling(source.getFileName() + ".optimized");
        try {
            Raster raster = readBounded(source, mimeType);
            BufferedImage oriented = orient(raster.image(), raster.orientation());
            BufferedImage output = scale(oriented);
            boolean resized = output.getWidth() != oriented.getWidth() || output.getHeight() != oriented.getHeight()
                    || raster.subsampling() > 1;
            write(output, candidate, format);
            if (resized || raster.orientation() != 1 || Files.size(candidate) < Files.size(source)) {
                replace(candidate, source);
            }
        } catch (ResponseStatusException | IOException exception) {
            Files.deleteIfExists(candidate);
            throw exception;
        } catch (RuntimeException exception) {
            Files.deleteIfExists(candidate);
            throw bad("Image content could not be optimized safely.");
        } finally {
            Files.deleteIfExists(candidate);
        }
    }

    private static Raster readBounded(Path source, String mimeType) throws IOException {
        try (ImageInputStream input = ImageIO.createImageInputStream(source.toFile())) {
            if (input == null) throw bad("Image content could not be decoded.");
            Iterator<ImageReader> readers = ImageIO.getImageReaders(input);
            if (!readers.hasNext()) throw bad("Image content could not be decoded.");
            ImageReader reader = readers.next();
            try {
                reader.setInput(input, true, true);
                int width;
                int height;
                try {
                    width = reader.getWidth(0);
                    height = reader.getHeight(0);
                } catch (IIOException exception) {
                    throw bad("Image content could not be decoded.");
                }
                long pixels = pixelCount(width, height);
                if (pixels > MAX_SOURCE_PIXELS) throw bad("Image dimensions exceed the safe processing limit.");
                int subsampling = 1;
                while (pixelCount(ceilDiv(width, subsampling), ceilDiv(height, subsampling)) > MAX_DECODE_PIXELS) {
                    subsampling++;
                }
                ImageReadParam parameters = reader.getDefaultReadParam();
                if (subsampling > 1) parameters.setSourceSubsampling(subsampling, subsampling, 0, 0);
                BufferedImage image;
                try {
                    image = reader.read(0, parameters);
                } catch (IIOException exception) {
                    throw bad("Image content could not be decoded.");
                }
                if (image == null) throw bad("Image content could not be decoded.");
                int orientation = "image/jpeg".equals(mimeType) ? exifOrientation(source) : 1;
                return new Raster(image, orientation, subsampling);
            } finally {
                reader.dispose();
            }
        }
    }

    private static BufferedImage orient(BufferedImage source, int orientation) {
        if (orientation < 2 || orientation > 8) return source;
        int width = source.getWidth(); int height = source.getHeight();
        boolean swapsAxes = orientation >= 5;
        BufferedImage target = new BufferedImage(swapsAxes ? height : width, swapsAxes ? width : height,
                source.getColorModel().hasAlpha() ? BufferedImage.TYPE_INT_ARGB : BufferedImage.TYPE_INT_RGB);
        AffineTransform transform = switch (orientation) {
            case 2 -> new AffineTransform(-1, 0, 0, 1, width, 0);
            case 3 -> new AffineTransform(-1, 0, 0, -1, width, height);
            case 4 -> new AffineTransform(1, 0, 0, -1, 0, height);
            case 5 -> new AffineTransform(0, 1, 1, 0, 0, 0);
            case 6 -> new AffineTransform(0, 1, -1, 0, height, 0);
            case 7 -> new AffineTransform(0, -1, -1, 0, height, width);
            case 8 -> new AffineTransform(0, -1, 1, 0, 0, width);
            default -> new AffineTransform();
        };
        Graphics2D graphics = target.createGraphics();
        try { graphics.drawRenderedImage(source, transform); }
        finally { graphics.dispose(); }
        return target;
    }

    private static BufferedImage scale(BufferedImage source) {
        double factor = Math.min(1d, Math.min((double) MAX_DIMENSION / source.getWidth(),
                (double) MAX_DIMENSION / source.getHeight()));
        if (factor >= 1d) return source;
        int width = Math.max(1, (int) Math.round(source.getWidth() * factor));
        int height = Math.max(1, (int) Math.round(source.getHeight() * factor));
        BufferedImage target = new BufferedImage(width, height,
                source.getColorModel().hasAlpha() ? BufferedImage.TYPE_INT_ARGB : BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = target.createGraphics();
        try {
            graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            graphics.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
            graphics.drawImage(source, 0, 0, width, height, null);
        } finally { graphics.dispose(); }
        return target;
    }

    private static void write(BufferedImage source, Path target, String format) throws IOException {
        BufferedImage image = "jpeg".equals(format) ? opaque(source) : source;
        Iterator<ImageWriter> writers = ImageIO.getImageWritersByFormatName(format);
        if (!writers.hasNext()) throw bad("Image output format is unavailable.");
        ImageWriter writer = writers.next();
        try (ImageOutputStream output = ImageIO.createImageOutputStream(target.toFile())) {
            writer.setOutput(output);
            ImageWriteParam parameters = writer.getDefaultWriteParam();
            if (parameters.canWriteCompressed()) {
                parameters.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
                parameters.setCompressionQuality("jpeg".equals(format) ? JPEG_QUALITY : PNG_COMPRESSION_QUALITY);
            }
            writer.write(null, new IIOImage(image, null, null), parameters);
        } finally { writer.dispose(); }
    }

    private static BufferedImage opaque(BufferedImage source) {
        if (!source.getColorModel().hasAlpha() && source.getType() == BufferedImage.TYPE_INT_RGB) return source;
        BufferedImage target = new BufferedImage(source.getWidth(), source.getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = target.createGraphics();
        try { graphics.setColor(Color.WHITE); graphics.fillRect(0, 0, target.getWidth(), target.getHeight()); graphics.drawImage(source, 0, 0, null); }
        finally { graphics.dispose(); }
        return target;
    }

    private static int exifOrientation(Path source) {
        try (DataInputStream input = new DataInputStream(Files.newInputStream(source))) {
            if (input.readUnsignedShort() != 0xffd8) return 1;
            while (true) {
                int markerStart;
                do { markerStart = input.readUnsignedByte(); } while (markerStart != 0xff);
                int marker;
                do { marker = input.readUnsignedByte(); } while (marker == 0xff);
                if (marker == 0xd9 || marker == 0xda) return 1;
                int length = input.readUnsignedShort() - 2;
                if (length < 0) return 1;
                byte[] segment = input.readNBytes(length);
                if (segment.length != length) return 1;
                if (marker == 0xe1) {
                    int orientation = parseExifOrientation(segment);
                    if (orientation != 1) return orientation;
                }
            }
        } catch (IOException | RuntimeException ignored) { return 1; }
    }

    private static int parseExifOrientation(byte[] segment) {
        if (segment.length < 14 || segment[0] != 'E' || segment[1] != 'x' || segment[2] != 'i'
                || segment[3] != 'f' || segment[4] != 0 || segment[5] != 0) return 1;
        ByteOrder order;
        if (segment[6] == 'I' && segment[7] == 'I') order = ByteOrder.LITTLE_ENDIAN;
        else if (segment[6] == 'M' && segment[7] == 'M') order = ByteOrder.BIG_ENDIAN;
        else return 1;
        ByteBuffer values = ByteBuffer.wrap(segment).order(order);
        if (Short.toUnsignedInt(values.getShort(8)) != 42) return 1;
        int directory = 6 + values.getInt(10);
        if (directory < 6 || directory + 2 > segment.length) return 1;
        int entries = Short.toUnsignedInt(values.getShort(directory));
        for (int index = 0; index < entries; index++) {
            int entry = directory + 2 + index * 12;
            if (entry + 12 > segment.length) return 1;
            if (Short.toUnsignedInt(values.getShort(entry)) == 0x0112
                    && Short.toUnsignedInt(values.getShort(entry + 2)) == 3 && values.getInt(entry + 4) == 1) {
                int orientation = Short.toUnsignedInt(values.getShort(entry + 8));
                return orientation >= 1 && orientation <= 8 ? orientation : 1;
            }
        }
        return 1;
    }

    private static long pixelCount(int width, int height) {
        if (width < 1 || height < 1) throw bad("Image dimensions are invalid.");
        return Math.multiplyExact((long) width, height);
    }
    private static int ceilDiv(int value, int divisor) { return (value + divisor - 1) / divisor; }
    private static String format(String mimeType) {
        if ("image/jpeg".equals(mimeType)) return "jpeg";
        if ("image/png".equals(mimeType)) return "png";
        return null;
    }
    private static void replace(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
            Files.move(source, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private record Raster(BufferedImage image, int orientation, int subsampling) { }
}
