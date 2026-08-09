package eu.royalblackwater.api.testing;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
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
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Executes every controller entry point with an authenticated typed principal and populated mocked collaborators.
 *
 * <p>The anonymous API contract deliberately stops protected routes at the security boundary. This complementary
 * contract crosses that boundary so controller response mapping, service delegation and no-content branches remain
 * executable even when the integration suite is focused on transport/authentication semantics.</p>
 */
class AuthenticatedControllerSurfaceTest {
    private static final Path MAIN_JAVA = sourceRoot();
    private static final Path API_ROOT = MAIN_JAVA.resolve(Path.of("eu", "royalblackwater", "api"));
    private static final AuthenticatedUser ACTOR =
            new AuthenticatedUser(1, "coverage-admin", "admin", true, true, true);

    @AfterEach
    void clearSecurityContext() {
        SecurityContextHolder.clearContext();
    }

    @TestFactory
    Stream<DynamicTest> everyControllerEntryPointExecutesPastAuthentication() throws Exception {
        List<DynamicTest> tests = new ArrayList<>();
        for (Class<?> controller : controllerTypes()) {
            for (Method method : Arrays.stream(controller.getDeclaredMethods())
                    .filter(AuthenticatedControllerSurfaceTest::publicEntryPoint)
                    .sorted(Comparator.comparing(Method::getName).thenComparing(Method::toGenericString))
                    .toList()) {
                tests.add(DynamicTest.dynamicTest(controller.getSimpleName() + "." + method.getName(),
                        () -> invoke(controller, method)));
            }
        }
        assertThat(tests).as("authenticated controller entry points").isNotEmpty();
        return tests.stream();
    }

    private static void invoke(Class<?> controllerType, Method method) throws Exception {
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(ACTOR, null, List.of()));
        Object controller = instantiate(controllerType);
        Type[] genericTypes = method.getGenericParameterTypes();
        Class<?>[] parameterTypes = method.getParameterTypes();
        Object[] arguments = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            arguments[index] = SyntheticBoundaryValues.argument(genericTypes[index], parameterTypes[index], 0);
        }
        try {
            method.setAccessible(true);
            method.invoke(controller, arguments);
        } catch (InvocationTargetException invocation) {
            Throwable cause = invocation.getCause();
            assertThat(cause)
                    .as("%s.%s must not fail with an unsafe JVM/programming error after authentication",
                            controllerType.getSimpleName(), method.getName())
                    .isNotInstanceOf(NullPointerException.class)
                    .isNotInstanceOf(ClassCastException.class)
                    .isNotInstanceOf(IndexOutOfBoundsException.class)
                    .isNotInstanceOf(AssertionError.class)
                    .isNotInstanceOf(LinkageError.class);
        } finally {
            SecurityContextHolder.clearContext();
        }
    }

    private static Object instantiate(Class<?> type) throws Exception {
        Constructor<?> constructor = Arrays.stream(type.getDeclaredConstructors())
                .max(Comparator.comparingInt(Constructor::getParameterCount))
                .orElseThrow(() -> new AssertionError("No constructor for " + type.getName()));
        constructor.setAccessible(true);
        Type[] genericTypes = constructor.getGenericParameterTypes();
        Class<?>[] parameterTypes = constructor.getParameterTypes();
        Object[] dependencies = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index++) {
            dependencies[index] = SyntheticBoundaryValues.dependency(
                    genericTypes[index], parameterTypes[index], SyntheticBoundaryValues.DependencyProfile.POPULATED);
        }
        return constructor.newInstance(dependencies);
    }

    private static List<Class<?>> controllerTypes() throws Exception {
        try (Stream<Path> files = Files.walk(API_ROOT)) {
            return files.filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith("Controller.java"))
                    .map(MAIN_JAVA::relativize)
                    .map(Path::toString)
                    .map(name -> name.substring(0, name.length() - 5).replace('/', '.').replace('\\', '.'))
                    .<Class<?>>map(AuthenticatedControllerSurfaceTest::load)
                    .sorted(Comparator.comparing((Class<?> type) -> type.getName()))
                    .toList();
        }
    }

    private static boolean publicEntryPoint(Method method) {
        return Modifier.isPublic(method.getModifiers())
                && !Modifier.isStatic(method.getModifiers())
                && !method.isSynthetic() && !method.isBridge()
                && method.getDeclaringClass() != Object.class;
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
            throw new AssertionError("Controller is not loadable: " + name, exception);
        }
    }
}
