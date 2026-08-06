package eu.royalblackwater.api.onboarding.mapper;

import eu.royalblackwater.api.dto.NewcomerGuideBlockRead;
import eu.royalblackwater.api.dto.NewcomerGuideRead;
import eu.royalblackwater.api.dto.NewcomerGuideResourceRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class NewcomerGuideDtoMapper {
    private NewcomerGuideDtoMapper() { }

    public static NewcomerGuideRead guide(
            Map<String, Object> page, long pageId, List<NewcomerGuideBlockRead> blocks) {
        return new NewcomerGuideRead(List.copyOf(blocks), pageId, RowValues.requiredString(page, "intro"),
                RowValues.requiredString(page, "title"), RowValues.dateTime(page, "updated_at"),
                RowValues.string(page, "updated_by"));
    }

    public static NewcomerGuideBlockRead block(
            Map<String, Object> row, List<NewcomerGuideResourceRead> resources) {
        return new NewcomerGuideBlockRead(RowValues.requiredString(row, "block_type"),
                RowValues.string(row, "body"), RowValues.longValue(row, "id"), List.copyOf(resources),
                RowValues.requiredString(row, "title"));
    }

    public static NewcomerGuideResourceRead resource(
            Map<String, Object> row, boolean available, String description, String href,
            String label, Long resourceId, String type) {
        return new NewcomerGuideResourceRead(available, description, href, RowValues.longValue(row, "id"),
                label, resourceId, type);
    }
}
