package eu.royalblackwater.api.files.mapper;

import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.files.dto.StoredFileDto;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.Map;

public final class FileDtoMapper {
    private FileDtoMapper() { }

    public static StoredFileDto stored(Map<String, Object> row) {
        return new StoredFileDto(RowValues.longValue(row, "id"), RowValues.nullableLong(row, "owner_id"));
    }

    public static FileRead read(Map<String, Object> row) {
        long id = RowValues.longValue(row, "id");
        return new FileRead(RowValues.dateTime(row, "created_at"), id, RowValues.booleanValue(row, "is_public"),
                RowValues.requiredString(row, "mime_type"), RowValues.requiredString(row, "original_name"),
                RowValues.nullableLong(row, "owner_id"), "/api/files/" + id + "/content",
                RowValues.requiredString(row, "relative_path"), RowValues.longValue(row, "size_bytes"),
                RowValues.requiredString(row, "stored_name"), RowValues.requiredString(row, "usage_context"));
    }
}
