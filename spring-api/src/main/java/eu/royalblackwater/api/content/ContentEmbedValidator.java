package eu.royalblackwater.api.content;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;

@Component
public class ContentEmbedValidator {
    private static final Pattern FILE = Pattern.compile("\\[\\[file:(?<id>\\d+)(?:\\|(?<size>[a-z0-9_-]+))?]]",
            Pattern.CASE_INSENSITIVE);
    private static final Pattern BUILD = Pattern.compile("\\[\\[build:(?<id>\\d+)(?:\\|(?<layout>[a-z0-9_-]+))?]]",
            Pattern.CASE_INSENSITIVE);
    private static final Set<String> FILE_SIZES = Set.of("small", "medium", "large", "full");
    private static final Set<String> BUILD_LAYOUTS = Set.of("compact", "card", "full");

    public void validateFiles(String body, List<Long> attachedIds) {
        validate(body, attachedIds, FILE, "size", FILE_SIZES, 24,
                "Invalid inline file size", "Inline file embeds must reference files attached to the same content.");
    }

    public void validateBuilds(String body, List<Long> linkedIds) {
        validate(body, linkedIds, BUILD, "layout", BUILD_LAYOUTS, 16,
                "Invalid inline build layout", "Inline build embeds must reference builds linked to the same guide.");
    }

    private static void validate(String body, List<Long> availableIds, Pattern pattern, String optionName,
                                 Set<String> allowedOptions, int maximum, String optionError, String referenceError) {
        Set<Long> available = new HashSet<>(availableIds == null ? List.of() : availableIds);
        Matcher matcher = pattern.matcher(body == null ? "" : body);
        int count = 0;
        while (matcher.find()) {
            if (++count > maximum) throw bad("Too many inline embeds. Maximum is " + maximum + ".");
            String option = matcher.group(optionName);
            if (option != null && !allowedOptions.contains(option.toLowerCase())) {
                throw bad(optionError + " '" + option + "'. Allowed: " + String.join(", ", allowedOptions) + ".");
            }
            if (!available.contains(Long.parseLong(matcher.group("id")))) throw bad(referenceError);
        }
    }

    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
