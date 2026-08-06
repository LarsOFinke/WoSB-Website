package eu.royalblackwater.api.guides.mapper;

import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.dto.GuideRead;
import eu.royalblackwater.api.dto.GuideSummary;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class GuideDtoMapper {
    private GuideDtoMapper() { }

    public static GuideSummary summary(Map<String, Object> row, UserReferenceRead owner) {
        long ownerId = RowValues.longValue(row, "owner_id");
        return new GuideSummary(RowValues.longValue(row, "attachment_count"),
                RowValues.longValue(row, "build_reference_count"),
                RowValues.requiredString(row, "category"), RowValues.dateTime(row, "created_at"),
                RowValues.longValue(row, "id"), owner, ownerId, RowValues.string(row, "summary"),
                RowValues.requiredString(row, "title"), RowValues.dateTime(row, "updated_at"));
    }
    public static GuideRead detail(GuideSummary summary, List<FileRead> attachments, String body,
            List<BuildRead> linkedBuilds) {
        return new GuideRead(summary.attachmentCount(), attachments, body, summary.buildReferenceCount(),
                linkedBuilds, summary.category(), summary.createdAt(), summary.id(), summary.owner(),
                summary.ownerId(), summary.summary(), summary.title(), summary.updatedAt());
    }

}
