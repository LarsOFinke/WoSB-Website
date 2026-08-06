package eu.royalblackwater.api.operations.service;

import eu.royalblackwater.api.operations.mapper.OperationsDtoMapper;
import eu.royalblackwater.api.operations.repository.ControlFileStore;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.SystemUpdateRequestResult;
import eu.royalblackwater.api.dto.SystemUpdateStatus;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class SystemUpdateService {
    private static final Set<String> ACTIVE=Set.of("queued","running");
    private static final Set<String> OPERATIONS=Set.of("update","restart","rollback");
    private final ControlFileStore files;
    private final AuditService audit;
    private final OperationsDtoMapper mapper;
    private final Clock clock;

    public SystemUpdateService(ControlFileStore files, AuditService audit, OperationsDtoMapper mapper, Clock clock) {
        this.files = files;
        this.audit = audit;
        this.mapper = mapper;
        this.clock = clock;
    }

    public SystemUpdateStatus status(){
        Map<String,Object> status=new LinkedHashMap<>(files.readStatus("update-status.json"));
        Map<String,Object> request=files.readRequest("update.request");boolean requestExists=files.requestExists("update.request");
        String state=text(status.get("state"),"idle");
        if(stale(state,status,requestExists)){
            state="failed";status.put("state",state);status.put("finished_at",clock.instant().toString());
        }
        if(!request.isEmpty()&&!ACTIVE.contains(state)){
            state="queued";status.put("operation",text(request.get("operation"),"update"));
            status.put("requested_at",request.get("requested_at"));status.put("started_at",null);status.put("finished_at",null);
        }
        String operation=text(status.get("operation"),"update");
        return mapper.systemUpdateStatus(string(status.get("finished_at")), publicMessage(state, operation), operation,
                !requestExists && !ACTIVE.contains(state), string(status.get("requested_at")),
                string(status.get("started_at")), state);
    }

    public SystemUpdateRequestResult request(AuthenticatedUser actor,String rawOperation){
        String operation=rawOperation==null||rawOperation.isBlank()?"update":rawOperation.strip().toLowerCase();
        if(!OPERATIONS.contains(operation))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Operation must be update, restart, or rollback.");
        SystemUpdateStatus current=status();
        if(files.requestExists("update.request")||ACTIVE.contains(current.state()))throw new ResponseStatusException(HttpStatus.CONFLICT,"A server operation is already queued or running.");
        Map<String,Object> payload=Map.of("requested_by",actor.username(),"requested_at",clock.instant().toString(),"operation",operation);
        try{files.publishRequest("update.request",payload);}catch(ControlFileStore.ControlConflictException exception){throw new ResponseStatusException(HttpStatus.CONFLICT,exception.getMessage());}
        audit.record(actor,"system_update",operation,"request","Requested host operation: "+operation,Set.of("operation"));
        return mapper.systemUpdateRequest(true, status());
    }

    private boolean stale(String state,Map<String,Object> payload,boolean requestExists){
        if("running".equals(state)){
            Instant reference=parse(payload.get("heartbeat_at"));if(reference==null)reference=parse(payload.get("started_at"));
            return reference==null||Duration.between(reference,clock.instant()).compareTo(Duration.ofMinutes(3))>0;
        }
        if("queued".equals(state)&&!requestExists){Instant reference=parse(payload.get("requested_at"));return reference==null||Duration.between(reference,clock.instant()).compareTo(Duration.ofMinutes(10))>0;}
        return false;
    }
    private static String publicMessage(String state,String operation){
        String subject="restart".equals(operation)?"server restart":"artifact "+operation;
        return switch(state){case"queued"->"The "+subject+" is queued for the host runner.";case"running"->"The "+subject+" is running.";
            case"succeeded"->"The "+subject+" completed successfully.";case"failed"->"The "+subject+" failed; review host logs.";default->"No server operation has been requested yet.";};
    }
    private static Instant parse(Object value){if(!(value instanceof String text)||text.isBlank())return null;try{return Instant.parse(text.replace("+00:00","Z"));}catch(DateTimeParseException exception){return null;}}
    private static String text(Object value,String fallback){String result=string(value);return result==null||result.isBlank()?fallback:result;}
    private static String string(Object value){return value==null?null:String.valueOf(value);}
}
