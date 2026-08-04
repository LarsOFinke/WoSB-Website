package eu.royalblackwater.api.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

@Configuration
@EnableScheduling
@ConditionalOnProperty(name = "rbf.scheduling.enabled", havingValue = "true", matchIfMissing = true)
public class SchedulingConfiguration { }
