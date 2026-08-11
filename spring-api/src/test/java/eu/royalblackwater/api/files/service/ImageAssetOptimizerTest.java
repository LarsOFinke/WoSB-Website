package eu.royalblackwater.api.files.service;

import java.awt.Color;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ImageAssetOptimizerTest {
    @TempDir Path root;
    private final ImageAssetOptimizer optimizer = new ImageAssetOptimizer();

    @Test
    void recompressesJpegAndKeepsItReadable() throws Exception {
        Path source = root.resolve("photo.jpg");
        BufferedImage image = image(1200, 800, BufferedImage.TYPE_INT_RGB);
        writeJpeg(image, source, 1f);
        long originalSize = Files.size(source);

        optimizer.optimize(source, "image/jpeg");

        assertThat(Files.size(source)).isLessThan(originalSize);
        BufferedImage stored = ImageIO.read(source.toFile());
        assertThat(stored.getWidth()).isEqualTo(1200);
        assertThat(stored.getHeight()).isEqualTo(800);
    }

    @Test
    void boundsLargePngDimensionsWithoutChangingItsFormat() throws Exception {
        Path source = root.resolve("chart.png");
        ImageIO.write(image(5000, 120, BufferedImage.TYPE_INT_ARGB), "png", source.toFile());

        optimizer.optimize(source, "image/png");

        BufferedImage stored = ImageIO.read(source.toFile());
        assertThat(stored.getWidth()).isEqualTo(ImageAssetOptimizer.MAX_DIMENSION);
        assertThat(stored.getHeight()).isBetween(1, 120);
        assertThat(Files.readAllBytes(source)).startsWith((byte) 0x89, (byte) 0x50, (byte) 0x4e, (byte) 0x47);
    }

    @Test
    void preservesFormatsWithoutASafeStillImageWriter() throws Exception {
        Path source = root.resolve("animation.gif");
        byte[] content = "GIF89a-preserved".getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        Files.write(source, content);

        optimizer.optimize(source, "image/gif");

        assertThat(Files.readAllBytes(source)).isEqualTo(content);
    }

    @Test
    void rejectsMalformedSupportedImagesInsteadOfPassingThemThrough() throws Exception {
        Path source = root.resolve("broken.jpg");
        Files.write(source, new byte[]{(byte) 0xff, (byte) 0xd8, (byte) 0xff});

        assertThatThrownBy(() -> optimizer.optimize(source, "image/jpeg"))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("could not be decoded");
        assertThat(root.resolve("broken.jpg.optimized")).doesNotExist();
    }

    private static BufferedImage image(int width, int height, int type) {
        BufferedImage image = new BufferedImage(width, height, type);
        for (int y = 0; y < height; y++) for (int x = 0; x < width; x++) {
            image.setRGB(x, y, new Color((x * 31 + y * 7) & 255, (x * 11 + y * 29) & 255,
                    (x * 17 + y * 13) & 255, 255).getRGB());
        }
        return image;
    }

    private static void writeJpeg(BufferedImage image, Path target, float quality) throws Exception {
        ImageWriter writer = ImageIO.getImageWritersByFormatName("jpeg").next();
        try (ImageOutputStream output = ImageIO.createImageOutputStream(target.toFile())) {
            writer.setOutput(output);
            ImageWriteParam parameters = writer.getDefaultWriteParam();
            parameters.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
            parameters.setCompressionQuality(quality);
            writer.write(null, new IIOImage(image, null, null), parameters);
        } finally { writer.dispose(); }
    }
}
