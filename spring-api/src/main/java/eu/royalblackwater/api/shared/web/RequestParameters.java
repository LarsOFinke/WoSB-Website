package eu.royalblackwater.api.shared.web;

import java.util.LinkedHashMap;
import java.util.Map;

/** Builds immutable parameter views only for reusable filter factories. */
public final class RequestParameters {
    private RequestParameters() { }

    public static Map<String, Object> empty() {
        return Map.of();
    }

    public static Map<String, Object> of(Object... pairs) {
        if (pairs.length % 2 != 0) {
            throw new IllegalArgumentException("Request parameter pairs must contain name and value.");
        }
        Map<String, Object> parameters = new LinkedHashMap<>();
        for (int index = 0; index < pairs.length; index += 2) {
            parameters.put(String.valueOf(pairs[index]), pairs[index + 1]);
        }
        return Map.copyOf(parameters);
    }
}
