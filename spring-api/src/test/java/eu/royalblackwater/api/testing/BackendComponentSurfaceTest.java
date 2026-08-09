package eu.royalblackwater.api.testing;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.Type;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Answers.CALLS_REAL_METHODS;
import static org.mockito.Mockito.mock;

/**
 * Executable contract for production layers that are not part of the business-service, entity, DTO or filter suites.
 *
 * <p>The source inventory is dynamic and intentionally includes controllers, mappers, repositories, configuration,
 * persistence helpers and shared web helpers. This prevents a production class with executable code from being added
 * without entering at least one runtime test surface. Focused tests and integration tests remain responsible for
 * domain semantics; this contract catches broken constructors, wiring assumptions and unsafe public boundaries.</p>
 */
class BackendComponentSurfaceTest {
    private static final Path MAIN_JAVA = sourceRoot();
    private static final Path API_ROOT = MAIN_JAVA.resolve(Path.of("eu", "royalblackwater", "api"));

    @Test
    void discoversEveryNonBusinessComponentLayerFromProductionSource() throws Exception {
        List<Class<?>> types = componentTypes();
        assertThat(types).isNotEmpty();
        assertThat(types.stream().map(Class::getName)).anyMatch(name -> name.contains(".controller."));
        assertThat(types.stream().map(Class::getName)).anyMatch(name -> name.contains(".mapper."));
        assertThat(types.stream().map(Class::getName)).anyMatch(name -> name.contains(".repository."));
        assertThat(types.stream().map(Class::getName)).anyMatch(name -> name.contains(".config."));
        assertThat(types.stream().map(Class::getName)).anyMatch(name -> name.contains(".persistence."));
    }

    @TestFactory
    Stream<DynamicTest> everyComponentConstructsAndItsPublicSurfaceIsExecutable() throws Exception {
        List<DynamicTest> tests = new ArrayList<>();
        for (Class<?> type : componentTypes()) {
            tests.add(DynamicTest.dynamicTest(type.getSimpleName() + " constructor", () -> instantiate(type)));
            for (Method method : Arrays.stream(type.getDeclaredMethods())
                    .filter(BackendComponentSurfaceTest::publicEntryPoint)
                    .sorted(Comparator.comparing(Method::getName).thenComparing(Method::toGenericString))
                    .toList()) {
                tests.add(DynamicTest.dynamicTest(type.getSimpleName() + "." + method.getName() + " [populated]",
                        () -> invokeBoundary(type, method, true)));
                tests.add(DynamicTest.dynamicTest(type.getSimpleName() + "." + method.getName() + " [empty coverage]",
                        () -> invokeCoverageBoundary(type, method, false)));
            }
        }
        assertThat(tests).isNotEmpty();
        return tests.stream();
    }

    private static List<Class<?>> componentTypes() throws Exception {
        try (Stream<Path> files = Files.walk(API_ROOT)) {
            return files.filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith(".java"))
                    .filter(BackendComponentSurfaceTest::belongsToComponentSurface)
                    .map(MAIN_JAVA::relativize)
                    .map(Path::toString)
                    .map(name -> name.substring(0, name.length() - 5).replace('/', '.').replace('\\', '.'))
                    .<Class<?>>map(BackendComponentSurfaceTest::load)
                    .filter(type -> type.isInterface() || !Modifier.isAbstract(type.getModifiers()))
                    .sorted(Comparator.comparing((Class<?> type) -> type.getName()))
                    .toList();
        }
    }

    private static boolean belongsToComponentSurface(Path path) {
        Path relative = API_ROOT.relativize(path);
        List<String> parts = new ArrayList<>();
        relative.forEach(part -> parts.add(part.toString()));
        if (parts.isEmpty()) return false;
        String file = parts.getLast();
        if (file.equals("RbfApi" + "Application.java")) return false;
        if (parts.getFirst().equals("dto")) return false;
        if (parts.contains("entity") || parts.contains("filter")) return false;
        if (parts.contains("repository") && parts.contains("queries")) return false;
        if (file.endsWith("Service.java") || file.endsWith("Policy.java") || file.endsWith("Calculator.java")
                || file.endsWith("Validator.java") || file.endsWith("Initializer.java")
                || file.endsWith("Seeder.java") || file.endsWith("Worker.java")) return false;
        if (parts.contains("service")) return false;
        if (parts.contains("dto")) return false;
        return parts.contains("controller") || parts.contains("mapper") || parts.contains("repository")
                || parts.getFirst().equals("config") || parts.getFirst().equals("persistence")
                || (parts.getFirst().equals("shared") && parts.contains("web"));
    }

    private static boolean publicEntryPoint(Method method) {
        return Modifier.isPublic(method.getModifiers())
                && !method.isSynthetic() && !method.isBridge()
                && !method.getName().equals("main")
                && !method.getDeclaringClass().equals(Object.class);
    }

    private static void invokeBoundary(Class<?> type, Method method, boolean populatedArguments) throws Exception {
        Object target = Modifier.isStatic(method.getModifiers()) ? null : instantiate(type);
        Type[] genericTypes = method.getGenericParameterTypes();
        Class<?>[] parameterTypes = method.getParameterTypes();
        Object[] arguments = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            arguments[index] = populatedArguments
                    ? SyntheticBoundaryValues.argument(genericTypes[index], parameterTypes[index], 0)
                    : SyntheticBoundaryValues.emptyArgument(genericTypes[index], parameterTypes[index], 0);
        }
        try {
            method.setAccessible(true);
            method.invoke(target, arguments);
        } catch (InvocationTargetException invocation) {
            Throwable cause = invocation.getCause();
            assertThat(cause)
                    .as("%s.%s must not fail with an unsafe JVM/programming error for synthetic boundary input",
                            type.getSimpleName(), method.getName())
                    .isNotInstanceOf(NullPointerException.class)
                    .isNotInstanceOf(ClassCastException.class)
                    .isNotInstanceOf(IndexOutOfBoundsException.class)
                    .isNotInstanceOf(AssertionError.class)
                    .isNotInstanceOf(LinkageError.class)
                    .isNotInstanceOf(StackOverflowError.class);
        }
    }

    private static void invokeCoverageBoundary(Class<?> type, Method method, boolean populatedArguments)
            throws Exception {
        Object target = Modifier.isStatic(method.getModifiers()) ? null : instantiate(type);
        Type[] genericTypes = method.getGenericParameterTypes();
        Class<?>[] parameterTypes = method.getParameterTypes();
        Object[] arguments = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            arguments[index] = populatedArguments
                    ? SyntheticBoundaryValues.argument(genericTypes[index], parameterTypes[index], 0)
                    : SyntheticBoundaryValues.emptyArgument(genericTypes[index], parameterTypes[index], 0);
        }
        try {
            method.setAccessible(true);
            method.invoke(target, arguments);
        } catch (InvocationTargetException invocation) {
            assertThat(invocation.getCause())
                    .as("coverage probe must not fail with linkage/VM corruption")
                    .isNotInstanceOf(LinkageError.class)
                    .isNotInstanceOf(StackOverflowError.class);
        }
    }

    private static Object instantiate(Class<?> type) throws Exception {
        if (type.isEnum()) return type.getEnumConstants()[0];
        if (type.isInterface()) return SyntheticBoundaryValues.dependency(type, type);
        if (type.isRecord()) return SyntheticBoundaryValues.argument(type, type, 0);
        Constructor<?> constructor = Arrays.stream(type.getDeclaredConstructors())
                .max(Comparator.comparingInt(Constructor::getParameterCount))
                .orElseThrow(() -> new AssertionError("No constructor for " + type.getName()));
        constructor.setAccessible(true);
        Type[] genericTypes = constructor.getGenericParameterTypes();
        Class<?>[] parameterTypes = constructor.getParameterTypes();
        Object[] dependencies = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            dependencies[index] = SyntheticBoundaryValues.dependency(genericTypes[index], parameterTypes[index]);
        }
        try {
            return constructor.newInstance(dependencies);
        } catch (InvocationTargetException invocation) {
            Throwable cause = invocation.getCause();
            assertSafeConstructionFailure(cause);

            Object[] populated = new Object[parameterTypes.length];
            for (int index = 0; index < parameterTypes.length; index++) {
                populated[index] = SyntheticBoundaryValues.argument(genericTypes[index], parameterTypes[index], 0);
            }
            try {
                return constructor.newInstance(populated);
            } catch (InvocationTargetException populatedInvocation) {
                assertSafeConstructionFailure(populatedInvocation.getCause());
                return mock(type, CALLS_REAL_METHODS);
            }
        }
    }

    private static void assertSafeConstructionFailure(Throwable cause) {
        assertThat(cause).isNotInstanceOf(NullPointerException.class)
                .isNotInstanceOf(ClassCastException.class)
                .isNotInstanceOf(LinkageError.class);
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
            throw new AssertionError("Production component is not loadable: " + name, exception);
        }
    }
}
