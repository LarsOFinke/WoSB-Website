package eu.royalblackwater.api.transport;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public final class ApiParameters {
    private ApiParameters() { }

    public static Map<String, Object> empty() {
        return Map.of();
    }

    public static Map<String, Object> of(Object... nameValuePairs) {
        if (nameValuePairs.length % 2 != 0) {
            throw new IllegalArgumentException("Parameters require name/value pairs.");
        }
        Map<String, Object> values = new LinkedHashMap<>();
        for (int index = 0; index < nameValuePairs.length; index += 2) {
            Object value = nameValuePairs[index + 1];
            if (value != null) {
                values.put(String.valueOf(nameValuePairs[index]), value);
            }
        }
        return Collections.unmodifiableMap(values);
    }
}
