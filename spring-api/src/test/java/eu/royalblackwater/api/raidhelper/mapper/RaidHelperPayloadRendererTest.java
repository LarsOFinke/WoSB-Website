package eu.royalblackwater.api.raidhelper.mapper;

import eu.royalblackwater.api.raidhelper.dto.RaidHelperEventDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperTemplateConfigDto;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RaidHelperPayloadRendererTest {
    private final RaidHelperPayloadRenderer renderer = new RaidHelperPayloadRenderer(new ObjectMapper());

    @Test
    void rendersNestedValuesExactTokensListsUnknownTokensAndCustomTemplateIds() {
        RaidHelperEventDto event = new RaidHelperEventDto(42L, "Fleet Night", "training", null, null,
                LocalDateTime.of(2030, 1, 15, 12, 0), LocalDateTime.of(2030, 1, 15, 13, 30),
                false, 7L, "Alpha");
        RaidHelperTemplateConfigDto template = template("Europe/Berlin", "custom-42", """
                {
                  "title": "{{rendered.title}}",
                  "duration": "{{event.duration_minutes}}",
                  "scope": "{{scope.squad_id}}",
                  "items": ["{{event.title}}", "before {{event.unknown}} after", 2],
                  "nested": {"template": "{{raid_helper.template_id}}", "drop": null},
                  "templateId": "{{raid_helper.template_id}}"
                }
                """);

        Map<String, Object> values = renderer.render(event, template, "12345").values();

        assertThat(values).containsEntry("leaderId", "12345")
                .containsEntry("title", "Fleet Night")
                .containsEntry("duration", 90L)
                .containsEntry("scope", 7L)
                .containsEntry("templateId", "custom-42");
        assertThat(values.get("items")).isEqualTo(List.of("Fleet Night", "before  after", 2));
        @SuppressWarnings("unchecked")
        Map<String, Object> nested = (Map<String, Object>) values.get("nested");
        assertThat(nested).containsEntry("template", "custom-42").doesNotContainKey("drop");
    }

    @Test
    void fleetUtcContextNormalizesOffsetDurationAndRemovesStandardTemplateId() {
        RaidHelperEventDto event = new RaidHelperEventDto(1L, "Meeting", "meeting", "Description", "Harbor",
                LocalDateTime.of(2030, 1, 15, 12, 0), LocalDateTime.of(2030, 1, 15, 11, 0),
                true, null, null);
        RaidHelperTemplateConfigDto template = new RaidHelperTemplateConfigDto(1L, 1L, true, "UTC", "standard",
                "{{event.title}}", "{{event.description}}", "{{scope.name}}", """
                {"date":"{{event.date}}","time":"{{event.time}}","duration":"{{event.duration_minutes}}",
                 "offset":"{{event.utc_offset}}","scope":"{{scope.type}}","templateId":"{{raid_helper.template_id}}"}
                """);

        Map<String, Object> values = renderer.render(event, template, "99999").values();

        assertThat(values).containsEntry("duration", 1L)
                .containsEntry("offset", "+00:00")
                .containsEntry("scope", "fleet")
                .doesNotContainKey("templateId");
    }

    @Test
    void rejectsInvalidJsonAndNonObjectPayloads() {
        RaidHelperEventDto event = new RaidHelperEventDto(1L, "Meeting", "meeting", null, null,
                LocalDateTime.of(2030, 1, 15, 12, 0), LocalDateTime.of(2030, 1, 15, 13, 0),
                false, null, null);

        assertThatThrownBy(() -> renderer.render(event, template("UTC", null, "{"), "12345"))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("invalid JSON");
        assertThatThrownBy(() -> renderer.render(event, template("UTC", null, "[1,2,3]"), "12345"))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("JSON object");
    }

    private static RaidHelperTemplateConfigDto template(String timezone, String raidTemplateId, String payload) {
        return new RaidHelperTemplateConfigDto(1L, 1L, true, timezone, raidTemplateId,
                "{{event.title}}", "{{event.description}}", "{{scope.name}}", payload);
    }
}
