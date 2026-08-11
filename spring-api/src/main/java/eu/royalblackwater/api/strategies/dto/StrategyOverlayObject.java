package eu.royalblackwater.api.strategies.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record StrategyOverlayObject(
        String id,
        String type,
        double x,
        double y,
        Double x2,
        Double y2,
        Double width,
        Double height,
        Double rotation,
        String color,
        String text,
        @JsonProperty("shipId") @JsonAlias("ship_id") Long shipId,
        @JsonProperty("shipName") @JsonAlias("ship_name") String shipName,
        @JsonProperty("shipType") @JsonAlias("ship_type") String shipType,
        @JsonProperty("shipRate") @JsonAlias("ship_rate") Integer shipRate,
        @JsonProperty("playerName") @JsonAlias("player_name") String playerName,
        @JsonProperty("buildId") @JsonAlias("build_id") Long buildId,
        @JsonProperty("guideId") @JsonAlias("guide_id") Long guideId,
        String formation,
        Double scale,
        List<Double> points) {
    public StrategyOverlayObject {
        points = points == null ? List.of() : List.copyOf(points);
    }
}
