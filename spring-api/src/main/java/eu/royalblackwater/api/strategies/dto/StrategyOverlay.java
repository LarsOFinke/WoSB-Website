package eu.royalblackwater.api.strategies.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record StrategyOverlay(int version, List<StrategyOverlayObject> objects,
                              StrategyOverlayBackground background) {
    public StrategyOverlay(int version, List<StrategyOverlayObject> objects) {
        this(version, objects, null);
    }

    public StrategyOverlay {
        objects = objects == null ? List.of() : List.copyOf(objects);
        background = version == 2 && background == null ? new StrategyOverlayBackground(null, null, null, null, null) : background;
    }
}
