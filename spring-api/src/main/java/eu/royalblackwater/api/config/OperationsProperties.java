package eu.royalblackwater.api.config;

import java.nio.file.Path;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.operations")
public record OperationsProperties(Path controlRoot) { }
