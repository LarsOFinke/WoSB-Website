package eu.royalblackwater.api.strategies.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record StrategyOverlay(int version, List<StrategyOverlayObject> objects) {
    public StrategyOverlay {
        objects = objects == null ? List.of() : List.copyOf(objects);
    }
}
