package eu.royalblackwater.api.shared.filter;

import java.util.Locale;
import java.util.Set;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

/** Validated, bounded query values shared by list endpoints. */
public record ListFilter(String search, int limit, int offset) {
    public static ListFilter of(String search, long limit, long offset, int maximumLimit) {
        return new ListFilter(
                optionalText(search, "search", 120),
                boundedInteger(limit, 1, maximumLimit, "limit"),
                boundedInteger(offset, 0, 100_000, "offset"));
    }

    public static String optionalText(String raw, String name, int maximumLength) {
        if (raw == null) {
            return null;
        }
        String value = raw.strip();
        if (value.isEmpty()) {
            return null;
        }
        if (value.length() > maximumLength) {
            throw bad(name + " is too long.");
        }
        return value;
    }

    public static String optionalEnum(String raw, String name, Set<String> values) {
        String value = optionalText(raw, name, 64);
        if (value == null) {
            return null;
        }
        String normalized = value.toLowerCase(Locale.ROOT);
        if (!values.contains(normalized)) {
            throw bad("Invalid " + name + " filter.");
        }
        return normalized;
    }

    public static Long optionalPositiveLong(Long value, String name) {
        if (value == null) {
            return null;
        }
        if (value <= 0) {
            throw bad("Invalid " + name + " filter.");
        }
        return value;
    }

    private static int boundedInteger(long candidate, int minimum, int maximum, String name) {
        if (candidate < minimum || candidate > maximum) {
            throw bad(name + " must be between " + minimum + " and " + maximum + ".");
        }
        return Math.toIntExact(candidate);
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }
}
