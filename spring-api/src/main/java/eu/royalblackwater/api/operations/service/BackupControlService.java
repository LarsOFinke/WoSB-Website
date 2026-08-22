package eu.royalblackwater.api.operations.service;

import eu.royalblackwater.api.operations.mapper.OperationsDtoMapper;
import eu.royalblackwater.api.operations.repository.ControlFileStore;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.BackupConfigurationRequest;
import eu.royalblackwater.api.dto.BackupControlRequestResult;
import eu.royalblackwater.api.dto.BackupControlStatus;
import eu.royalblackwater.api.dto.BackupDiscoveryRequest;
import eu.royalblackwater.api.dto.BackupEnrollmentResponseRequest;
import eu.royalblackwater.api.dto.DatabaseRestoreRequest;
import eu.royalblackwater.api.dto.FilesRestoreRequest;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.core.JacksonException;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class BackupControlService {
    private static final Set<String> ACTIVE=Set.of("queued","running");
    private static final Pattern HOST=Pattern.compile("^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$");
    private static final Pattern USER=Pattern.compile("^[A-Za-z0-9._-]{1,64}$");
    private static final Pattern HOST_KEY=Pattern.compile("^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$");
    private static final Pattern BACKUP_ID=Pattern.compile("^[a-f0-9]{64}$");
    private static final Pattern TOKEN=Pattern.compile("^[A-Za-z0-9_-]{24,128}$");
    private static final Set<String> COMPONENTS=Set.of("uploads","certs","letsencrypt");
    private static final TypeReference<Map<String,Object>> MAP=new TypeReference<>() { };
    private final ControlFileStore files;
    private final OperationsDtoMapper mapper;
    private final ObjectMapper json;
    private final AuditService audit;
    private final Clock clock;

    public BackupControlService(ControlFileStore files, OperationsDtoMapper mapper, ObjectMapper json,
            AuditService audit, Clock clock) {
        this.files = files;
        this.mapper = mapper;
        this.json = json;
        this.audit = audit;
        this.clock = clock;
    }

    public BackupControlStatus status(){
        Map<String,Object> status=new LinkedHashMap<>(files.readStatus("backup-status.json"));
        Map<String,Object> request=files.readRequest("backup.request");boolean requestExists=files.requestExists("backup.request");
        String state=text(status.get("state"),"idle");
        if(stale(state,status,requestExists,Duration.ofMinutes(5),Duration.ofMinutes(10))){
            state="failed";status.put("state",state);status.put("message","The previous backup operation stopped reporting a host-runner heartbeat.");status.put("finished_at",now());
        }
        if(!request.isEmpty()&&!ACTIVE.contains(state)){
            state="queued";status.put("state",state);status.put("operation",text(request.get("operation"),"backup"));
            status.put("message","Backup request accepted and waiting for the host runner.");
            status.put("requested_by",request.get("requested_by"));status.put("requested_at",request.get("requested_at"));
            status.put("started_at",null);status.put("finished_at",null);
        }
        if(ACTIVE.contains(state)&&"prepare_enrollment".equals(status.get("operation"))){
            status.put("enrollment_request",null);status.put("enrollment_id",null);status.put("enrollment_public_key",null);
        }
        status.putIfAbsent("state",state);status.putIfAbsent("operation","backup");status.putIfAbsent("message","No backup operation has been requested yet.");
        status.putIfAbsent("connection",Map.of());status.putIfAbsent("artifacts",List.of());status.putIfAbsent("local_database_backups",List.of());status.putIfAbsent("local_files_backups",List.of());
        status.put("request_available",!requestExists&&!ACTIVE.contains(state));
        return mapper.backupStatus(status);
    }

    public BackupControlRequestResult prepareKey(AuthenticatedUser actor,String capability){return request(actor,"prepare_key",Map.of(),"upload_key_prepared",capability);}
    public BackupControlRequestResult prepareEnrollment(AuthenticatedUser actor,String capability){return request(actor,"prepare_enrollment",Map.of(),"enrollment_prepared",capability);}
    public BackupControlRequestResult discover(AuthenticatedUser actor,BackupDiscoveryRequest input,String capability){
        String host=host(input.host());long port=input.port()==null?22:input.port();
        return request(actor,"discover",Map.of("host",host,"port",port),"discover_requested",capability);
    }
    public BackupControlRequestResult configure(AuthenticatedUser actor,BackupConfigurationRequest input,String capability){
        String host=host(input.host());String username=input.username().strip();
        if(!USER.matcher(username).matches())throw bad("Invalid SSH username.");
        String remote=input.remoteDirectory().strip();if(!remote.startsWith("/")||remote.contains("..")||!remote.matches("/[A-Za-z0-9._/-]+"))throw bad("Invalid remote backup directory.");
        String key=input.hostKey().strip();if(!HOST_KEY.matcher(key).matches())throw bad("Invalid SSH host key.");
        String privateKey=input.privateKey();if(privateKey!=null&&privateKey.length()>32768)throw bad("Private key is too large.");
        Map<String,Object> payload=new LinkedHashMap<>();payload.put("host",host);payload.put("port",input.port()==null?22:input.port());
        payload.put("username",username);payload.put("remote_directory",remote);payload.put("host_key",key);
        if(privateKey!=null&&!privateKey.isBlank())payload.put("private_key",privateKey.strip());
        return request(actor,"configure",payload,"configuration_requested",capability);
    }
    public BackupControlRequestResult deleteConfiguration(AuthenticatedUser actor,String capability){return request(actor,"delete_configuration",Map.of(),"delete_requested",capability);}
    public BackupControlRequestResult test(AuthenticatedUser actor,String capability){return request(actor,"test",Map.of(),"test_requested",capability);}
    public BackupControlRequestResult run(AuthenticatedUser actor,String capability){return request(actor,"backup",Map.of(),"backup_requested",capability);}
    public BackupControlRequestResult scan(AuthenticatedUser actor,String capability){return request(actor,"scan_local_backups",Map.of(),"catalog_scan_requested",capability);}

    public BackupControlRequestResult applyEnrollment(AuthenticatedUser actor,BackupEnrollmentResponseRequest input,String capability){
        Map<String,Object> response;
        try{response=json.readValue(input.responseJson(),MAP);}catch(JacksonException exception){throw bad("Enrollment response must contain valid JSON.");}
        Object request=status().enrollmentRequest();String expected=request instanceof Map<?,?> map?String.valueOf(map.get("enrollment_id")):"";
        if(expected.isBlank())throw conflict("Create a fresh enrollment request before importing a response.");
        if(!expected.equals(String.valueOf(response.get("enrollment_id"))))throw conflict("Enrollment response does not belong to the active request.");
        return request(actor,"apply_enrollment",Map.of("response_json",input.responseJson()),"enrollment_apply_requested",capability);
    }

    public BackupControlRequestResult restoreDatabase(AuthenticatedUser actor,DatabaseRestoreRequest input){
        requireBootstrap(actor);validateRestore(input.backupId(),input.approvalToken(),input.confirmation(),"RESTORE DATABASE");
        return request(actor,"restore_postgresql",Map.of("backup_id",input.backupId().toLowerCase(),
                "approval_token_sha256",sha256(input.approvalToken().strip())),"restore_requested");
    }
    public BackupControlRequestResult restoreFiles(AuthenticatedUser actor,FilesRestoreRequest input){
        requireBootstrap(actor);validateRestore(input.backupId(),input.approvalToken(),input.confirmation(),"RESTORE FILES");
        List<String> components=input.components().stream().map(String::strip).distinct().sorted().toList();
        if(components.size()!=input.components().size()||!COMPONENTS.containsAll(components))throw bad("Invalid or duplicate file-restore components.");
        return request(actor,"restore_files",Map.of("backup_id",input.backupId().toLowerCase(),"components",components,
                "approval_token_sha256",sha256(input.approvalToken().strip())),"restore_requested");
    }

    private BackupControlRequestResult request(AuthenticatedUser actor,String operation,Map<String,Object> values,String action){
        BackupControlStatus current=status();
        if(files.requestExists("backup.request")||ACTIVE.contains(current.state()))throw conflict("A backup operation is already queued or running.");
        Map<String,Object> payload=new LinkedHashMap<>();payload.put("requested_by",actor.username());payload.put("requested_at",now());payload.put("operation",operation);payload.putAll(values);
        try{files.publishRequest("backup.request",payload);}catch(ControlFileStore.ControlConflictException exception){throw conflict(exception.getMessage());}
        audit.record(actor,"backup_control",operation,action,"Requested host backup operation: "+operation,Set.of("operation"));
        return mapper.backupRequest(true, status());
    }

    private BackupControlRequestResult request(AuthenticatedUser actor,String operation,Map<String,Object> values,String action,String capability){
        String token=capability==null?"":capability.strip();
        if(!TOKEN.matcher(token).matches())throw bad("Enter a valid one-time host approval token.");
        Map<String,Object> protectedValues=new LinkedHashMap<>(values);
        protectedValues.put("host_capability_sha256",sha256(token));
        return request(actor,operation,protectedValues,action);
    }

    private boolean stale(String state,Map<String,Object> payload,boolean requestExists,Duration running,Duration queued){
        Instant reference;
        if("running".equals(state)){reference=parse(payload.get("heartbeat_at"));if(reference==null)reference=parse(payload.get("started_at"));return reference==null||Duration.between(reference,clock.instant()).compareTo(running)>0;}
        if("queued".equals(state)&&!requestExists){reference=parse(payload.get("requested_at"));return reference==null||Duration.between(reference,clock.instant()).compareTo(queued)>0;}
        return false;
    }
    private static void validateRestore(String backupId,String approval,String confirmation,String expected){
        if(!BACKUP_ID.matcher(backupId.strip().toLowerCase()).matches())throw bad("Select a valid host-generated backup.");
        if(!TOKEN.matcher(approval.strip()).matches())throw bad("Enter the one-time host approval token.");
        if(!expected.equals(confirmation))throw bad("Restore confirmation phrase is invalid.");
    }
    private static String host(String value){String host=value.strip();if(!HOST.matcher(host).matches()||host.equalsIgnoreCase("localhost")||host.endsWith(".local"))throw bad("Invalid public backup host.");return host;}
    private static void requireBootstrap(AuthenticatedUser actor){if(!actor.canGrantAdmin())throw new ResponseStatusException(FORBIDDEN,"Bootstrap administrator required.");}
    private String now(){return clock.instant().toString();}
    private static Instant parse(Object value){if(!(value instanceof String text)||text.isBlank())return null;try{return Instant.parse(text.replace("+00:00","Z"));}catch(DateTimeParseException exception){return null;}}
    private static String text(Object value,String fallback){return value==null||String.valueOf(value).isBlank()?fallback:String.valueOf(value);}
    private static String sha256(String value){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));}catch(Exception exception){throw new IllegalStateException(exception);}}
    private static ResponseStatusException bad(String value){return new ResponseStatusException(BAD_REQUEST,value);}
    private static ResponseStatusException conflict(String value){return new ResponseStatusException(CONFLICT,value);}
}
