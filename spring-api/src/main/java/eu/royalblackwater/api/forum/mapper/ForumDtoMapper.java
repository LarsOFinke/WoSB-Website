package eu.royalblackwater.api.forum.mapper;

import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.dto.ForumPostRead;
import eu.royalblackwater.api.dto.ForumThreadRead;
import eu.royalblackwater.api.dto.ForumThreadSummary;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class ForumDtoMapper {
    private ForumDtoMapper() { }

    public static ForumThreadSummary threadSummary(Map<String, Object> row, String category) {
        long ownerId = RowValues.longValue(row, "owner_id");
        return new ForumThreadSummary(category, RowValues.dateTime(row, "created_at"),
                RowValues.longValue(row, "id"), RowValues.dateTime(row, "last_activity_at"),
                new UserReferenceRead(RowValues.requiredString(row, "owner_name"), ownerId), ownerId,
                RowValues.longValue(row, "reply_count"), RowValues.requiredString(row, "title"),
                RowValues.dateTime(row, "updated_at"));
    }

    public static ForumPostRead post(Map<String, Object> row, List<FileRead> attachments) {
        long authorId = RowValues.longValue(row, "author_id");
        return new ForumPostRead(attachments,
                new UserReferenceRead(RowValues.requiredString(row, "author_name"), authorId),
                authorId, RowValues.requiredString(row, "body"), RowValues.dateTime(row, "created_at"),
                RowValues.longValue(row, "id"), RowValues.longValue(row, "thread_id"),
                RowValues.dateTime(row, "updated_at"));
    }
    public static ForumThreadRead thread(ForumThreadSummary summary, List<ForumPostRead> posts) {
        return new ForumThreadRead(summary.category(), summary.createdAt(), summary.id(),
                summary.lastActivityAt(), summary.owner(), summary.ownerId(), posts,
                summary.replyCount(), summary.title(), summary.updatedAt());
    }

}
