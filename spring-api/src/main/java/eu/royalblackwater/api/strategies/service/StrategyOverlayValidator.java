package eu.royalblackwater.api.strategies.service;

import eu.royalblackwater.api.strategies.dto.PreparedStrategyOverlay;
import eu.royalblackwater.api.strategies.dto.StrategyBuildReference;
import eu.royalblackwater.api.strategies.dto.StrategyOverlay;
import eu.royalblackwater.api.strategies.dto.StrategyOverlayObject;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

@Service
public class StrategyOverlayValidator {
    private static final Set<String> TYPES = Set.of("ship", "line", "arrow", "formation", "text", "freehand");
    private static final Set<String> FORMATIONS = Set.of("line", "circle", "wedge", "column", "box");
    private static final Pattern ID = Pattern.compile("[A-Za-z0-9_-]{1,64}");
    private static final Pattern COLOR = Pattern.compile("#[0-9a-fA-F]{6}");
    private final ObjectMapper json;

    public StrategyOverlayValidator(ObjectMapper json) {
        this.json = json;
    }

    public PreparedStrategyOverlay prepare(String value) {
        if (value == null || value.isBlank() || value.length() > 200_000) throw bad("Strategy overlay is invalid.");
        StrategyOverlay overlay;
        try {
            overlay = json.readValue(value, StrategyOverlay.class);
        } catch (JacksonException exception) {
            throw bad("Strategy overlay must be valid JSON.");
        }
        if (overlay.version() != 1) throw bad("Unsupported strategy overlay version.");
        if (overlay.objects().size() > 250) throw bad("A strategy can contain at most 250 objects.");
        Set<String> objectIds = new LinkedHashSet<>();
        Set<Long> ships = new LinkedHashSet<>();
        Set<Long> builds = new LinkedHashSet<>();
        Set<Long> guides = new LinkedHashSet<>();
        Set<StrategyBuildReference> buildReferences = new LinkedHashSet<>();
        for (StrategyOverlayObject object : overlay.objects()) {
            validateObject(object, objectIds);
            if (object.shipId() != null) ships.add(object.shipId());
            if (object.buildId() != null) {
                builds.add(object.buildId());
                buildReferences.add(new StrategyBuildReference(object.buildId(), object.shipId()));
            }
            if (object.guideId() != null) guides.add(object.guideId());
        }
        try {
            return new PreparedStrategyOverlay(json.writeValueAsString(overlay), Set.copyOf(ships),
                    Set.copyOf(builds), Set.copyOf(guides), Set.copyOf(buildReferences));
        } catch (JacksonException exception) {
            throw new IllegalStateException("Could not normalize strategy overlay.", exception);
        }
    }

    private static void validateObject(StrategyOverlayObject object, Set<String> ids) {
        if (object == null || object.id() == null || !ID.matcher(object.id()).matches() || !ids.add(object.id())) {
            throw bad("Strategy object identifiers must be unique and safe.");
        }
        if (!TYPES.contains(object.type())) throw bad("Unsupported strategy object type.");
        coordinate(object.x()); coordinate(object.y());
        optionalCoordinate(object.x2()); optionalCoordinate(object.y2());
        optionalSize(object.width()); optionalSize(object.height());
        if (object.scale() != null && (!Double.isFinite(object.scale()) || object.scale() < 0.25 || object.scale() > 4)) {
            throw bad("Strategy object scale is invalid.");
        }
        if (object.rotation() != null && (!Double.isFinite(object.rotation()) || Math.abs(object.rotation()) > 360)) {
            throw bad("Strategy object rotation is invalid.");
        }
        if (object.color() != null && !COLOR.matcher(object.color()).matches()) throw bad("Strategy object color is invalid.");
        text(object.text(), 500, "Strategy text is too long.");
        text(object.shipName(), 120, "Ship name is too long.");
        text(object.shipType(), 80, "Ship type is too long.");
        if (object.shipRate() != null && (object.shipRate() < 1 || object.shipRate() > 7)) throw bad("Ship rate is invalid.");
        text(object.playerName(), 120, "Player name is too long.");
        if ("ship".equals(object.type()) && (object.shipId() == null || object.shipId() <= 0)) {
            throw bad("Every ship marker must reference a ship from the website catalog.");
        }
        positive(object.buildId(), "Build reference is invalid.");
        positive(object.guideId(), "Guide reference is invalid.");
        if (object.buildId() != null && !"ship".equals(object.type())) {
            throw bad("Build references are only allowed on ship markers.");
        }
        if ("formation".equals(object.type()) && !FORMATIONS.contains(object.formation())) {
            throw bad("Unsupported formation type.");
        }
        if ("freehand".equals(object.type())) {
            if (object.points().size() < 4 || object.points().size() > 400 || object.points().size() % 2 != 0) {
                throw bad("Freehand lines require between 2 and 200 points.");
            }
            object.points().forEach(StrategyOverlayValidator::coordinate);
        }
    }

    private static void coordinate(double value) {
        if (!Double.isFinite(value) || value < 0 || value > 1) throw bad("Strategy coordinates must be normalized.");
    }
    private static void optionalCoordinate(Double value) { if (value != null) coordinate(value); }
    private static void optionalSize(Double value) {
        if (value != null && (!Double.isFinite(value) || value <= 0 || value > 1)) throw bad("Strategy object size is invalid.");
    }
    private static void positive(Long value, String message) { if (value != null && value <= 0) throw bad(message); }
    private static void text(String value, int maximum, String message) { if (value != null && value.length() > maximum) throw bad(message); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
