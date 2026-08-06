package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.service.BuildStatCatalog;
import eu.royalblackwater.api.builds.dto.BuildStatDefinition;
import eu.royalblackwater.api.dto.BuildStatDefinitionRead;
import eu.royalblackwater.api.dto.BuildStatRow;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;

@Component
public class BuildStatCalculator {
    public List<BuildStatDefinitionRead> definitionsForApi() {
        return BuildStatCatalog.ALL.stream().map(BuildDtoMapper::statDefinition).toList();
    }

    public List<BuildStatRow> calculate(
            Map<String, ? extends Number> ship,
            Map<String, ? extends Number> effects,
            List<? extends Map<String, ? extends Number>> effectSets) {
        List<BuildStatRow> rows = new ArrayList<>();
        Set<String> consumedEffects = new HashSet<>();
        for (BuildStatDefinition definition : BuildStatCatalog.ALL) {
            Double base = definition.baseField() == null ? null : number(ship.get(definition.baseField()));
            double percent = percentage(definition.pctEffect(), effects, effectSets);
            String flatKey = definition.calculationFlatEffect() != null
                    ? definition.calculationFlatEffect() : definition.flatEffect();
            double flat = flatKey == null ? 0 : numberOrZero(effects.get(flatKey));
            addConsumed(consumedEffects, definition.pctEffect(), definition.flatEffect(),
                    definition.calculationFlatEffect());
            if (base == null && percent == 0 && flat == 0) continue;

            Double effective = base;
            if (base != null && definition.pctEffect() != null) {
                Double percentageBase = definition.pctBaseField() == null
                        ? base : number(ship.get(definition.pctBaseField()));
                if (percentageBase == null || (percentageBase <= 0 && base > 0)) percentageBase = base;
                effective = base + percentageBase * percent / 100;
            }
            if (effective != null) effective += flat;
            else if (definition.flatEffect() != null) effective = flat;
            double rawModifier = base != null && effective != null ? effective - base : (flat != 0 ? flat : percent);
            boolean hasPercentage = percent != 0;
            boolean hasFlat = flat != 0;
            rows.add(BuildDtoMapper.statRow(
                    rounded(base, definition.precision()), definition.category(),
                    definition.pctEffect() != null ? definition.pctEffect() : definition.flatEffect(),
                    rounded(effective, definition.precision()), hasFlat ? rounded(flat, definition.precision()) : null,
                    isDebuff(definition, base, effective, rawModifier), definition.key(), definition.label(),
                    rounded(rawModifier, definition.precision()),
                    hasPercentage && hasFlat ? "composite" : hasPercentage ? "percent" : "flat",
                    hasPercentage ? rounded(percent, 1) : null, definition.precision(),
                    definition.source(), definition.unit()));
        }
        effects.entrySet().stream().filter(entry -> !consumedEffects.contains(entry.getKey()))
                .sorted(Map.Entry.comparingByKey()).forEach(entry -> appendUnknown(rows, entry));
        return List.copyOf(rows);
    }

    public Map<String, Number> effectiveStats(List<BuildStatRow> rows) {
        Map<String, Number> result = new LinkedHashMap<>();
        rows.forEach(row -> result.put(row.key(), row.effective()));
        return Map.copyOf(result);
    }

    public static long roundWhole(double value) {
        return BigDecimal.valueOf(value).setScale(0, RoundingMode.HALF_UP).longValueExact();
    }

    private static double percentage(String key, Map<String, ? extends Number> effects,
                                     List<? extends Map<String, ? extends Number>> effectSets) {
        if (key == null) return 0;
        double multiplier = 1;
        boolean found = false;
        if (effectSets != null) {
            for (Map<String, ? extends Number> effectSet : effectSets) {
                double value = numberOrZero(effectSet.get(key));
                if (value != 0) {
                    multiplier *= 1 + value / 100;
                    found = true;
                }
            }
        }
        if (!found) multiplier = 1 + numberOrZero(effects.get(key)) / 100;
        return (multiplier - 1) * 100;
    }

    private static void appendUnknown(List<BuildStatRow> rows, Map.Entry<String, ? extends Number> entry) {
        double value = entry.getValue() == null ? 0 : entry.getValue().doubleValue();
        if (value == 0) return;
        int precision = value == Math.rint(value) ? 0 : 1;
        String label = java.util.Arrays.stream(entry.getKey().replace("_pct", " %").split("_"))
                .filter(part -> !part.isBlank())
                .map(part -> Character.toUpperCase(part.charAt(0)) + part.substring(1))
                .reduce((left, right) -> left + " " + right).orElse(entry.getKey());
        Number rounded = rounded(value, precision);
        rows.add(BuildDtoMapper.unknownStatRow(entry.getKey(), label, rounded, value < 0, precision,
                entry.getKey().endsWith("_pct") ? "%" : null));
    }

    private static boolean isDebuff(BuildStatDefinition definition, Double base, Double effective, double modifier) {
        double delta = base != null && effective != null ? effective - base : modifier;
        if (delta == 0) return false;
        return definition.positiveIsGood() ? delta < 0 : delta > 0;
    }

    private static Number rounded(Double value, int precision) {
        if (value == null) return null;
        BigDecimal rounded = BigDecimal.valueOf(value).setScale(Math.max(0, precision), RoundingMode.HALF_UP);
        if (precision <= 0) return rounded.longValueExact();
        return rounded.doubleValue();
    }

    private static Double number(Number value) { return value == null ? null : value.doubleValue(); }
    private static double numberOrZero(Number value) { return value == null ? 0 : value.doubleValue(); }
    private static void addConsumed(Set<String> target, String... keys) {
        for (String key : keys) if (key != null) target.add(key);
    }
}
