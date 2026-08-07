package eu.royalblackwater.api.securityops.mapper;

import eu.royalblackwater.api.dto.IpBlockRead;
import eu.royalblackwater.api.dto.IpBlockSummary;
import eu.royalblackwater.api.dto.SecurityDashboard;
import eu.royalblackwater.api.dto.SecurityDayBucket;
import eu.royalblackwater.api.dto.SecurityIpRow;
import eu.royalblackwater.api.dto.SecurityReasonBreakdown;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.nullableLong;
import static eu.royalblackwater.api.persistence.RowValues.string;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.dateTime;
import static eu.royalblackwater.api.persistence.RowValues.nullableDateTime;

public final class SecurityOperationsDtoMapper {
    private SecurityOperationsDtoMapper() { }

    public static SecurityDashboard dashboard(List<SecurityDayBucket> days, List<SecurityIpRow> ips,
                                              Map<String, Long> signalCounts,
                                              Map<String, Long> threatCounts, String threatLevel,
                                              long threatScore, long totalEvents, long uniqueIps) {
        return new SecurityDashboard(days, ips, signalCounts, threatCounts, threatLevel, threatScore,
                totalEvents, uniqueIps);
    }

    public static SecurityReasonBreakdown reason(long eventCount, String reason, String requestTarget,
                                                 String signal) {
        return new SecurityReasonBreakdown(eventCount, reason, requestTarget, signal);
    }

    public static SecurityIpRow ipRow(String clientIp, long eventCount, LocalDate firstSeen, LocalDate lastSeen,
                                      long loginFailurePoints, long loginFailures, long rateLimitPoints,
                                      long rateLimits, List<SecurityReasonBreakdown> reasons, long reconnaissance,
                                      long reconnaissancePoints, String threatLevel, long threatScore,
                                      long volumeBonus) {
        return new SecurityIpRow(clientIp, eventCount, firstSeen, lastSeen, loginFailurePoints, loginFailures,
                rateLimitPoints, rateLimits, reasons, reconnaissance, reconnaissancePoints, threatLevel,
                threatScore, volumeBonus);
    }

    public static SecurityDayBucket dayBucket(LocalDate day, long loginFailures, long rateLimits,
                                              long reconnaissance, long totalEvents, long uniqueIps) {
        return new SecurityDayBucket(day, loginFailures, rateLimits, reconnaissance, totalEvents, uniqueIps);
    }

    public static IpBlockRead ipBlock(Map<String, Object> row, LocalDateTime now) {
        LocalDateTime expires = nullableDateTime(row, "expires_at");
        LocalDateTime unblocked = nullableDateTime(row, "unblocked_at");
        boolean expired = expires != null && !expires.isAfter(now);
        return new IpBlockRead(dateTime(row, "created_at"), nullableLong(row, "created_by_user_id"),
                requiredString(row, "created_by_username"), expires, longValue(row, "id"),
                requiredString(row, "ip_address"), unblocked == null && !expired, expired, expires != null,
                string(row, "notes"), requiredString(row, "reason"), string(row, "unblock_reason"),
                unblocked, nullableLong(row, "unblocked_by_user_id"), string(row, "unblocked_by_username"));
    }
    public static IpBlockSummary summary(long active, long expired, long unblocked,
            long createdToday, long createdWeek, long total) {
        return new IpBlockSummary(active, expired, unblocked, createdToday, createdWeek, total);
    }

}
