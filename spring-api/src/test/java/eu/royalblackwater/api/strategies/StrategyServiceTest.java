package eu.royalblackwater.api.strategies;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.StrategyCreate;
import eu.royalblackwater.api.dto.StrategyUpdate;
import eu.royalblackwater.api.files.dto.StoredFileDto;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.strategies.repository.StrategyRepository;
import eu.royalblackwater.api.strategies.repository.queries.StrategyQueries;
import eu.royalblackwater.api.strategies.dto.StrategyOverlay;
import eu.royalblackwater.api.strategies.dto.StrategyOverlayObject;
import eu.royalblackwater.api.strategies.mapper.StrategyMapper;
import eu.royalblackwater.api.strategies.service.StrategyOverlayValidator;
import eu.royalblackwater.api.strategies.service.StrategyService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.PropertyNamingStrategies;
import tools.jackson.databind.json.JsonMapper;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class StrategyServiceTest {
    private static final AuthenticatedUser OWNER = new AuthenticatedUser(7, "captain", "member", false, false, false);
    private static final String VALID = """
            {"version":1,"objects":[
              {"id":"ship-1","type":"ship","x":0.25,"y":0.75,"rotation":0,"color":"#f4c76b",
               "shipId":11,"shipName":"Leopard","shipType":"Frigate","shipRate":3,
               "playerName":null,"buildId":21,"guideId":31,"points":[]}
            ]}
            """;

    @Test
    void overlayKeepsPlayersOptionalAndExtractsWebsiteReferences() {
        StrategyOverlayValidator validator = new StrategyOverlayValidator(new ObjectMapper());
        var prepared = validator.prepare(VALID);

        assertThat(prepared.shipIds()).containsExactly(11L);
        assertThat(prepared.buildIds()).containsExactly(21L);
        assertThat(prepared.guideIds()).containsExactly(31L);
        assertThat(prepared.buildReferences()).singleElement().satisfies(reference -> {
            assertThat(reference.buildId()).isEqualTo(21L);
            assertThat(reference.shipId()).isEqualTo(11L);
        });
        assertThat(prepared.json()).contains("\"playerName\":null");
    }

    @Test
    void overlayAcceptsTheCompleteBrowserDocumentAndIgnoresClientOnlyState() {
        String browserDocument = """
                {"version":1,"editorViewport":{"zoom":1.25},"objects":[
                  {"id":"ship-1","type":"ship","x":0.55,"y":0.6,"rotation":15,"scale":1.5,
                   "color":"#f4c76b","shipId":11,"shipName":"Leopard","shipType":"Frigate",
                   "shipRate":3,"playerName":null,"buildId":21,"guideId":31,"selected":true},
                  {"id":"arrow-1","type":"arrow","x":0.2,"y":0.3,"x2":0.7,"y2":0.5,
                   "rotation":45,"scale":2,"color":"#ef6461"},
                  {"id":"formation-1","type":"formation","x":0.5,"y":0.5,"width":0.4,
                   "height":0.3,"rotation":0,"scale":1,"color":"#5cc8ff","formation":"wedge"},
                  {"id":"freehand-1","type":"freehand","x":0,"y":0,"rotation":0,"scale":1,
                   "color":"#ffffff","points":[0.1,0.2,0.3,0.4]}
                ]}
                """;

        ObjectMapper productionMapper = JsonMapper.builder()
                .propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
                .build();
        var prepared = new StrategyOverlayValidator(productionMapper).prepare(browserDocument);

        assertThat(prepared.shipIds()).containsExactly(11L);
        assertThat(prepared.buildIds()).containsExactly(21L);
        assertThat(prepared.guideIds()).containsExactly(31L);
        assertThat(prepared.json()).contains("\"shipId\":11", "\"shipName\":\"Leopard\"", "\"scale\":2.0")
                .doesNotContain("ship_id", "ship_name", "editorViewport", "selected");
    }

    @Test
    void overlayRecordsDefensivelyCopyObjectAndPointLists() {
        List<Double> points = new ArrayList<>(List.of(0.1, 0.2, 0.3, 0.4));
        StrategyOverlayObject object = new StrategyOverlayObject("free-1", "freehand", 0, 0,
                null, null, null, null, null, "#ffffff", null, null, null, null,
                null, null, null, null, null, null, points);
        List<StrategyOverlayObject> objects = new ArrayList<>(List.of(object));
        StrategyOverlay overlay = new StrategyOverlay(1, objects);
        points.add(0.5); objects.clear();

        assertThat(object.points()).hasSize(4);
        assertThat(overlay.objects()).containsExactly(object);
    }

    @Test
    void overlayRejectsShipMarkersWithoutShipsAndOutOfBoundsCoordinates() {
        StrategyOverlayValidator validator = new StrategyOverlayValidator(new ObjectMapper());
        assertThatThrownBy(() -> validator.prepare(
                "{\"version\":1,\"objects\":[{\"id\":\"x\",\"type\":\"ship\",\"x\":1.2,\"y\":0.5}]}"))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("normalized");
        assertThatThrownBy(() -> validator.prepare(
                "{\"version\":1,\"objects\":[{\"id\":\"x\",\"type\":\"text\",\"x\":0.5,\"y\":0.5,\"scale\":4.1}]}"))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("scale");
    }

    @Test
    void createRejectsReferencesThatAreNotPresentOnTheWebsite() {
        StrategyRepository repository = mock(StrategyRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        when(files.ownedImage(9, OWNER)).thenReturn(new StoredFileDto(9, 7L));
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        StrategyService service = new StrategyService(repository,
                new StrategyOverlayValidator(new ObjectMapper()), files, mock(AuditService.class),
                Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC));

        assertThatThrownBy(() -> service.create(new StrategyCreate("Port battle", null, 9, VALID), OWNER))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("ships do not exist");
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void createRejectsABuildThatBelongsToADifferentMarkerShip() {
        StrategyRepository repository = mock(StrategyRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        when(files.ownedImage(9, OWNER)).thenReturn(new StoredFileDto(9, 7L));
        when(repository.count(eq(StrategyQueries.EXISTING_SHIPS), anyMap())).thenReturn(1L);
        when(repository.query(eq(StrategyQueries.BUILD_SHIPS), anyMap()))
                .thenReturn(List.of(Map.of("id", 21L, "ship_id", 12L)));
        StrategyService service = new StrategyService(repository,
                new StrategyOverlayValidator(new ObjectMapper()), files, mock(AuditService.class),
                Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC));

        assertThatThrownBy(() -> service.create(new StrategyCreate("Port battle", null, 9, VALID), OWNER))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("does not belong to the ship");
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void mapperKeepsBackgroundAndPublicationMetadataInReadModels() {
        var row = strategyRow(41, 9);

        var detail = StrategyMapper.read(row);
        var summary = StrategyMapper.summary(row);

        assertThat(detail.id()).isEqualTo(41L);
        assertThat(detail.backgroundFile().id()).isEqualTo(9L);
        assertThat(detail.publishedAt()).isEqualTo(row.get("published_at"));
        assertThat(summary.title()).isEqualTo(detail.title());
        assertThat(summary.backgroundFile()).isEqualTo(detail.backgroundFile());
    }

    @Test
    void publicationRefreshesTheBackgroundFileRatherThanTheStrategyId() {
        StrategyRepository repository = mock(StrategyRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        when(repository.optional(eq(StrategyQueries.OWNED), anyMap()))
                .thenReturn(Optional.of(strategyRow(41, 9)));
        StrategyService service = service(repository, files);

        service.publication(41, true, OWNER);

        verify(files).refreshPublication(Set.of(9L));
    }

    @Test
    void deleteRefreshesTheBackgroundFileRatherThanTheStrategyId() {
        StrategyRepository repository = mock(StrategyRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        when(repository.optional(eq(StrategyQueries.OWNED), anyMap()))
                .thenReturn(Optional.of(strategyRow(41, 9)));
        when(repository.update(eq(StrategyQueries.DELETE), anyMap())).thenReturn(1);
        StrategyService service = service(repository, files);

        service.delete(41, OWNER);

        verify(files).refreshPublication(Set.of(9L));
    }

    @Test
    void updateRefreshesPreviousAndReplacementBackgroundFiles() {
        StrategyRepository repository = mock(StrategyRepository.class);
        FileAssetService files = mock(FileAssetService.class);
        when(repository.optional(eq(StrategyQueries.OWNED), anyMap()))
                .thenReturn(Optional.of(strategyRow(41, 9)));
        when(files.ownedImage(10, OWNER)).thenReturn(new StoredFileDto(10, 7L));
        when(repository.count(eq(StrategyQueries.EXISTING_SHIPS), anyMap())).thenReturn(1L);
        when(repository.query(eq(StrategyQueries.BUILD_SHIPS), anyMap()))
                .thenReturn(List.of(Map.of("id", 21L, "ship_id", 11L)));
        when(repository.count(eq(StrategyQueries.EXISTING_GUIDES), anyMap())).thenReturn(1L);
        when(repository.update(eq(StrategyQueries.UPDATE), anyMap())).thenReturn(1);
        StrategyService service = service(repository, files);

        service.update(41, new StrategyUpdate("Updated plan", null, 10, VALID), OWNER);

        verify(files).refreshPublication(Set.of(9L, 10L));
    }

    private static StrategyService service(StrategyRepository repository, FileAssetService files) {
        return new StrategyService(repository, new StrategyOverlayValidator(new ObjectMapper()), files,
                mock(AuditService.class), Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC));
    }

    private static Map<String, Object> strategyRow(long strategyId, long backgroundFileId) {
        LocalDateTime createdAt = LocalDateTime.of(2030, 1, 15, 12, 0);
        var row = new LinkedHashMap<String, Object>();
        row.put("strategy_id", strategyId);
        row.put("owner_id", 7L);
        row.put("background_file_id", backgroundFileId);
        row.put("title", "North harbor approach");
        row.put("description", "Hold the eastern line");
        row.put("overlay_json", VALID);
        row.put("is_published", true);
        row.put("public_id", "4f30d366-5d04-4bc1-ae1a-4df5b88c0834");
        row.put("strategy_created_at", createdAt);
        row.put("strategy_updated_at", createdAt.plusHours(1));
        row.put("published_at", createdAt.plusHours(1).plusMinutes(10));
        row.put("id", backgroundFileId);
        row.put("created_at", createdAt.minusDays(1));
        row.put("is_public", true);
        row.put("mime_type", "image/png");
        row.put("original_name", "harbor.png");
        row.put("relative_path", "strategy/7/harbor.png");
        row.put("size_bytes", 2048L);
        row.put("stored_name", "harbor.png");
        row.put("usage_context", "strategy");
        return row;
    }
}
