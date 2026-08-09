package eu.royalblackwater.api.testing;

import jakarta.validation.Validation;
import jakarta.validation.Validator;
import java.lang.reflect.Array;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.RecordComponent;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.http.ContentDisposition;
import org.springframework.http.MediaType;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Answers.RETURNS_DEEP_STUBS;
import static org.mockito.Mockito.mock;

/** Runtime contract for hand-written/module-local DTO records that are not generator-owned. */
class ModuleDtoContractTest {
    private static final Path SOURCE_ROOT = sourceRoot();
    private static final Path API_ROOT = SOURCE_ROOT.resolve(Path.of("eu", "royalblackwater", "api"));
    private final Validator validator = Validation.buildDefaultValidatorFactory().getValidator();
    private final ObjectMapper json = new ObjectMapper();

    @TestFactory
    Stream<DynamicTest> everyModuleDtoConstructsValidatesSerializesAndExposesAccessors() throws Exception {
        List<Class<?>> types = dtoTypes();
        assertThat(types).isNotEmpty().allMatch(Class::isRecord);
        return types.stream().map(type -> DynamicTest.dynamicTest(type.getName(), () -> {
            Object value = construct(type, 0);
            assertThat(value).isInstanceOf(type);
            assertThat(validator.validate(value)).isNotNull();
            if (Arrays.stream(type.getRecordComponents()).noneMatch(
                    component -> Resource.class.isAssignableFrom(component.getType()))) {
                assertThat(json.writeValueAsString(value)).startsWith("{").endsWith("}");
            }
            for (Method method : Arrays.stream(type.getDeclaredMethods())
                    .filter(candidate -> Modifier.isPublic(candidate.getModifiers()))
                    .filter(candidate -> !Modifier.isStatic(candidate.getModifiers()))
                    .filter(candidate -> candidate.getParameterCount() == 0)
                    .filter(candidate -> !candidate.isSynthetic())
                    .toList()) {
                method.invoke(value);
            }
        }));
    }

    private static List<Class<?>> dtoTypes() throws Exception {
        try (Stream<Path> files = Files.walk(API_ROOT)) {
            return files.filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith(".java"))
                    .filter(path -> path.getParent() != null && "dto".equals(path.getParent().getFileName().toString()))
                    .filter(path -> !path.getParent().equals(API_ROOT.resolve("dto")))
                    .map(SOURCE_ROOT::relativize)
                    .map(Path::toString)
                    .map(name -> name.substring(0, name.length() - 5).replace('/', '.').replace('\\', '.'))
                    .map(ModuleDtoContractTest::load)
                    .sorted(Comparator.comparing(Class::getName))
                    .toList();
        }
    }

    private static Object construct(Class<?> type, int depth) throws Exception {
        if (!type.isRecord()) return mock(type, RETURNS_DEEP_STUBS);
        RecordComponent[] components = type.getRecordComponents();
        Class<?>[] parameterTypes = Arrays.stream(components).map(RecordComponent::getType).toArray(Class<?>[]::new);
        Constructor<?> constructor = type.getDeclaredConstructor(parameterTypes);
        Object[] values = new Object[components.length];
        for (int index = 0; index < components.length; index++) {
            values[index] = neutral(components[index].getType(), depth + 1);
        }
        constructor.setAccessible(true);
        return constructor.newInstance(values);
    }

    private static Object neutral(Class<?> type, int depth) throws Exception {
        if (type == String.class) return "test";
        if (type == boolean.class || type == Boolean.class) return false;
        if (type == byte.class || type == Byte.class) return (byte) 1;
        if (type == short.class || type == Short.class) return (short) 1;
        if (type == int.class || type == Integer.class) return 1;
        if (type == long.class || type == Long.class) return 1L;
        if (type == float.class || type == Float.class) return 1.0f;
        if (type == double.class || type == Double.class) return 1.0d;
        if (type == char.class || type == Character.class) return 'x';
        if (type == LocalDate.class) return LocalDate.of(2030, 1, 15);
        if (type == LocalDateTime.class) return LocalDateTime.of(2030, 1, 15, 12, 0);
        if (type == Instant.class) return Instant.parse("2030-01-15T12:00:00Z");
        if (type == UUID.class) return UUID.fromString("00000000-0000-0000-0000-000000000001");
        if (type == URI.class) return URI.create("https://example.invalid/test");
        if (Resource.class.isAssignableFrom(type)) return new ByteArrayResource(new byte[0]);
        if (type == MediaType.class) return MediaType.APPLICATION_OCTET_STREAM;
        if (type == ContentDisposition.class) return ContentDisposition.attachment().filename("test.bin").build();
        if (type == CacheControl.class) return CacheControl.noCache();
        if (List.class.isAssignableFrom(type)) return List.of();
        if (Set.class.isAssignableFrom(type)) return Set.of();
        if (Map.class.isAssignableFrom(type)) return Map.of();
        if (Optional.class.isAssignableFrom(type)) return Optional.empty();
        if (type.isArray()) return Array.newInstance(type.componentType(), 0);
        if (type.isEnum()) return type.getEnumConstants()[0];
        if (type.isRecord() && depth <= 4) return construct(type, depth);
        return mock(type, RETURNS_DEEP_STUBS);
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
            throw new AssertionError("Module DTO is not loadable: " + name, exception);
        }
    }
}
