package eu.royalblackwater.api.strategies.dto;

public record StrategyOverlayBackground(
        String fit,
        Double scale,
        Double opacity,
        Double brightness,
        Double contrast) {
    public StrategyOverlayBackground {
        fit = fit == null ? "stretch" : fit;
        scale = scale == null ? 1.0 : scale;
        opacity = opacity == null ? 0.82 : opacity;
        brightness = brightness == null ? 1.0 : brightness;
        contrast = contrast == null ? 1.0 : contrast;
    }
}
