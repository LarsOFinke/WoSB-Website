package eu.royalblackwater.api.testing;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.lang.reflect.Array;
import java.lang.reflect.Constructor;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.RecordComponent;
import java.lang.reflect.Type;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Stream;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.mockito.invocation.InvocationOnMock;
import tools.jackson.databind.ObjectMapper;

import static org.mockito.Mockito.mock;

/** Type-correct synthetic values for backend-wide executable surface tests. */
final class SyntheticBoundaryValues {
    enum DependencyProfile { EMPTY, POPULATED }

    static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final int MAX_DEPTH = 6;

    private SyntheticBoundaryValues() { }

    static Object dependency(Type genericType, Class<?> type) {
        return dependency(genericType, type, DependencyProfile.EMPTY);
    }

    static Object dependency(Type genericType, Class<?> type, DependencyProfile profile) {
        if (type == ObjectMapper.class) return new ObjectMapper();
        return value(genericType, type, 0, profile == DependencyProfile.POPULATED);
    }

    static Object argument(Type genericType, Class<?> type, int depth) {
        return value(genericType, type, depth, true);
    }

    static Object emptyArgument(Type genericType, Class<?> type, int depth) {
        return value(genericType, type, depth, false);
    }

    static List<Object> branchArguments(Type genericType, Class<?> type) {
        LinkedHashSet<Object> values = new LinkedHashSet<>();
        if (!type.isPrimitive()) values.add(null);
        values.add(emptyArgument(genericType, type, 0));
        values.add(argument(genericType, type, 0));
        if (type == String.class) {
            values.add(" ");
            values.add("training");
            values.add("meeting");
            values.add("open");
            values.add("closed");
            values.add("fleet");
            values.add("squad");
            values.add("general");
            values.add("master-data");
            values.add("12345");
            values.add("https://raid-helper.xyz/api/v4");
            values.add("/internal");
        } else if (type == boolean.class || type == Boolean.class) {
            values.add(Boolean.FALSE);
            values.add(Boolean.TRUE);
        } else if (type == int.class || type == Integer.class) {
            values.add(-1); values.add(0); values.add(1); values.add(2); values.add(50);
        } else if (type == long.class || type == Long.class) {
            values.add(-1L); values.add(0L); values.add(1L); values.add(2L); values.add(7L); values.add(50L);
        } else if (type == double.class || type == Double.class) {
            values.add(-1.0d); values.add(0.0d); values.add(1.0d); values.add(2.5d);
        } else if (type == float.class || type == Float.class) {
            values.add(-1.0f); values.add(0.0f); values.add(1.0f); values.add(2.5f);
        } else if (type.isEnum()) {
            values.addAll(Arrays.asList(type.getEnumConstants()));
        }
        values.removeIf(value -> value == null && type.isPrimitive());
        return java.util.Collections.unmodifiableList(new java.util.ArrayList<>(values));
    }

    private static Object answer(InvocationOnMock invocation, boolean populated) {
        if (invocation.getMethod().getName().startsWith("save")
                && invocation.getArguments().length == 1
                && invocation.getArgument(0) != null) {
            return invocation.getArgument(0);
        }
        return value(invocation.getMethod().getGenericReturnType(), invocation.getMethod().getReturnType(), 0, populated);
    }

    private static Object value(Type genericType, Class<?> type, int depth, boolean populated) {
        if (type == void.class || type == Void.class) return null;
        if (depth > MAX_DEPTH) return type.isPrimitive() ? primitive(type, false) : null;
        if (type == String.class) return populated ? "test" : "";
        if (type == boolean.class || type == Boolean.class) return populated;
        if (type == byte.class || type == Byte.class) return populated ? (byte) 1 : (byte) 0;
        if (type == short.class || type == Short.class) return populated ? (short) 1 : (short) 0;
        if (type == int.class || type == Integer.class) return populated ? 1 : 0;
        if (type == long.class || type == Long.class) return populated ? 1L : 0L;
        if (type == float.class || type == Float.class) return populated ? 1.0f : 0.0f;
        if (type == double.class || type == Double.class) return populated ? 1.0d : 0.0d;
        if (type == char.class || type == Character.class) return populated ? 'x' : '\0';
        if (type == Instant.class) return CLOCK.instant();
        if (type == LocalDate.class) return LocalDate.of(2030, 1, 15);
        if (type == LocalDateTime.class) return LocalDateTime.of(2030, 1, 15, 12, 0);
        if (type == Duration.class) return Duration.ofMinutes(30);
        if (type == Clock.class) return CLOCK;
        if (type == UUID.class) return UUID.fromString("00000000-0000-0000-0000-000000000001");
        if (type == URI.class) return URI.create("https://example.invalid/test");
        if (type == Path.class) return Path.of(System.getProperty("java.io.tmpdir"), "rbf-synthetic-boundary");
        if (type == Class.class) return Object.class;
        if (InputStream.class.isAssignableFrom(type)) {
            return new ByteArrayInputStream("{}".getBytes(StandardCharsets.UTF_8));
        }
        if (Resource.class.isAssignableFrom(type)) {
            return new ByteArrayResource("{}".getBytes(StandardCharsets.UTF_8));
        }
        if (type.isEnum()) return type.getEnumConstants()[0];
        if (type.isArray()) return arrayValue(type.componentType(), depth, populated);
        if (Optional.class.isAssignableFrom(type)) return optionalValue(genericType, depth, populated);
        if (Stream.class.isAssignableFrom(type)) return populated
                ? listValue(genericType, depth, true).stream() : Stream.empty();
        if (Iterator.class.isAssignableFrom(type)) return populated
                ? listValue(genericType, depth, true).iterator() : Collections.emptyIterator();
        if (List.class.isAssignableFrom(type)) return listValue(genericType, depth, populated);
        if (Set.class.isAssignableFrom(type)) return setValue(genericType, depth, populated);
        if (Map.class.isAssignableFrom(type)) return mapValue(genericType, depth, populated);
        if (Collection.class.isAssignableFrom(type) || Iterable.class.isAssignableFrom(type)) {
            return listValue(genericType, depth, populated);
        }
        if (type.isRecord()) return recordValue(type, depth + 1, populated);
        if (type == Object.class) return null;
        return mock(type, invocation -> answer(invocation, populated));
    }


    private static Object arrayValue(Class<?> componentType, int depth, boolean populated) {
        int length = populated ? 1 : 0;
        Object array = Array.newInstance(componentType, length);
        if (length == 1) {
            Object item = value(componentType, componentType, depth + 1, true);
            if (item != null || !componentType.isPrimitive()) Array.set(array, 0, item);
        }
        return array;
    }

    private static Optional<?> optionalValue(Type genericType, int depth, boolean populated) {
        if (!populated) return Optional.empty();
        Object element = elementValue(genericType, depth + 1, true);
        return Optional.ofNullable(element);
    }

    private static Map<?, ?> mapValue(Type genericType, int depth, boolean populated) {
        if (!populated) return Map.of();
        if (!(genericType instanceof ParameterizedType parameterized)
                || parameterized.getActualTypeArguments().length < 2) {
            return universalRow();
        }
        Type keyType = parameterized.getActualTypeArguments()[0];
        Type valueType = parameterized.getActualTypeArguments()[1];
        if (keyType == String.class && valueType == Object.class) return universalRow();

        Object key = typedValue(keyType, depth + 1);
        Object mapValue = typedValue(valueType, depth + 1);
        if (key == null || mapValue == null) return Map.of();
        return Map.of(key, mapValue);
    }

    private static Object typedValue(Type type, int depth) {
        if (type instanceof Class<?> valueClass) return value(type, valueClass, depth, true);
        if (type instanceof ParameterizedType nested && nested.getRawType() instanceof Class<?> rawClass) {
            return value(type, rawClass, depth, true);
        }
        return null;
    }

    private static Map<String, Object> universalRow() {
        Map<String, Object> row = new HashMap<>();
        String[] strings = {
                "action", "actor_role", "actor_username", "announcement_template", "api_base_url",
                "api_key_encrypted", "author_name", "block_type", "body", "build_name", "build_role_label",
                "build_type", "category", "category_key", "category_label", "channel_id", "client_ip", "code",
                "column_name", "created_by_username", "delivery_id", "description", "description_template",
                "destination_name", "display_name", "effect_key", "endpoint_url", "entity_id", "entity_type",
                "event_type", "event_types_json", "fleet_focus", "fleet_name", "fleet_role", "fleet_slug",
                "focus", "image_url", "intro", "ip_address", "key", "label", "last_operation", "location",
                "max_weapon_class", "message", "message_template", "mime_type", "mortar_modification_source",
                "name", "notes", "option_kind", "option_name", "original_name", "owner_display_name",
                "owner_name", "password_hash", "payload_json", "payload_template_json", "printout_checksum",
                "profile_name", "raid_template_id", "reason", "relative_path", "reply_email", "request_target",
                "resource_id", "resource_type", "role", "role_label", "scope_type", "seed_key", "seed_revision",
                "server_id", "ship_name", "ship_type", "signal", "site_role", "slot_type", "slug", "source",
                "squad_name", "squad_role", "squad_slug", "status", "stored_name", "subject", "subject_username",
                "summary", "table_name", "template_name", "timezone", "title", "title_template", "updated_by",
                "usage_context", "username", "weapon_class", "webhook_name"
        };
        for (String key : strings) row.put(key, "test");
        row.put("status", "open");
        row.put("block_type", "resources");
        row.put("resource_type", "internal");
        row.put("scope_type", "fleet");
        row.put("category", "training");
        row.put("timezone", "UTC");
        row.put("api_base_url", "https://raid-helper.xyz/api/v4");
        row.put("api_key_encrypted", "encrypted-secret");
        row.put("server_id", "12345");
        row.put("channel_id", "54321");
        row.put("default_leader_id", "12345");
        row.put("leader_id_override", null);
        row.put("external_event_id", null);
        row.put("raid_template_id", "");
        row.put("payload_template_json", "{\"title\":\"{{event.title}}\",\"date\":\"{{event.date}}\",\"time\":\"{{event.time}}\"}");
        row.put("title_template", "{{event.title}}");
        row.put("description_template", "{{event.description}}");
        row.put("announcement_template", "");
        row.put("relative_path", "synthetic.txt");
        row.put("stored_name", "synthetic.txt");
        row.put("original_name", "synthetic.txt");
        row.put("mime_type", "text/plain");
        row.put("usage_context", "general");
        row.put("last_operation", "create");

        String[] numbers = {
                "active_count", "actor_user_id", "attempts", "author_id", "block_id",
                "broadside_capacity_delta", "broadside_weapon_capacity", "build_id", "build_reference_count",
                "capacity", "category_id", "created_by_user_id", "created_user_id", "crew_capacity",
                "crew_capacity_delta", "dedicated_special_weapon_capacity", "destination_id", "displacement_tons",
                "durability", "durability_delta", "event_count", "event_id", "file_id", "fleet_id",
                "fleet_membership_id", "front_special_weapon_capacity", "front_weapon_capacity", "handled_by_user_id",
                "hold_capacity", "id", "max_members", "max_ship_rate", "member_count", "membership_id",
                "mercenaries", "min_ship_rate", "mortar_capacity", "mortar_weapon_capacity", "musketeers",
                "option_id", "owner_id", "pending_count", "printout_size_bytes", "profile_id", "rank", "rate",
                "rear_special_weapon_capacity", "rear_weapon_capacity", "reply_count", "research_upgrade_feature_id",
                "response_status", "role_rank", "sail_slots", "sailor_minimum", "sailors", "scope_id", "ship_id",
                "ship_rate", "size_bytes", "soldiers", "sort_order", "special_weapon_capacity", "squad_id",
                "subject_user_id", "template_id", "thread_id", "unblocked_by_user_id", "upgrade_slots",
                "upvote_count", "user_id", "value", "webhook_id"
        };
        for (String key : numbers) row.put(key, 1L);
        row.put("active_count", 1L);
        row.put("max_members", 5L);
        row.put("min_ship_rate", 5L);
        row.put("max_ship_rate", 1L);

        String[] decimals = {
                "armor", "base_damage", "effect_value", "hold_capacity_pct", "maneuverability",
                "maneuverability_delta", "max_caliber_inches", "max_mortar_caliber_inches",
                "mortar_modification_broadside_capacity_delta", "mortar_modification_crew_capacity_delta",
                "mortar_modification_durability_delta", "mortar_modification_hold_capacity_pct",
                "mortar_modification_maneuverability_delta", "mortar_modification_max_caliber_inches",
                "mortar_modification_mortar_capacity", "mortar_modification_speed_pct", "reload_seconds",
                "speed_knots", "speed_min_knots", "speed_pct", "weapon_caliber_inches"
        };
        for (String key : decimals) row.put(key, 1.0d);

        String[] flags = {
                "all_day", "allow_guests", "broadcast_enabled", "can_manage_fleet", "can_manage_members",
                "destination_active", "destination_default", "fleet_active", "has_lantern", "is_active",
                "is_bootstrap_admin", "is_cancelled", "is_customized", "is_default", "is_guest",
                "is_leadership", "is_public", "is_seed_overridden", "is_system", "profile_active", "published",
                "raid_helper_enabled", "template_active", "template_default", "uses_premium_features",
                "wants_fleet_membership"
        };
        for (String key : flags) row.put(key, true);

        String[] timestamps = {
                "closed_at", "created_at", "delivered_at", "end_at", "expires_at", "joined_at",
                "last_activity_at", "last_attempt_at", "last_failure_at", "last_success_at", "left_at",
                "printout_source_updated_at", "printout_updated_at", "resolved_at", "reviewed_at",
                "scheduled_end_at", "scheduled_start_at", "start_at", "synced_at", "unblocked_at", "updated_at"
        };
        LocalDateTime time = LocalDateTime.of(2030, 1, 15, 12, 0);
        for (String key : timestamps) row.put(key, time);
        row.put("start_at", time);
        row.put("end_at", time.plusHours(1));
        row.put("expires_at", time.plusDays(1));
        row.put("scheduled_start_at", time.plusHours(1));
        row.put("scheduled_end_at", time.plusHours(2));
        return row;
    }

    private static List<?> listValue(Type genericType, int depth, boolean populated) {
        if (!populated) return List.of();
        Object element = elementValue(genericType, depth + 1, true);
        return element == null ? List.of() : List.of(element);
    }

    private static Set<?> setValue(Type genericType, int depth, boolean populated) {
        if (!populated) return Set.of();
        Object element = elementValue(genericType, depth + 1, true);
        return element == null ? Set.of() : Set.of(element);
    }

    private static Object elementValue(Type genericType, int depth, boolean populated) {
        if (!(genericType instanceof ParameterizedType parameterized)
                || parameterized.getActualTypeArguments().length == 0) {
            return null;
        }
        Type item = parameterized.getActualTypeArguments()[0];
        if (item instanceof Class<?> itemClass) return value(item, itemClass, depth, populated);
        if (item instanceof ParameterizedType nested && nested.getRawType() instanceof Class<?> rawClass) {
            return value(item, rawClass, depth, populated);
        }
        return null;
    }

    private static Object recordValue(Class<?> type, int depth, boolean populated) {
        try {
            RecordComponent[] components = type.getRecordComponents();
            Class<?>[] parameterTypes = Arrays.stream(components).map(RecordComponent::getType).toArray(Class<?>[]::new);
            Constructor<?> constructor = type.getDeclaredConstructor(parameterTypes);
            constructor.setAccessible(true);
            Object[] values = new Object[components.length];
            for (int index = 0; index < components.length; index++) {
                RecordComponent component = components[index];
                if (type.getName().equals("eu.royalblackwater.api.builds.dto.BuildPayload")
                        && component.getName().equals("upgrades")) {
                    values[index] = Collections.nCopies(8, null);
                } else {
                    values[index] = value(component.getGenericType(), component.getType(), depth + 1, populated);
                }
            }
            return constructor.newInstance(values);
        } catch (ReflectiveOperationException exception) {
            throw new AssertionError("Could not create synthetic record " + type.getName(), exception);
        }
    }

    private static Object primitive(Class<?> type, boolean populated) {
        if (type == boolean.class) return populated;
        if (type == char.class) return populated ? 'x' : '\0';
        if (type == byte.class) return populated ? (byte) 1 : (byte) 0;
        if (type == short.class) return populated ? (short) 1 : (short) 0;
        if (type == int.class) return populated ? 1 : 0;
        if (type == long.class) return populated ? 1L : 0L;
        if (type == float.class) return populated ? 1.0f : 0.0f;
        if (type == double.class) return populated ? 1.0d : 0.0d;
        throw new IllegalArgumentException("Unsupported primitive " + type);
    }
}
