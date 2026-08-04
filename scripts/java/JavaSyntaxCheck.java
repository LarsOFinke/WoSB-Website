import com.sun.source.util.JavacTask;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.stream.Stream;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

/** Parse every Java source without resolving third-party dependencies. */
public final class JavaSyntaxCheck {
    private JavaSyntaxCheck() {
    }

    public static void main(String[] args) throws Exception {
        Path root = args.length == 0 ? Path.of("spring-api", "src") : Path.of(args[0]);
        List<Path> sources = findSources(root);
        if (sources.isEmpty()) {
            throw new IllegalStateException("No Java sources found below " + root);
        }

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new IllegalStateException("A full JDK is required for the Java syntax check.");
        }

        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager files = compiler.getStandardFileManager(diagnostics, Locale.ROOT, null)) {
            Iterable<? extends JavaFileObject> units = files.getJavaFileObjectsFromPaths(sources);
            JavacTask task = (JavacTask) compiler.getTask(
                    null,
                    files,
                    diagnostics,
                    List.of("--release", "21", "-proc:none", "-Xlint:none"),
                    null,
                    units);
            task.parse();
        }

        List<Diagnostic<? extends JavaFileObject>> errors = diagnostics.getDiagnostics().stream()
                .filter(diagnostic -> diagnostic.getKind() == Diagnostic.Kind.ERROR)
                .toList();
        if (!errors.isEmpty()) {
            errors.forEach(JavaSyntaxCheck::printDiagnostic);
            throw new IllegalStateException("Java syntax check failed with " + errors.size() + " error(s).");
        }
        System.out.printf("Java syntax OK (%d source files).%n", sources.size());
    }

    private static List<Path> findSources(Path root) throws IOException {
        try (Stream<Path> paths = Files.walk(root)) {
            return paths.filter(path -> path.getFileName().toString().endsWith(".java"))
                    .sorted(Comparator.comparing(Path::toString))
                    .toList();
        }
    }

    private static void printDiagnostic(Diagnostic<? extends JavaFileObject> diagnostic) {
        String source = diagnostic.getSource() == null ? "<unknown>" : diagnostic.getSource().getName();
        System.err.printf(
                "%s:%d:%d: %s%n",
                source,
                diagnostic.getLineNumber(),
                diagnostic.getColumnNumber(),
                diagnostic.getMessage(Locale.ROOT));
    }
}
