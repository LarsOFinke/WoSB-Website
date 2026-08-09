package eu.royalblackwater.api.testing;

import jakarta.persistence.Entity;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Answers.RETURNS_DEEP_STUBS;
import static org.mockito.Mockito.mock;

/** Executable baseline contract for every JPA entity, complementing schema validation and state-transition tests. */
class PersistenceEntityContractTest {
    private static final Path SOURCE_ROOT = sourceRoot();
    private static final Path API_ROOT = SOURCE_ROOT.resolve(Path.of("eu", "royalblackwater", "api"));

    @TestFactory
    Stream<DynamicTest> everyEntityConstructsAndItsReadSurfaceIsExecutable() throws Exception {
        List<Class<?>> entities = entityTypes();
        assertThat(entities).isNotEmpty().allMatch(type -> type.isAnnotationPresent(Entity.class));
        return entities.stream().map(type -> DynamicTest.dynamicTest(type.getName(), () -> {
            Object entity = instantiate(type);
            populateNeutralFields(entity);
            for (Method method : Arrays.stream(type.getDeclaredMethods())
                    .filter(candidate -> Modifier.isPublic(candidate.getModifiers()))
                    .filter(candidate -> !Modifier.isStatic(candidate.getModifiers()))
                    .filter(candidate -> candidate.getParameterCount() == 0)
                    .filter(candidate -> !candidate.isSynthetic())
                    .toList()) {
                method.invoke(entity);
            }
        }));
    }

    private static List<Class<?>> entityTypes() throws Exception {
        try (Stream<Path> files = Files.walk(API_ROOT)) {
            return files.filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith(".java"))
                    .filter(path -> path.getParent() != null && "entity".equals(path.getParent().getFileName().toString()))
                    .map(SOURCE_ROOT::relativize)
                    .map(Path::toString)
                    .map(name -> name.substring(0, name.length() - 5).replace('/', '.').replace('\\', '.'))
                    .<Class<?>>map(PersistenceEntityContractTest::load)
                    .sorted(Comparator.comparing((Class<?> type) -> type.getName()))
                    .toList();
        }
    }

    private static Object instantiate(Class<?> type) throws Exception {
        Constructor<?> constructor = type.getDeclaredConstructor();
        constructor.setAccessible(true);
        return constructor.newInstance();
    }

    private static void populateNeutralFields(Object target) throws IllegalAccessException {
        for (Field field : target.getClass().getDeclaredFields()) {
            if (Modifier.isStatic(field.getModifiers())) continue;
            field.setAccessible(true);
            if (field.getType().isPrimitive() || field.get(target) != null) continue;
            Object value = neutral(field.getType());
            if (value != null) field.set(target, value);
        }
    }

    private static Object neutral(Class<?> type) {
        if (type == String.class) return "test";
        if (type == Integer.class) return 1;
        if (type == Long.class) return 1L;
        if (type == LocalDate.class) return LocalDate.of(2030, 1, 15);
        if (type == LocalDateTime.class) return LocalDateTime.of(2030, 1, 15, 12, 0);
        if (List.class.isAssignableFrom(type)) return new ArrayList<>();
        if (Set.class.isAssignableFrom(type)) return Set.of();
        if (Map.class.isAssignableFrom(type)) return Map.of();
        if (type.isEnum()) return type.getEnumConstants()[0];
        if (type.isAnnotationPresent(Entity.class)) return mock(type, RETURNS_DEEP_STUBS);
        return null;
    }

    private static Path sourceRoot() {
        Path moduleRoot = Path.of("src", "main", "java");
        if (Files.isDirectory(moduleRoot)) return moduleRoot;
        Path repositoryRoot = Path.of("spring-api", "src", "main", "java");
        if (Files.isDirectory(repositoryRoot)) return repositoryRoot;
        throw new IllegalStateException("Spring production source root is unavailable.");
    }

    private static Class<?> load(String name) {
        try {
            return Class.forName(name);
        } catch (ClassNotFoundException exception) {
            throw new AssertionError("Persistence entity is not loadable: " + name, exception);
        }
    }
}
