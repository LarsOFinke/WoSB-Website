package eu.royalblackwater.api.securityops.service;

import eu.royalblackwater.api.dto.SecurityDashboard;
import eu.royalblackwater.api.dto.SecurityDayBucket;
import eu.royalblackwater.api.dto.SecurityIpRow;
import eu.royalblackwater.api.dto.SecurityReasonBreakdown;
import eu.royalblackwater.api.securityops.mapper.SecurityOperationsDtoMapper;
import eu.royalblackwater.api.securityops.repository.SecurityOperationsRepository;
import eu.royalblackwater.api.securityops.repository.queries.SecurityDashboardQueries;
import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.date;

@Service
public class SecurityDashboardService {
    private static final Map<String,Integer> WEIGHTS=Map.of("reconnaissance",25,"login_failure",6,"rate_limit",15);
    private final SecurityOperationsRepository repository;
    private final Clock clock;
    public SecurityDashboardService(SecurityOperationsRepository repository,Clock clock){this.repository=repository;this.clock=clock;}

    @Transactional(readOnly=true)
    public SecurityDashboard build(LocalDate from,LocalDate to,String threatLevel,String clientIp,String sort,long limit){
        LocalDate today=LocalDate.ofInstant(clock.instant(),ZoneOffset.UTC);
        LocalDate effectiveTo=to==null?today:to.isAfter(today)?today:to;
        LocalDate effectiveFrom=from==null?effectiveTo.minusDays(6):from;
        if(effectiveFrom.isAfter(effectiveTo)){LocalDate swap=effectiveFrom;effectiveFrom=effectiveTo;effectiveTo=swap;}
        if(effectiveFrom.isBefore(effectiveTo.minusDays(29))) effectiveFrom=effectiveTo.minusDays(29);
        List<Map<String,Object>> rows=repository.query(SecurityDashboardQueries.BUILD_SELECT_01,Map.of("from",effectiveFrom,"to",effectiveTo));
        List<SecurityIpRow> all=ipRows(rows);
        Map<String,Long> threatCounts=new LinkedHashMap<>();for(String level:List.of("low","guarded","elevated","critical")) threatCounts.put(level,0L);
        for(SecurityIpRow row:all) threatCounts.computeIfPresent(row.threatLevel(),(key,value)->value+1);
        List<SecurityIpRow> visible=new ArrayList<>(all);
        if(threatLevel!=null&&!threatLevel.isBlank()) visible.removeIf(row->!row.threatLevel().equals(threatLevel));
        sort(visible,sort);
        List<SecurityIpRow> metrics=clientIp==null||clientIp.isBlank()?visible:visible.stream().filter(row->row.clientIp().equals(clientIp.strip())).toList();
        java.util.Set<String> allowed=metrics.stream().map(SecurityIpRow::clientIp).collect(java.util.stream.Collectors.toSet());
        List<Map<String,Object>> filtered=rows.stream().filter(row->allowed.contains(requiredString(row,"client_ip"))).toList();
        Map<String,Long> signals=new LinkedHashMap<>();for(String signal:WEIGHTS.keySet()) signals.put(signal,0L);
        for(Map<String,Object> row:filtered) signals.computeIfPresent(requiredString(row,"signal"),(key,value)->value+longValue(row,"event_count"));
        long score=metrics.stream().mapToLong(SecurityIpRow::threatScore).max().orElse(0);
        return SecurityOperationsDtoMapper.dashboard(days(filtered,effectiveFrom,effectiveTo),
                visible.stream().limit(Math.max(1,Math.min(1000,limit))).toList(), signals, threatCounts,
                level(score), score, filtered.stream().mapToLong(row->longValue(row,"event_count")).sum(),
                metrics.size());
    }

    private List<SecurityIpRow> ipRows(List<Map<String,Object>> rows){
        Map<String,IpAccumulator> grouped=new LinkedHashMap<>();
        for(Map<String,Object> row:rows){
            String ip=requiredString(row,"client_ip");
            IpAccumulator item=grouped.computeIfAbsent(ip,ignored->new IpAccumulator());
            String signal=requiredString(row,"signal");long count=longValue(row,"event_count");
            item.signals.merge(signal,count,Long::sum);
            String reason=requiredString(row,"reason");String target=requiredString(row,"request_target");
            item.reasons.merge(signal+"\u0000"+reason+"\u0000"+target,count,Long::sum);
            LocalDate day=date(row,"day");item.first=item.first==null||day.isBefore(item.first)?day:item.first;item.last=item.last==null||day.isAfter(item.last)?day:item.last;
        }
        List<SecurityIpRow> result=new ArrayList<>();
        for(Map.Entry<String,IpAccumulator> entry:grouped.entrySet()){
            IpAccumulator item=entry.getValue();long reconnaissance=item.signals.getOrDefault("reconnaissance",0L);
            long login=item.signals.getOrDefault("login_failure",0L);long rate=item.signals.getOrDefault("rate_limit",0L);
            long volume=Math.min(Math.max(reconnaissance+login+rate-3,0)*2,20);long score=Math.min(100,reconnaissance*25+login*6+rate*15+volume);
            List<SecurityReasonBreakdown> reasons=item.reasons.entrySet().stream().sorted(Map.Entry.<String,Long>comparingByValue().reversed())
                    .map(value->{String[] parts=value.getKey().split("\\u0000",-1);return SecurityOperationsDtoMapper.reason(value.getValue(),parts[1],parts[2],parts[0]);}).toList();
            result.add(SecurityOperationsDtoMapper.ipRow(entry.getKey(), reconnaissance+login+rate, item.first,
                    item.last, login*6, login, rate*15, rate, reasons, reconnaissance, reconnaissance*25,
                    level(score), score, volume));
        }
        return result;
    }

    private List<SecurityDayBucket> days(List<Map<String,Object>> rows,LocalDate from,LocalDate to){
        Map<LocalDate,DayAccumulator> grouped=new HashMap<>();
        for(Map<String,Object> row:rows){
            LocalDate day=date(row,"day");DayAccumulator item=grouped.computeIfAbsent(day,ignored->new DayAccumulator());
            long count=longValue(row,"event_count");item.total+=count;item.ips.add(requiredString(row,"client_ip"));item.signals.merge(requiredString(row,"signal"),count,Long::sum);
        }
        List<SecurityDayBucket> result=new ArrayList<>();
        for(LocalDate day=from;!day.isAfter(to);day=day.plusDays(1)){
            DayAccumulator item=grouped.getOrDefault(day,new DayAccumulator());
            result.add(SecurityOperationsDtoMapper.dayBucket(day, item.signals.getOrDefault("login_failure",0L),
                    item.signals.getOrDefault("rate_limit",0L), item.signals.getOrDefault("reconnaissance",0L),
                    item.total, item.ips.size()));
        }
        return result;
    }

    private static void sort(List<SecurityIpRow> rows,String raw){
        String sort=raw==null?"threat":raw;
        Comparator<SecurityIpRow> comparator=switch(sort){
            case "events" -> Comparator.comparingLong(SecurityIpRow::eventCount).thenComparingLong(SecurityIpRow::threatScore);
            case "last_seen" -> Comparator.comparing(SecurityIpRow::lastSeen).thenComparingLong(SecurityIpRow::threatScore);
            case "ip" -> Comparator.comparing(SecurityIpRow::clientIp);
            default -> Comparator.comparingLong(SecurityIpRow::threatScore).thenComparingLong(SecurityIpRow::reconnaissance).thenComparingLong(SecurityIpRow::eventCount);
        };
        rows.sort("ip".equals(sort)?comparator:comparator.reversed());
    }
    private static String level(long score){if(score>=70)return"critical";if(score>=45)return"elevated";if(score>=20)return"guarded";return"low";}
    private static final class IpAccumulator{final Map<String,Long>signals=new HashMap<>();final Map<String,Long>reasons=new HashMap<>();LocalDate first;LocalDate last;}
    private static final class DayAccumulator{final Map<String,Long>signals=new HashMap<>();final java.util.Set<String>ips=new LinkedHashSet<>();long total;}
}
