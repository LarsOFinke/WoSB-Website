package eu.royalblackwater.api.webhooks;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.*;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.FernetSecretBox;
import eu.royalblackwater.api.transport.ContractConversionService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.core.JacksonException;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

@Service
public class WebhookService {
    private static final TypeReference<List<String>> STRINGS=new TypeReference<>() { };
    private final JdbcQueryService jdbc;
    private final WebhookPolicy policy;
    private final WebhookHttpClient http;
    private final FernetSecretBox secrets;
    private final ObjectMapper json;
    private final ContractConversionService contracts;
    private final AuditService audit;
    private final Clock clock;

    public WebhookService(JdbcQueryService jdbc,WebhookPolicy policy,WebhookHttpClient http,FernetSecretBox secrets,
            ObjectMapper json,ContractConversionService contracts,AuditService audit,Clock clock){
        this.jdbc=jdbc;this.policy=policy;this.http=http;this.secrets=secrets;this.json=json;
        this.contracts=contracts;this.audit=audit;this.clock=clock;
    }

    @Transactional(readOnly=true)
    public List<OutboundWebhookRead> list(String purpose){
        String where="broadcast".equals(purpose)?" where broadcast_enabled=true":"";
        return jdbc.query("select * from outbound_webhooks"+where+" order by name,id",Map.of()).stream().map(this::read).toList();
    }

    @Transactional(readOnly=true)
    public OutboundWebhookSummary summary(String purpose){
        String filter="broadcast".equals(purpose)?" and broadcast_enabled=true":"";
        return new OutboundWebhookSummary(
                jdbc.count("select count(*) from outbound_webhooks where is_active=true"+filter,Map.of()),
                jdbc.count("select count(*) from outbound_webhook_deliveries where status='failed'",Map.of()),
                jdbc.count("select count(*) from outbound_webhooks where last_failure_at is not null and (last_success_at is null or last_failure_at>last_success_at)"+filter,Map.of()),
                jdbc.count("select count(*) from outbound_webhook_deliveries where status='delivered'",Map.of()),
                jdbc.count("select count(*) from outbound_webhooks where 1=1"+filter,Map.of()));
    }

    @Transactional
    public OutboundWebhookRead create(AuthenticatedUser actor,OutboundWebhookCreate input){
        WebhookPolicy.Scope scope=validatedScope(input.scopeType(),input.scopeId());
        List<String> events=policy.events(input.eventTypes(),value(input.broadcastEnabled(),false));
        long id=jdbc.insertReturningId("""
                insert into outbound_webhooks(name,endpoint_url,event_types_json,scope_type,scope_id,message_template,
                    discord_username,broadcast_enabled,is_active,created_at,updated_at,created_by_user_id,created_by_username)
                values(:name,:endpoint,:events,:scope,:scopeId,:template,:username,:broadcast,:active,:now,:now,:actorId,:actor) returning id
                """,SqlParameters.ofNullable("name",input.name().strip(),"endpoint",secrets.encrypt(policy.endpoint(input.endpointUrl())),
                        "events",write(events),"scope",scope.type(),"scopeId",scope.id(),"template",blank(input.messageTemplate()),
                        "username",blank(input.discordUsername()),"broadcast",value(input.broadcastEnabled(),false),
                        "active",value(input.isActive(),true),"now",now(),"actorId",actor.id(),"actor",actor.username()));
        audit.record(actor,"outbound_webhook",id,"create","Created outbound Discord webhook",Set.of("name","scope","event_types"));
        return requiredRead(id);
    }

    @Transactional
    public OutboundWebhookRead update(AuthenticatedUser actor,long id,OutboundWebhookUpdate input){
        Map<String,Object> current=required(id);
        WebhookPolicy.Scope scope=validatedScope(input.scopeType(),input.scopeId());
        boolean broadcast=value(input.broadcastEnabled(),false);
        List<String> events=policy.events(input.eventTypes(),broadcast);
        String encrypted=input.endpointUrl()==null||input.endpointUrl().isBlank()?requiredString(current,"endpoint_url")
                :secrets.encrypt(policy.endpoint(input.endpointUrl()));
        jdbc.update("""
                update outbound_webhooks set name=:name,endpoint_url=:endpoint,event_types_json=:events,scope_type=:scope,
                    scope_id=:scopeId,message_template=:template,discord_username=:username,broadcast_enabled=:broadcast,
                    is_active=:active,updated_at=:now where id=:id
                """,SqlParameters.ofNullable("id",id,"name",input.name().strip(),"endpoint",encrypted,"events",write(events),
                        "scope",scope.type(),"scopeId",scope.id(),"template",blank(input.messageTemplate()),
                        "username",blank(input.discordUsername()),"broadcast",broadcast,"active",value(input.isActive(),true),"now",now()));
        audit.record(actor,"outbound_webhook",id,"update","Updated outbound Discord webhook",Set.of("configuration"));
        return requiredRead(id);
    }

    @Transactional
    public void delete(AuthenticatedUser actor,long id){
        required(id);
        jdbc.update("delete from outbound_webhooks where id=:id",Map.of("id",id));
        audit.record(actor,"outbound_webhook",id,"delete","Deleted outbound Discord webhook",Set.of());
    }

    @Transactional
    public OutboundWebhookDeliveryRead test(AuthenticatedUser actor,long id,OutboundWebhookTestRequest input){
        Map<String,Object> webhook=required(id);
        String event=input.eventType()==null||input.eventType().isBlank()?"integration.test":input.eventType().strip();
        policy.events(List.of(event),false);
        String message="🧪 RBF webhook test by "+actor.username()+" · event `"+event+"`";
        return deliver(webhook,event,"integration",String.valueOf(id),message,blank(string(webhook,"discord_username")));
    }

    @Transactional
    public List<OutboundWebhookDeliveryRead> broadcast(AuthenticatedUser actor,OutboundWebhookBroadcastRequest input){
        List<OutboundWebhookDeliveryRead> deliveries=new ArrayList<>();
        for(Long id:input.webhookIds().stream().distinct().toList()){
            Map<String,Object> webhook=required(id);
            if(!booleanValue(webhook,"is_active")||!booleanValue(webhook,"broadcast_enabled"))
                throw new ResponseStatusException(org.springframework.http.HttpStatus.CONFLICT,"Selected webhook is not an active broadcast target.");
            deliveries.add(deliver(webhook,"integration.test","broadcast",UUID.randomUUID().toString(),input.message(),
                    blank(input.discordUsername())==null?blank(string(webhook,"discord_username")):blank(input.discordUsername())));
        }
        audit.record(actor,"outbound_webhook","broadcast","broadcast","Sent Discord broadcast",Set.of("message","targets"));
        return List.copyOf(deliveries);
    }

    @Transactional(readOnly=true)
    public List<OutboundWebhookDeliveryRead> deliveries(Long webhookId,String status,String eventType,long limit){
        StringBuilder sql=new StringBuilder("""
                select d.*,w.name webhook_name from outbound_webhook_deliveries d
                join outbound_webhooks w on w.id=d.webhook_id where 1=1
                """);
        Map<String,Object> params=new LinkedHashMap<>();
        if(webhookId!=null){sql.append(" and d.webhook_id=:webhook");params.put("webhook",webhookId);}
        if(status!=null&&!status.isBlank()){sql.append(" and d.status=:status");params.put("status",status.strip());}
        if(eventType!=null&&!eventType.isBlank()){sql.append(" and d.event_type=:event");params.put("event",eventType.strip());}
        sql.append(" order by d.created_at desc,d.id desc limit :limit");params.put("limit",Math.max(1,Math.min(1000,limit)));
        return jdbc.query(sql.toString(),params).stream().map(row->contracts.convert(row,OutboundWebhookDeliveryRead.class)).toList();
    }

    @Transactional
    public OutboundWebhookDeliveryRead retry(AuthenticatedUser actor,long deliveryId){
        Map<String,Object> row=jdbc.optional("""
                select d.*,w.name webhook_name,w.endpoint_url,w.discord_username from outbound_webhook_deliveries d
                join outbound_webhooks w on w.id=d.webhook_id where d.id=:id
                """,Map.of("id",deliveryId)).orElseThrow(()->notFound("Delivery"));
        WebhookHttpClient.Result result=send(requiredString(row,"endpoint_url"),requiredString(row,"payload_json"));
        updateDelivery(deliveryId,result);
        audit.record(actor,"outbound_webhook_delivery",deliveryId,"retry","Retried outbound webhook delivery",Set.of("status"));
        return delivery(deliveryId);
    }

    @Transactional
    public OutboundWebhookDeliveryDeleteResult deleteDelivery(AuthenticatedUser actor,long id){
        int count=jdbc.update("delete from outbound_webhook_deliveries where id=:id",Map.of("id",id));
        audit.record(actor,"outbound_webhook_delivery",id,"delete","Deleted webhook delivery history record",Set.of());
        return new OutboundWebhookDeliveryDeleteResult((long)count);
    }

    @Transactional
    public OutboundWebhookDeliveryDeleteResult deleteHistory(AuthenticatedUser actor,Long webhookId,String status,String eventType){
        StringBuilder sql=new StringBuilder("delete from outbound_webhook_deliveries where 1=1");
        Map<String,Object> params=new LinkedHashMap<>();
        if(webhookId!=null){sql.append(" and webhook_id=:webhook");params.put("webhook",webhookId);}
        if(status!=null&&!status.isBlank()){sql.append(" and status=:status");params.put("status",status.strip());}
        if(eventType!=null&&!eventType.isBlank()){sql.append(" and event_type=:event");params.put("event",eventType.strip());}
        int count=jdbc.update(sql.toString(),params);
        audit.record(actor,"outbound_webhook_delivery","history","delete","Deleted webhook delivery history",Set.of("filters"));
        return new OutboundWebhookDeliveryDeleteResult((long)count);
    }

    private OutboundWebhookDeliveryRead deliver(Map<String,Object> webhook,String event,String resourceType,String resourceId,
            String message,String username){
        String deliveryId=UUID.randomUUID().toString();
        Map<String,Object> payload=new LinkedHashMap<>();payload.put("content",message);
        if(username!=null) payload.put("username",username);
        String payloadJson=write(payload);
        long id=jdbc.insertReturningId("""
                insert into outbound_webhook_deliveries(webhook_id,delivery_id,event_type,resource_type,resource_id,payload_json,
                    status,attempts,created_at) values(:webhook,:delivery,:event,:type,:resource,:payload,'pending',0,:now) returning id
                """,Map.of("webhook",longValue(webhook,"id"),"delivery",deliveryId,"event",event,"type",resourceType,
                        "resource",resourceId,"payload",payloadJson,"now",now()));
        WebhookHttpClient.Result result=send(requiredString(webhook,"endpoint_url"),payloadJson);
        updateDelivery(id,result);
        return delivery(id);
    }

    private WebhookHttpClient.Result send(String storedEndpoint,String payload){
        String endpoint=policy.endpoint(secrets.decrypt(storedEndpoint));
        return http.send(endpoint,payload);
    }

    private void updateDelivery(long id,WebhookHttpClient.Result result){
        LocalDateTime timestamp=now();
        jdbc.update("""
                update outbound_webhook_deliveries set status=:status,attempts=attempts+1,response_status=:response,
                    response_body=:body,error_message=:error,last_attempt_at=:now,delivered_at=:delivered where id=:id
                """,SqlParameters.ofNullable("id",id,"status",result.success()?"delivered":"failed","response",result.status(),
                        "body",result.body(),"error",result.error(),"now",timestamp,"delivered",result.success()?timestamp:null));
        jdbc.update("""
                update outbound_webhooks set last_success_at=case when :success then :now else last_success_at end,
                    last_failure_at=case when :success then last_failure_at else :now end where id=(select webhook_id from outbound_webhook_deliveries where id=:id)
                """,Map.of("id",id,"success",result.success(),"now",timestamp));
    }

    private OutboundWebhookDeliveryRead delivery(long id){
        Map<String,Object> row=jdbc.optional("""
                select d.*,w.name webhook_name from outbound_webhook_deliveries d join outbound_webhooks w on w.id=d.webhook_id where d.id=:id
                """,Map.of("id",id)).orElseThrow(()->notFound("Delivery"));
        return contracts.convert(row,OutboundWebhookDeliveryRead.class);
    }

    private OutboundWebhookRead requiredRead(long id){return read(required(id));}
    private Map<String,Object> required(long id){return jdbc.optional("select * from outbound_webhooks where id=:id",Map.of("id",id)).orElseThrow(()->notFound("Webhook"));}
    private OutboundWebhookRead read(Map<String,Object> row){
        return new OutboundWebhookRead(booleanValue(row,"broadcast_enabled"),dateTime(row,"created_at"),requiredString(row,"created_by_username"),
                string(row,"discord_username"),policy.publicEndpoint(requiredString(row,"endpoint_url"),secrets),events(requiredString(row,"event_types_json")),
                longValue(row,"id"),booleanValue(row,"is_active"),nullableDateTime(row,"last_failure_at"),nullableDateTime(row,"last_success_at"),
                string(row,"message_template"),requiredString(row,"name"),nullableLong(row,"scope_id"),requiredString(row,"scope_type"),dateTime(row,"updated_at"));
    }

    private WebhookPolicy.Scope validatedScope(String type,Long id){
        WebhookPolicy.Scope scope=policy.scope(type,id);
        if("fleet".equals(scope.type())&&jdbc.count("select count(*) from fleets where id=:id",Map.of("id",scope.id()))==0) throw notFound("Fleet");
        if("squad".equals(scope.type())&&jdbc.count("select count(*) from squads where id=:id",Map.of("id",scope.id()))==0) throw notFound("Squad");
        return scope;
    }
    private List<String> events(String value){try{return json.readValue(value,STRINGS);}catch(JacksonException exception){return List.of();}}
    private String write(Object value){try{return json.writeValueAsString(value);}catch(JacksonException exception){throw new IllegalStateException("Could not serialize webhook data",exception);}}
    private LocalDateTime now(){return LocalDateTime.ofInstant(clock.instant(),ZoneOffset.UTC);}
    private static <T>T value(T value,T fallback){return value==null?fallback:value;}
    private static String blank(String value){return value==null||value.isBlank()?null:value.strip();}
    private static ResponseStatusException notFound(String subject){return new ResponseStatusException(NOT_FOUND,subject+" not found.");}
}
