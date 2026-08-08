package eu.royalblackwater.api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.diagnostics")
public record ApiDiagnosticsProperties(boolean httpLifecycleLogging) { }
