package eu.royalblackwater.api.persistence;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;

public final class RowValues {
    private RowValues() { }

    public static long longValue(Map<String, Object> row, String key) {
        Object value = row.get(key);
        if (value instanceof Number number) return number.longValue();
        throw new IllegalStateException("Expected numeric column: " + key);
    }

    public static Long nullableLong(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value instanceof Number number ? number.longValue() : null;
    }

    public static int intValue(Map<String, Object> row, String key) {
        return Math.toIntExact(longValue(row, key));
    }

    public static String string(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value == null ? null : String.valueOf(value);
    }

    public static String requiredString(Map<String, Object> row, String key) {
        String value = string(row, key);
        if (value == null) throw new IllegalStateException("Expected text column: " + key);
        return value;
    }

    public static boolean booleanValue(Map<String, Object> row, String key) {
        Object value = row.get(key);
        if (value instanceof Boolean flag) return flag;
        throw new IllegalStateException("Expected boolean column: " + key);
    }

    public static LocalDate date(Map<String, Object> row, String key) {
        Object value = row.get(key);
        if (value instanceof LocalDate date) return date;
        if (value instanceof java.sql.Date sqlDate) return sqlDate.toLocalDate();
        throw new IllegalStateException("Expected date column: " + key);
    }

    public static LocalDateTime dateTime(Map<String, Object> row, String key) {
        LocalDateTime value = nullableDateTime(row, key);
        if (value == null) throw new IllegalStateException("Expected timestamp column: " + key);
        return value;
    }

    public static LocalDateTime nullableDateTime(Map<String, Object> row, String key) {
        Object value = row.get(key);
        if (value instanceof LocalDateTime time) return time;
        if (value instanceof Timestamp timestamp) return timestamp.toLocalDateTime();
        return null;
    }
}
