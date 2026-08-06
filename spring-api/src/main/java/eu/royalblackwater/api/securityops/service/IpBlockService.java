package eu.royalblackwater.api.securityops.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.IpBlockCreate;
import eu.royalblackwater.api.dto.IpBlockRead;
import eu.royalblackwater.api.dto.IpBlockSummary;
import eu.royalblackwater.api.dto.IpBlockUnblock;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.securityops.mapper.SecurityOperationsDtoMapper;
import eu.royalblackwater.api.securityops.repository.SecurityOperationsRepository;
import eu.royalblackwater.api.securityops.repository.queries.IpBlockQueries;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class IpBlockService {
    private final SecurityOperationsRepository repository;
    private final AuditService audit;
    private final Clock clock;
    public IpBlockService(SecurityOperationsRepository repository,AuditService audit,Clock clock){this.repository=repository;this.audit=audit;this.clock=clock;}

    @Transactional(readOnly=true)
    public boolean isBlocked(String rawIp){
        String ip=normalizeIp(rawIp,false);
        if(ip==null) return false;
        return repository.count(IpBlockQueries.IS_BLOCKED_SELECT_01,Map.of("ip",ip,"now",now()))>0;
    }

    @Transactional(readOnly=true)
    public List<IpBlockRead> list(String status,String search,long limit){
        StringBuilder sql=new StringBuilder(IpBlockQueries.LIST_SELECT_01);
        Map<String,Object> params=new LinkedHashMap<>();
        String normalized=status==null?"active":status.strip().toLowerCase();
        switch(normalized){
            case "active" -> sql.append(IpBlockQueries.LIST_AND_01);
            case "expired" -> sql.append(IpBlockQueries.LIST_AND_02);
            case "unblocked" -> sql.append(IpBlockQueries.LIST_AND_03);
            case "all" -> { }
            default -> throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Invalid IP-block status.");
        }
        if(!"all".equals(normalized)){params.put("now",now());}
        if(search!=null&&!search.isBlank()){sql.append(IpBlockQueries.LIST_AND_04);params.put("search","%"+search.strip()+"%");}
        sql.append(IpBlockQueries.LIST_ORDER_BY_01);params.put("limit",Math.max(1,Math.min(1000,limit)));
        return repository.query(sql.toString(),params).stream().map(row -> SecurityOperationsDtoMapper.ipBlock(row, now())).toList();
    }

    @Transactional(readOnly=true)
    public IpBlockSummary summary(){
        LocalDateTime now=now();
        return SecurityOperationsDtoMapper.summary(
                repository.count(IpBlockQueries.SUMMARY_SELECT_01,Map.of("now",now)),
                repository.count(IpBlockQueries.SUMMARY_SELECT_02,Map.of("now",now)),
                repository.count(IpBlockQueries.SUMMARY_SELECT_03,Map.of()),
                repository.count(IpBlockQueries.SUMMARY_SELECT_04,Map.of()),
                repository.count(IpBlockQueries.SUMMARY_SELECT_05,Map.of()),
                repository.count(IpBlockQueries.SUMMARY_SELECT_06,Map.of()));
    }

    @Transactional
    public IpBlockRead create(AuthenticatedUser actor,IpBlockCreate input){
        String ip=normalizeIp(input.ipAddress(),true);
        if(input.expiresAt()!=null&&!input.expiresAt().isAfter(now())) throw new ResponseStatusException(CONFLICT,"Expiration must be in the future.");
        if(isBlocked(ip)) throw new ResponseStatusException(CONFLICT,"IP address is already actively blocked.");
        long id=repository.insertReturningId(IpBlockQueries.CREATE_INSERT_01,SqlParameters.ofNullable("ip",ip,"reason",input.reason().strip(),"notes",blank(input.notes()),"now",now(),
                        "actorId",actor.id(),"actor",actor.username(),"expires",input.expiresAt()));
        audit.record(actor,"ip_block",id,"create","Blocked IP address "+ip,Set.of("reason","expires_at"));
        return required(id);
    }

    @Transactional
    public IpBlockRead unblock(AuthenticatedUser actor,long id,IpBlockUnblock input){
        Map<String,Object> row=repository.optional(IpBlockQueries.UNBLOCK_SELECT_01,Map.of("id",id)).orElseThrow(()->new ResponseStatusException(NOT_FOUND,"IP block not found."));
        if(row.get("unblocked_at")!=null) return SecurityOperationsDtoMapper.ipBlock(row, now());
        repository.update(IpBlockQueries.UNBLOCK_UPDATE_01,SqlParameters.ofNullable("id",id,"now",now(),"actorId",actor.id(),"actor",actor.username(),"reason",blank(input.reason())));
        audit.record(actor,"ip_block",id,"unblock","Unblocked IP address",Set.of("unblock_reason"));
        return required(id);
    }

    private IpBlockRead required(long id){return SecurityOperationsDtoMapper.ipBlock(repository.required(IpBlockQueries.UNBLOCK_SELECT_01,Map.of("id",id)), now());}

    static String normalizeIp(String value,boolean required){
        if(value==null||value.isBlank()){if(required) throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"IP address is required.");return null;}
        String raw=value.strip();
        if(!raw.matches("[0-9a-fA-F:.]+")) throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Only literal IPv4 or IPv6 addresses may be blocked.");
        try{return InetAddress.getByName(raw).getHostAddress();}catch(UnknownHostException exception){throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Invalid IP address.");}
    }
    private LocalDateTime now(){return LocalDateTime.ofInstant(clock.instant(),ZoneOffset.UTC);}
    private static String blank(String value){return value==null||value.isBlank()?null:value.strip();}
}
