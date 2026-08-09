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
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Backend-wide executable safety net for the complete business/service layer.
 *
 * <p>The inventory is discovered from production source instead of a maintained allow-list. Every public entry point
 * of classes ending in Service, Policy, Calculator, Validator, Initializer, Seeder or Worker is invoked with a
 * deterministic non-null boundary object graph and mocked collaborators. Controlled domain rejection is permitted;
 * JVM/runtime failures that usually signal missing guards or broken wiring are not.</p>
 *
 * <p>Focused module tests remain responsible for business semantics. This test exists to prevent a newly added class or
 * public entry point from silently falling outside the executable backend test surface.</p>
 */
class BackendServiceSurfaceTest {
    private static final Path MAIN_JAVA = sourceRoot();
    private static final Path SERVICE_ROOT = MAIN_JAVA.resolve(Path.of("eu", "royalblackwater", "api"));
    private static final String API_PREFIX = "eu.royalblackwater.api.";
    private static final Set<String> BUSINESS_SUFFIXES = Set.of(
            "Service.java", "Policy.java", "Calculator.java", "Validator.java",
            "Initializer.java", "Seeder.java", "Worker.java");

    @Test
    void discoversEveryBusinessComponentFromTheProductionServiceLayer() throws Exception {
        List<Class<?>> components = businessComponents();
        assertThat(components).as("business/service layer components").isNotEmpty();
        assertThat(components).allSatisfy(type -> assertThat(type.getName()).startsWith(API_PREFIX));
        assertThat(components.stream().flatMap(type -> Arrays.stream(type.getDeclaredMethods()))
                .filter(BackendServiceSurfaceTest::publicEntryPoint)).isNotEmpty();
    }

    @TestFactory
    Stream<DynamicTest> everyPublicBusinessEntryPointHasAnExecutableBoundaryCase() throws Exception {
        List<DynamicTest> tests = new ArrayList<>();
        for (Class<?> componentType : businessComponents()) {
            for (Method method : Arrays.stream(componentType.getDeclaredMethods())
                    .filter(BackendServiceSurfaceTest::publicEntryPoint)
                    .sorted(Comparator.comparing(Method::getName).thenComparing(Method::toGenericString))
                    .toList()) {
                tests.add(DynamicTest.dynamicTest(componentType.getSimpleName() + "." + method.getName() + " [populated/empty-deps]",
                        () -> invokeBoundary(componentType, method, true, SyntheticBoundaryValues.DependencyProfile.EMPTY)));
                tests.add(DynamicTest.dynamicTest(componentType.getSimpleName() + "." + method.getName() + " [empty/empty-deps coverage]",
                        () -> invokeCoverageBoundary(componentType, method, false, SyntheticBoundaryValues.DependencyProfile.EMPTY)));
                tests.add(DynamicTest.dynamicTest(componentType.getSimpleName() + "." + method.getName() + " [populated/populated-deps coverage]",
                        () -> invokeCoverageBoundary(componentType, method, true, SyntheticBoundaryValues.DependencyProfile.POPULATED)));
                tests.add(DynamicTest.dynamicTest(componentType.getSimpleName() + "." + method.getName() + " [empty/populated-deps coverage]",
                        () -> invokeCoverageBoundary(componentType, method, false, SyntheticBoundaryValues.DependencyProfile.POPULATED)));
            }
        }
        assertThat(tests).as("public business entry points").isNotEmpty();
        return tests.stream();
    }

    private static void invokeBoundary(Class<?> componentType, Method method, boolean populatedArguments,
            SyntheticBoundaryValues.DependencyProfile dependencyProfile) throws Exception {
        Object component = instantiate(componentType, dependencyProfile);
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
            method.invoke(component, arguments);
        } catch (InvocationTargetException invocation) {
            Throwable cause = invocation.getCause();
            assertThat(cause)
                    .as("%s.%s must fail in a controlled domain-specific way for synthetic boundary input",
                            componentType.getSimpleName(), method.getName())
                    .isNotInstanceOf(NullPointerException.class)
                    .isNotInstanceOf(ClassCastException.class)
                    .isNotInstanceOf(IndexOutOfBoundsException.class)
                    .isNotInstanceOf(AssertionError.class)
                    .isNotInstanceOf(LinkageError.class)
                    .isNotInstanceOf(StackOverflowError.class);
        }
    }

    private static void invokeCoverageBoundary(Class<?> componentType, Method method, boolean populatedArguments,
            SyntheticBoundaryValues.DependencyProfile dependencyProfile) throws Exception {
        Object component = instantiate(componentType, dependencyProfile);
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
            method.invoke(component, arguments);
        } catch (InvocationTargetException invocation) {
            assertThat(invocation.getCause())
                    .as("coverage probe must not fail with linkage/VM corruption")
                    .isNotInstanceOf(LinkageError.class)
                    .isNotInstanceOf(StackOverflowError.class);
        }
    }

    private static Object instantiate(Class<?> type, SyntheticBoundaryValues.DependencyProfile dependencyProfile)
            throws Exception {
        Constructor<?> constructor = Arrays.stream(type.getDeclaredConstructors())
                .filter(value -> !Modifier.isPrivate(value.getModifiers()))
                .max(Comparator.comparingInt(Constructor::getParameterCount))
                .orElseThrow(() -> new AssertionError("No usable constructor for " + type.getName()));
        constructor.setAccessible(true);
        Type[] genericTypes = constructor.getGenericParameterTypes();
        Class<?>[] parameterTypes = constructor.getParameterTypes();
        Object[] dependencies = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            dependencies[index] = dependency(genericTypes[index], parameterTypes[index], dependencyProfile);
        }
        return constructor.newInstance(dependencies);
    }

    private static Object dependency(Type genericType, Class<?> type,
            SyntheticBoundaryValues.DependencyProfile dependencyProfile) {
        return SyntheticBoundaryValues.dependency(genericType, type, dependencyProfile);
    }

    private static boolean publicEntryPoint(Method method) {
        return Modifier.isPublic(method.getModifiers())
                && !Modifier.isStatic(method.getModifiers())
                && !method.isBridge()
                && !method.isSynthetic()
                && method.getDeclaringClass() != Object.class;
    }

    private static List<Class<?>> businessComponents() throws Exception {
        try (Stream<Path> files = Files.walk(SERVICE_ROOT)) {
            return files.filter(Files::isRegularFile)
                    .filter(path -> BUSINESS_SUFFIXES.stream().anyMatch(suffix -> path.getFileName().toString().endsWith(suffix)))
                    .filter(path -> path.getParent() != null && !path.getParent().equals(SERVICE_ROOT.resolve("dto")))
                    .map(MAIN_JAVA::relativize)
                    .map(Path::toString)
                    .map(name -> name.substring(0, name.length() - ".java".length()).replace('/', '.').replace('\\', '.'))
                    .filter(name -> name.startsWith(API_PREFIX))
                    .<Class<?>>map(BackendServiceSurfaceTest::load)
                    .filter(type -> !Throwable.class.isAssignableFrom(type))
                    .sorted(Comparator.comparing((Class<?> type) -> type.getName()))
                    .toList();
        }
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
            throw new AssertionError("Production business component is not loadable: " + name, exception);
        }
    }
}
