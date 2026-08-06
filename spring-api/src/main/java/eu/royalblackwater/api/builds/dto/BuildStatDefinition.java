package eu.royalblackwater.api.builds.dto;

public record BuildStatDefinition(
        String key,
        String label,
        String category,
        String baseField,
        String unit,
        String pctEffect,
        String flatEffect,
        String calculationFlatEffect,
        int precision,
        boolean positiveIsGood,
        String source,
        String pctBaseField) { }
