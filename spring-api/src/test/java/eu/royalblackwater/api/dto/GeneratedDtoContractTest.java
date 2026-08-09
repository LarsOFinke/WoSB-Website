package eu.royalblackwater.api.dto;

import jakarta.validation.Validation;
import jakarta.validation.Validator;
import java.lang.reflect.Constructor;
import java.lang.reflect.RecordComponent;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;

/** Runtime safety net for every generated OpenAPI DTO. */
class GeneratedDtoContractTest {
    private static final Path DTO_SOURCE = dtoSource();
    private final Validator validator = Validation.buildDefaultValidatorFactory().getValidator();
    private final ObjectMapper json = new ObjectMapper();

    @TestFactory
    Stream<DynamicTest> everyGeneratedDtoLoadsConstructsValidatesAndSerializes() throws Exception {
        List<Class<?>> types;
        try (Stream<Path> files = Files.list(DTO_SOURCE)) {
            types = files.filter(path -> path.getFileName().toString().endsWith(".java"))
                    .map(path -> "eu.royalblackwater.api.dto." + path.getFileName().toString().replaceFirst("\\.java$", ""))
                    .<Class<?>>map(GeneratedDtoContractTest::load)
                    .sorted(Comparator.comparing((Class<?> type) -> type.getName()))
                    .toList();
        }
        assertThat(types).isNotEmpty().allMatch(Class::isRecord);
        return types.stream().map(type -> DynamicTest.dynamicTest(type.getSimpleName(), () -> {
            Object value = construct(type);
            assertThat(value).isInstanceOf(type);
            assertThat(validator.validate(value)).isNotNull();
            assertThat(json.writeValueAsString(value)).startsWith("{").endsWith("}");
        }));
    }

    private static Object construct(Class<?> type) throws Exception {
        RecordComponent[] components = type.getRecordComponents();
        Class<?>[] parameterTypes = Arrays.stream(components).map(RecordComponent::getType).toArray(Class<?>[]::new);
        Constructor<?> constructor = type.getDeclaredConstructor(parameterTypes);
        Object[] values = Arrays.stream(parameterTypes).map(GeneratedDtoContractTest::neutralValue).toArray();
        return constructor.newInstance(values);
    }

    private static Object neutralValue(Class<?> type) {
        if (!type.isPrimitive()) return null;
        if (type == boolean.class) return false;
        if (type == char.class) return '\0';
        if (type == byte.class) return (byte) 0;
        if (type == short.class) return (short) 0;
        if (type == int.class) return 0;
        if (type == long.class) return 0L;
        if (type == float.class) return 0.0f;
        if (type == double.class) return 0.0d;
        throw new IllegalArgumentException("Unsupported primitive: " + type);
    }

    private static Path dtoSource() {
        Path moduleRoot = Path.of("src", "main", "java", "eu", "royalblackwater", "api", "dto");
        if (Files.isDirectory(moduleRoot)) return moduleRoot;
        Path repositoryRoot = Path.of("spring-api", "src", "main", "java", "eu", "royalblackwater", "api", "dto");
        if (Files.isDirectory(repositoryRoot)) return repositoryRoot;
        throw new IllegalStateException("Generated DTO source root is unavailable.");
    }

    private static Class<?> load(String name) {
        try {
            return Class.forName(name);
        } catch (ClassNotFoundException exception) {
            throw new AssertionError("Generated DTO is not loadable: " + name, exception);
        }
    }
}
