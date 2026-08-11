package eu.royalblackwater.api.strategies.mapper;

import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.dto.StrategyRead;
import eu.royalblackwater.api.dto.StrategySummary;
import eu.royalblackwater.api.files.mapper.FileDtoMapper;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.Map;

public final class StrategyMapper {
    private StrategyMapper() { }

    public static StrategyRead read(Map<String, Object> row) {
        FileRead background = FileDtoMapper.read(row);
        return new StrategyRead(RowValues.longValue(row, "strategy_id"), RowValues.longValue(row, "owner_id"),
                RowValues.requiredString(row, "title"), RowValues.string(row, "description"),
                RowValues.requiredString(row, "overlay_json"), RowValues.booleanValue(row, "is_published"),
                RowValues.requiredString(row, "public_id"), background,
                RowValues.dateTime(row, "strategy_created_at"), RowValues.dateTime(row, "strategy_updated_at"),
                RowValues.nullableDateTime(row, "published_at"));
    }

    public static StrategySummary summary(Map<String, Object> row) {
        StrategyRead detail = read(row);
        return new StrategySummary(detail.id(), detail.title(), detail.description(), detail.isPublished(),
                detail.publicId(), detail.backgroundFile(), detail.createdAt(), detail.updatedAt());
    }
}
