package eu.royalblackwater.api.config;

import java.nio.file.Path;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.storage")
public record StorageProperties(
        Path uploadRoot,
        long imageLimitMb,
        long documentLimitMb,
        long videoLimitMb,
        long perUserTotalMb,
        long globalTotalMb,
        long minimumFreeMb) {

    public StorageProperties {
        uploadRoot = uploadRoot == null ? Path.of("/var/lib/rbf/uploads") : uploadRoot;
        imageLimitMb = positiveOr(imageLimitMb, 12);
        documentLimitMb = positiveOr(documentLimitMb, 24);
        videoLimitMb = positiveOr(videoLimitMb, 50);
        perUserTotalMb = nonNegativeOr(perUserTotalMb, 250);
        globalTotalMb = nonNegativeOr(globalTotalMb, 4096);
        minimumFreeMb = nonNegativeOr(minimumFreeMb, 512);
    }

    private static long positiveOr(long value, long fallback) { return value > 0 ? value : fallback; }
    private static long nonNegativeOr(long value, long fallback) { return value >= 0 ? value : fallback; }
}
