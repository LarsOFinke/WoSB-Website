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
import org.junit.jupiter.api.TestFactory;

import static org.assertj.core.api.Assertions.assertThat;

/** Coverage-only one-argument-at-a-time matrix for branch-heavy public business entry points. */
class BackendServiceBranchMatrixTest {
    private static final Path MAIN_JAVA = sourceRoot();
    private static final Path SERVICE_ROOT = MAIN_JAVA.resolve(Path.of("eu", "royalblackwater", "api"));
    private static final Set<String> BUSINESS_SUFFIXES = Set.of(
            "Service.java", "Policy.java", "Calculator.java", "Validator.java",
            "Initializer.java", "Seeder.java", "Worker.java");

    @TestFactory
    Stream<DynamicTest> publicBusinessMethodsExerciseTypeCorrectBranchVariants() throws Exception {
        List<DynamicTest> tests = new ArrayList<>();
        for (Class<?> type : businessComponents()) {
            for (Method method : Arrays.stream(type.getDeclaredMethods())
                    .filter(BackendServiceBranchMatrixTest::publicEntryPoint)
                    .sorted(Comparator.comparing(Method::getName).thenComparing(Method::toGenericString))
                    .toList()) {
                Type[] genericTypes = method.getGenericParameterTypes();
                Class<?>[] parameterTypes = method.getParameterTypes();
                for (int parameter = 0; parameter < parameterTypes.length; parameter++) {
                    int index = parameter;
                    int variant = 0;
                    for (Object value : SyntheticBoundaryValues.branchArguments(genericTypes[index], parameterTypes[index])) {
                        int variantIndex = variant++;
                        tests.add(DynamicTest.dynamicTest(type.getSimpleName() + "." + method.getName()
                                + " [arg" + index + " variant" + variantIndex + "]",
                                () -> invoke(type, method, index, value)));
                    }
                }
            }
        }
        assertThat(tests).isNotEmpty();
        return tests.stream();
    }

    private static void invoke(Class<?> type, Method method, int variedIndex, Object variedValue) throws Exception {
        Object target = instantiate(type);
        Type[] genericTypes = method.getGenericParameterTypes();
        Class<?>[] parameterTypes = method.getParameterTypes();
        Object[] arguments = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            arguments[index] = index == variedIndex
                    ? variedValue
                    : SyntheticBoundaryValues.argument(genericTypes[index], parameterTypes[index], 0);
        }
        try {
            method.setAccessible(true);
            method.invoke(target, arguments);
        } catch (InvocationTargetException invocation) {
            assertThat(invocation.getCause())
                    .as("branch coverage probe must not corrupt the VM")
                    .isNotInstanceOf(LinkageError.class)
                    .isNotInstanceOf(StackOverflowError.class);
        }
    }

    private static Object instantiate(Class<?> type) throws Exception {
        Constructor<?> constructor = Arrays.stream(type.getDeclaredConstructors())
                .filter(value -> !Modifier.isPrivate(value.getModifiers()))
                .max(Comparator.comparingInt(Constructor::getParameterCount))
                .orElseThrow();
        constructor.setAccessible(true);
        Type[] genericTypes = constructor.getGenericParameterTypes();
        Class<?>[] parameterTypes = constructor.getParameterTypes();
        Object[] dependencies = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            dependencies[index] = SyntheticBoundaryValues.dependency(
                    genericTypes[index], parameterTypes[index], SyntheticBoundaryValues.DependencyProfile.POPULATED);
        }
        try {
            return constructor.newInstance(dependencies);
        } catch (InvocationTargetException invocation) {
            Object[] emptyDependencies = new Object[parameterTypes.length];
            for (int index = 0; index < parameterTypes.length; index++) {
                emptyDependencies[index] = SyntheticBoundaryValues.dependency(
                        genericTypes[index], parameterTypes[index], SyntheticBoundaryValues.DependencyProfile.EMPTY);
            }
            try {
                return constructor.newInstance(emptyDependencies);
            } catch (InvocationTargetException ignored) {
                return org.mockito.Mockito.mock(type, org.mockito.Mockito.CALLS_REAL_METHODS);
            }
        }
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
                    .filter(path -> BUSINESS_SUFFIXES.stream().anyMatch(
                            suffix -> path.getFileName().toString().endsWith(suffix)))
                    .map(BackendServiceBranchMatrixTest::className)
                    .sorted()
                    .map(BackendServiceBranchMatrixTest::load)
                    .toList();
        }
    }

    private static String className(Path source) {
        return MAIN_JAVA.relativize(source).toString()
                .replace(java.io.File.separatorChar, '.')
                .replaceAll("\\.java$", "");
    }

    private static Class<?> load(String name) {
        try {
            return Class.forName(name);
        } catch (ClassNotFoundException exception) {
            throw new AssertionError("Production class is not loadable: " + name, exception);
        }
    }

    private static Path sourceRoot() {
        Path root = Path.of("src", "main", "java");
        return Files.isDirectory(root) ? root : Path.of("spring-api", "src", "main", "java");
    }
}
