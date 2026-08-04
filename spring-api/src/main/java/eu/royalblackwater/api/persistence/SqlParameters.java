package eu.royalblackwater.api.persistence;

import java.util.LinkedHashMap;
import java.util.Map;

public final class SqlParameters {
    private SqlParameters() { }

    public static Map<String, Object> ofNullable(Object... nameValuePairs) {
        if (nameValuePairs.length % 2 != 0) {
            throw new IllegalArgumentException("Parameters require name/value pairs.");
        }
        Map<String, Object> values = new LinkedHashMap<>();
        for (int index = 0; index < nameValuePairs.length; index += 2) {
            values.put(String.valueOf(nameValuePairs[index]), nameValuePairs[index + 1]);
        }
        return values;
    }
}
