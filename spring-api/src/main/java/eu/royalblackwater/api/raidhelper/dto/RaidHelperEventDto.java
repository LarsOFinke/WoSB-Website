package eu.royalblackwater.api.raidhelper.dto;

import java.time.LocalDateTime;

/** Typed event input for rendering a dynamic Raid-Helper JSON payload. */
public record RaidHelperEventDto(
        long eventId,
        String title,
        String category,
        String description,
        String location,
        LocalDateTime startAt,
        LocalDateTime endAt,
        boolean allDay,
        Long squadId,
        String squadName) {
}
