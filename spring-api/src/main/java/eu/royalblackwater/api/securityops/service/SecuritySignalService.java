package eu.royalblackwater.api.securityops.service;

import eu.royalblackwater.api.securityops.repository.SecurityOperationsRepository;
import eu.royalblackwater.api.securityops.repository.queries.SecuritySignalQueries;
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
    private final SecurityOperationsRepository repository;
    private final Clock clock;
    public SecuritySignalService(SecurityOperationsRepository repository,Clock clock){this.repository=repository;this.clock=clock;}

    @Transactional(propagation=Propagation.REQUIRES_NEW)
    public void record(String clientIp,String signal,String reason,String target){
        String ip=clientIp==null||clientIp.isBlank()?"unknown":clientIp.substring(0,Math.min(45,clientIp.length()));
        String safeReason=normalize(reason,32,"unknown");
        String safeTarget=normalize(target,180,"/");
        repository.update(SecuritySignalQueries.RECORD_INSERT_01,Map.of("day",LocalDate.ofInstant(clock.instant(),ZoneOffset.UTC),"ip",ip,"signal",signal,
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
