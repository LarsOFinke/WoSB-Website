package eu.royalblackwater.api.securityops;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SecuritySignalService {
    private final JdbcQueryService jdbc;
    private final Clock clock;
    public SecuritySignalService(JdbcQueryService jdbc,Clock clock){this.jdbc=jdbc;this.clock=clock;}

    @Transactional(propagation=Propagation.REQUIRES_NEW)
    public void record(String clientIp,String signal,String reason,String target){
        String ip=clientIp==null||clientIp.isBlank()?"unknown":clientIp.substring(0,Math.min(45,clientIp.length()));
        String safeReason=normalize(reason,32,"unknown");
        String safeTarget=normalize(target,180,"/");
        jdbc.update("""
                insert into security_signal_buckets(day,client_ip,signal,reason,request_target,event_count)
                values(:day,:ip,:signal,:reason,:target,1)
                on conflict(day,client_ip,signal,reason,request_target)
                do update set event_count=security_signal_buckets.event_count+1
                """,Map.of("day",LocalDate.ofInstant(clock.instant(),ZoneOffset.UTC),"ip",ip,"signal",signal,
                        "reason",safeReason,"target",safeTarget));
    }

    public void record(HttpServletRequest request,String signal,String reason){
        record(request.getRemoteAddr(),signal,reason,request.getRequestURI());
    }

    private static String normalize(String value,int limit,String fallback){
        String result=value==null||value.isBlank()?fallback:value.strip().replaceAll("[^a-zA-Z0-9_./:-]","_");
        return result.substring(0,Math.min(limit,result.length()));
    }
}
