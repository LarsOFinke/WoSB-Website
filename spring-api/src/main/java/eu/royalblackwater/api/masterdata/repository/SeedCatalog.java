package eu.royalblackwater.api.masterdata.repository;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.ResourcePatternResolver;
import org.springframework.stereotype.Component;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

@Component
public class SeedCatalog {
    private static final TypeReference<Map<String, Object>> MAP = new TypeReference<>() { };
    private final ResourcePatternResolver resources;
    private final ObjectMapper json;

    public SeedCatalog(ResourcePatternResolver resources, ObjectMapper json) {
        this.resources = resources;
        this.json = json;
    }

    public List<Map<String, Object>> categories() { return items("classpath:seed/builds/categories.json"); }

    public List<Map<String, Object>> options() {
        return resources("classpath*:seed/builds/options/*/*.json").stream()
                .map(this::item).toList();
    }

    public List<Map<String, Object>> ships() {
        return resources("classpath*:seed/ships/rates/*/*.json").stream()
                .map(this::item).toList();
    }

    public Map<String, Object> definitions() { return document("classpath:seed/ships/definitions.json"); }
    public Map<String, Object> buildRules() { return document("classpath:seed/system/build-rules.json"); }
    public Map<String, Object> systemRoles() { return document("classpath:seed/system/roles.json"); }
    public List<Map<String, Object>> systemFleets() { return items("classpath:seed/system/fleets.json"); }

    private List<Map<String, Object>> items(String location) {
        return listOfMaps(document(location).get("items"));
    }

    private Map<String, Object> document(String location) {
        return read(resources.getResource(location));
    }

    private Map<String, Object> item(Resource resource) {
        return readOnlyMap(read(resource));
    }

    private List<Resource> resources(String pattern) {
        try {
            List<Resource> result = new ArrayList<>(List.of(resources.getResources(pattern)));
            result.sort(Comparator.comparing(SeedCatalog::resourceLocation));
            return result;
        } catch (IOException exception) {
            throw new IllegalStateException("Could not enumerate seed resources: " + pattern, exception);
        }
    }

    private static String resourceLocation(Resource resource) {
        try {
            return resource.getURL().toExternalForm();
        } catch (IOException exception) {
            return resource.getDescription();
        }
    }

    private Map<String, Object> read(Resource resource) {
        try (InputStream input = resource.getInputStream()) {
            return json.readValue(input, MAP);
        } catch (IOException exception) {
            throw new IllegalStateException("Could not read seed resource: " + resource, exception);
        }
    }

    public static List<Map<String, Object>> listOfMaps(Object value) {
        if (!(value instanceof List<?> list)) return List.of();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Object item : list) {
            if (item instanceof Map<?, ?> raw) result.add(readOnlyMap(raw));
        }
        return List.copyOf(result);
    }

    private static Map<String, Object> readOnlyMap(Map<?, ?> raw) {
        Map<String, Object> normalized = new LinkedHashMap<>();
        raw.forEach((key, entry) -> normalized.put(String.valueOf(key), entry));
        return Collections.unmodifiableMap(normalized);
    }
}
