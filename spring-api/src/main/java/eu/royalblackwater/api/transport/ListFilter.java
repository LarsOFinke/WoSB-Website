package eu.royalblackwater.api.transport;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.web.server.ResponseStatusException;

/** Validated, bounded query values shared by list endpoints. */
public record ListFilter(String search, int limit, int offset) {
    public static ListFilter from(Map<String, Object> parameters, int defaultLimit, int maximumLimit) {
        if (defaultLimit < 1 || defaultLimit > maximumLimit) {
            throw new IllegalArgumentException("Invalid list-filter limits.");
        }
        String search = normalizedText(parameters.get("search"), 120, "search");
        int limit = boundedInteger(parameters.get("limit"), defaultLimit, 1, maximumLimit, "limit");
        int offset = boundedInteger(parameters.get("offset"), 0, 0, 100_000, "offset");
        return new ListFilter(search, limit, offset);
    }

    public static String optionalText(Map<String, Object> parameters, String name, int maximumLength) {
        return normalizedText(parameters.get(name), maximumLength, name);
    }

    public static String optionalEnum(Map<String, Object> parameters, String name, Set<String> values) {
        String value = normalizedText(parameters.get(name), 64, name);
        if (value == null) {
            return null;
        }
        String normalized = value.toLowerCase(Locale.ROOT);
        if (!values.contains(normalized)) {
            throw bad("Invalid " + name + " filter.");
        }
        return normalized;
    }

    public static Long optionalPositiveLong(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        if (value == null) {
            return null;
        }
        long candidate = exactLong(value, name);
        if (candidate <= 0) {
            throw bad("Invalid " + name + " filter.");
        }
        return candidate;
    }

    private static String normalizedText(Object raw, int maximumLength, String name) {
        if (raw == null) {
            return null;
        }
        String value = String.valueOf(raw).strip();
        if (value.isEmpty()) {
            return null;
        }
        if (value.length() > maximumLength) {
            throw bad(name + " is too long.");
        }
        return value;
    }

    private static int boundedInteger(Object raw, int fallback, int minimum, int maximum, String name) {
        long candidate = raw == null ? fallback : exactLong(raw, name);
        if (candidate < minimum || candidate > maximum) {
            throw bad(name + " must be between " + minimum + " and " + maximum + ".");
        }
        return Math.toIntExact(candidate);
    }

    private static long exactLong(Object raw, String name) {
        try {
            if (raw instanceof BigInteger integer) {
                return integer.longValueExact();
            }
            if (raw instanceof BigDecimal decimal) {
                return decimal.longValueExact();
            }
            if (raw instanceof Byte || raw instanceof Short || raw instanceof Integer || raw instanceof Long) {
                return ((Number) raw).longValue();
            }
            if (raw instanceof Number number) {
                return new BigDecimal(number.toString()).longValueExact();
            }
        } catch (ArithmeticException exception) {
            throw bad("Invalid " + name + ".");
        }
        throw bad("Invalid " + name + ".");
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }
}
