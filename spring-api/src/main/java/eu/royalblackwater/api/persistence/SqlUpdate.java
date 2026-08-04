package eu.royalblackwater.api.persistence;

import java.util.LinkedHashMap;
import java.util.Map;

public final class SqlUpdate {
    private final String table;
    private final String idColumn;
    private final Object id;
    private final Map<String, Object> values = new LinkedHashMap<>();

    public SqlUpdate(String table, String idColumn, Object id) {
        if (!identifier(table) || !identifier(idColumn)) throw new IllegalArgumentException("Unsafe SQL identifier.");
        this.table = table;
        this.idColumn = idColumn;
        this.id = id;
    }

    public SqlUpdate set(String column, Object value) {
        if (!identifier(column)) throw new IllegalArgumentException("Unsafe SQL identifier.");
        values.put(column, value);
        return this;
    }

    public boolean isEmpty() {
        return values.isEmpty();
    }

    public String sql() {
        if (values.isEmpty()) throw new IllegalStateException("No update values.");
        String assignments = values.keySet().stream()
                .map(column -> column + " = :value_" + column).collect(java.util.stream.Collectors.joining(", "));
        return "update " + table + " set " + assignments + " where " + idColumn + " = :row_id";
    }

    public Map<String, Object> parameters() {
        Map<String, Object> parameters = new LinkedHashMap<>();
        values.forEach((column, value) -> parameters.put("value_" + column, value));
        parameters.put("row_id", id);
        return parameters;
    }

    public java.util.Set<String> columns() {
        return java.util.Set.copyOf(values.keySet());
    }

    private static boolean identifier(String value) {
        return value != null && value.matches("[a-z][a-z0-9_]*");
    }
}
