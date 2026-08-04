package eu.royalblackwater.api.securityops;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.IpBlockCreate;
import eu.royalblackwater.api.contract.IpBlockRead;
import eu.royalblackwater.api.contract.IpBlockSummary;
import eu.royalblackwater.api.contract.IpBlockUnblock;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class IpBlockService {
    private final JdbcQueryService jdbc;
    private final AuditService audit;
    private final Clock clock;
    public IpBlockService(JdbcQueryService jdbc,AuditService audit,Clock clock){this.jdbc=jdbc;this.audit=audit;this.clock=clock;}

    @Transactional(readOnly=true)
    public boolean isBlocked(String rawIp){
        String ip=normalizeIp(rawIp,false);
        if(ip==null) return false;
        return jdbc.count("""
                select count(*) from ip_blocks where ip_address=:ip and unblocked_at is null
                  and (expires_at is null or expires_at>:now)
                """,Map.of("ip",ip,"now",now()))>0;
    }

    @Transactional(readOnly=true)
    public List<IpBlockRead> list(String status,String search,long limit){
        StringBuilder sql=new StringBuilder("select * from ip_blocks where 1=1");
        Map<String,Object> params=new LinkedHashMap<>();
        String normalized=status==null?"active":status.strip().toLowerCase();
        switch(normalized){
            case "active" -> sql.append(" and unblocked_at is null and (expires_at is null or expires_at>:now)");
            case "expired" -> sql.append(" and unblocked_at is null and expires_at<=:now");
            case "unblocked" -> sql.append(" and unblocked_at is not null");
            case "all" -> { }
            default -> throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Invalid IP-block status.");
        }
        if(!"all".equals(normalized)){params.put("now",now());}
        if(search!=null&&!search.isBlank()){sql.append(" and (ip_address ilike :search or reason ilike :search or coalesce(notes,'') ilike :search)");params.put("search","%"+search.strip()+"%");}
        sql.append(" order by created_at desc,id desc limit :limit");params.put("limit",Math.max(1,Math.min(1000,limit)));
        return jdbc.query(sql.toString(),params).stream().map(this::read).toList();
    }

    @Transactional(readOnly=true)
    public IpBlockSummary summary(){
        LocalDateTime now=now();
        return new IpBlockSummary(
                jdbc.count("select count(*) from ip_blocks where unblocked_at is null and (expires_at is null or expires_at>:now)",Map.of("now",now)),
                jdbc.count("select count(*) from ip_blocks where unblocked_at is null and expires_at<=:now",Map.of("now",now)),
                jdbc.count("select count(*) from ip_blocks where expires_at is null",Map.of()),
                jdbc.count("select count(*) from ip_blocks where expires_at is not null",Map.of()),
                jdbc.count("select count(*) from ip_blocks",Map.of()),
                jdbc.count("select count(*) from ip_blocks where unblocked_at is not null",Map.of()));
    }

    @Transactional
    public IpBlockRead create(AuthenticatedUser actor,IpBlockCreate input){
        String ip=normalizeIp(input.ipAddress(),true);
        if(input.expiresAt()!=null&&!input.expiresAt().isAfter(now())) throw new ResponseStatusException(CONFLICT,"Expiration must be in the future.");
        if(isBlocked(ip)) throw new ResponseStatusException(CONFLICT,"IP address is already actively blocked.");
        long id=jdbc.insertReturningId("""
                insert into ip_blocks(ip_address,reason,notes,created_at,created_by_user_id,created_by_username,expires_at)
                values(:ip,:reason,:notes,:now,:actorId,:actor,:expires) returning id
                """,SqlParameters.ofNullable("ip",ip,"reason",input.reason().strip(),"notes",blank(input.notes()),"now",now(),
                        "actorId",actor.id(),"actor",actor.username(),"expires",input.expiresAt()));
        audit.record(actor,"ip_block",id,"create","Blocked IP address "+ip,Set.of("reason","expires_at"));
        return required(id);
    }

    @Transactional
    public IpBlockRead unblock(AuthenticatedUser actor,long id,IpBlockUnblock input){
        Map<String,Object> row=jdbc.optional("select * from ip_blocks where id=:id",Map.of("id",id)).orElseThrow(()->new ResponseStatusException(NOT_FOUND,"IP block not found."));
        if(row.get("unblocked_at")!=null) return read(row);
        jdbc.update("""
                update ip_blocks set unblocked_at=:now,unblocked_by_user_id=:actorId,
                    unblocked_by_username=:actor,unblock_reason=:reason where id=:id
                """,SqlParameters.ofNullable("id",id,"now",now(),"actorId",actor.id(),"actor",actor.username(),"reason",blank(input.reason())));
        audit.record(actor,"ip_block",id,"unblock","Unblocked IP address",Set.of("unblock_reason"));
        return required(id);
    }

    private IpBlockRead required(long id){return read(jdbc.required("select * from ip_blocks where id=:id",Map.of("id",id)));}
    private IpBlockRead read(Map<String,Object> row){
        LocalDateTime expires=nullableDateTime(row,"expires_at");
        LocalDateTime unblocked=nullableDateTime(row,"unblocked_at");
        boolean expired=expires!=null&&!expires.isAfter(now());
        return new IpBlockRead(dateTime(row,"created_at"),nullableLong(row,"created_by_user_id"),requiredString(row,"created_by_username"),
                expires,longValue(row,"id"),requiredString(row,"ip_address"),unblocked==null&&!expired,expired,expires!=null,
                string(row,"notes"),requiredString(row,"reason"),string(row,"unblock_reason"),unblocked,
                nullableLong(row,"unblocked_by_user_id"),string(row,"unblocked_by_username"));
    }

    static String normalizeIp(String value,boolean required){
        if(value==null||value.isBlank()){if(required) throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"IP address is required.");return null;}
        String raw=value.strip();
        if(!raw.matches("[0-9a-fA-F:.]+")) throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Only literal IPv4 or IPv6 addresses may be blocked.");
        try{return InetAddress.getByName(raw).getHostAddress();}catch(UnknownHostException exception){throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"Invalid IP address.");}
    }
    private LocalDateTime now(){return LocalDateTime.ofInstant(clock.instant(),ZoneOffset.UTC);}
    private static String blank(String value){return value==null||value.isBlank()?null:value.strip();}
}
