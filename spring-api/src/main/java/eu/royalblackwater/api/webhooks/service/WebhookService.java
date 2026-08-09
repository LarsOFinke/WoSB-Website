package eu.royalblackwater.api.webhooks.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.OutboundWebhookBroadcastRequest;
import eu.royalblackwater.api.dto.OutboundWebhookCreate;
import eu.royalblackwater.api.dto.OutboundWebhookDeliveryDeleteResult;
import eu.royalblackwater.api.dto.OutboundWebhookDeliveryRead;
import eu.royalblackwater.api.dto.OutboundWebhookEventCatalogItem;
import eu.royalblackwater.api.dto.OutboundWebhookRead;
import eu.royalblackwater.api.dto.OutboundWebhookSummary;
import eu.royalblackwater.api.dto.OutboundWebhookTestRequest;
import eu.royalblackwater.api.dto.OutboundWebhookUpdate;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.FernetSecretBox;
import eu.royalblackwater.api.webhooks.mapper.WebhookDtoMapper;
import eu.royalblackwater.api.webhooks.dto.WebhookDomainEvent;
import eu.royalblackwater.api.webhooks.repository.WebhookRepository;
import eu.royalblackwater.api.webhooks.repository.queries.WebhookQueries;
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

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.string;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.booleanValue;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class WebhookService {
    private static final TypeReference<List<String>> STRINGS=new TypeReference<>() { };
    private static final String FLEET_AVATAR_URL=
            "https://royal-blackwater-fleet.eu/rbf-fleet-icon.png";
    private final WebhookRepository repository;
    private final WebhookPolicy policy;
    private final WebhookHttpClient http;
    private final FernetSecretBox secrets;
    private final ObjectMapper json;
    private final AuditService audit;
    private final Clock clock;

    public WebhookService(WebhookRepository repository,WebhookPolicy policy,WebhookHttpClient http,FernetSecretBox secrets,
            ObjectMapper json,AuditService audit,Clock clock){
        this.repository=repository;this.policy=policy;this.http=http;this.secrets=secrets;this.json=json;
        this.audit=audit;this.clock=clock;
    }

    @Transactional(readOnly=true)
    public List<OutboundWebhookRead> list(String purpose){
        String where="broadcast".equals(purpose)?WebhookQueries.LIST_WHERE_01:"";
        return repository.query(WebhookQueries.LIST_SELECT_01+where+WebhookQueries.LIST_ORDER_BY_01,Map.of()).stream().map(this::toRead).toList();
    }

    @Transactional(readOnly = true)
    public List<OutboundWebhookEventCatalogItem> eventCatalog() {
        return WebhookDtoMapper.eventCatalog(WebhookEventCatalog.ALL);
    }

    @Transactional(readOnly=true)
    public OutboundWebhookSummary summary(String purpose){
        String filter="broadcast".equals(purpose)?WebhookQueries.SUMMARY_AND_01:"";
        return WebhookDtoMapper.summary(
                repository.count(WebhookQueries.SUMMARY_SELECT_01+filter,Map.of()),
                repository.count(WebhookQueries.SUMMARY_SELECT_02,Map.of()),
                repository.count(WebhookQueries.SUMMARY_SELECT_03+filter,Map.of()),
                repository.count(WebhookQueries.SUMMARY_SELECT_04,Map.of()),
                repository.count(WebhookQueries.SUMMARY_SELECT_05+filter,Map.of()));
    }

    @Transactional
    public OutboundWebhookRead create(AuthenticatedUser actor,OutboundWebhookCreate input){
        WebhookPolicy.Scope scope=validatedScope(input.scopeType(),input.scopeId());
        List<String> events=policy.events(input.eventTypes(),value(input.broadcastEnabled(),false));
        long id=repository.insertReturningId(WebhookQueries.CREATE_INSERT_01,SqlParameters.ofNullable("name",input.name().strip(),"endpoint",secrets.encrypt(policy.endpoint(input.endpointUrl())),
                        "events",write(events),"scope",scope.type(),"scopeId",scope.id(),"template",policy.template(input.messageTemplate()),
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
        repository.update(WebhookQueries.UPDATE_UPDATE_01,SqlParameters.ofNullable("id",id,"name",input.name().strip(),"endpoint",encrypted,"events",write(events),
                        "scope",scope.type(),"scopeId",scope.id(),"template",policy.template(input.messageTemplate()),
                        "username",blank(input.discordUsername()),"broadcast",broadcast,"active",value(input.isActive(),true),"now",now()));
        audit.record(actor,"outbound_webhook",id,"update","Updated outbound Discord webhook",Set.of("configuration"));
        return requiredRead(id);
    }

    @Transactional
    public void delete(AuthenticatedUser actor,long id){
        required(id);
        repository.update(WebhookQueries.DELETE_DELETE_01,Map.of("id",id));
        audit.record(actor,"outbound_webhook",id,"delete","Deleted outbound Discord webhook",Set.of());
    }

    @Transactional
    public OutboundWebhookDeliveryRead test(AuthenticatedUser actor,long id,OutboundWebhookTestRequest input){
        Map<String,Object> webhook=required(id);
        String event=input.eventType()==null||input.eventType().isBlank()?"integration.test":input.eventType().strip();
        policy.events(List.of(event),false);
        WebhookDomainEvent context=new WebhookDomainEvent(event,"integration",String.valueOf(id),
                "global",null,actor,"Manual connectivity and template rendering test.",now());
        return deliver(webhook,context,render(webhook,context),blank(string(webhook,"discord_username")));
    }

    @Transactional
    public List<OutboundWebhookDeliveryRead> broadcast(AuthenticatedUser actor,OutboundWebhookBroadcastRequest input){
        List<OutboundWebhookDeliveryRead> deliveries=new ArrayList<>();
        for(Long id:input.webhookIds().stream().distinct().toList()){
            Map<String,Object> webhook=required(id);
            if(!booleanValue(webhook,"is_active")||!booleanValue(webhook,"broadcast_enabled"))
                throw new ResponseStatusException(org.springframework.http.HttpStatus.CONFLICT,"Selected webhook is not an active broadcast target.");
            WebhookDomainEvent context=new WebhookDomainEvent("integration.test","broadcast",UUID.randomUUID().toString(),
                    "global",null,actor,input.message(),now());
            deliveries.add(deliver(webhook,context,input.message(),
                    blank(input.discordUsername())==null?blank(string(webhook,"discord_username")):blank(input.discordUsername())));
        }
        audit.record(actor,"outbound_webhook","broadcast","broadcast","Sent Discord broadcast",Set.of("message","targets"));
        return List.copyOf(deliveries);
    }

    @Transactional(readOnly=true)
    public List<OutboundWebhookDeliveryRead> deliveries(Long webhookId,String status,String eventType,long limit){
        StringBuilder sql=new StringBuilder(WebhookQueries.DELIVERIES_SELECT_01);
        Map<String,Object> params=new LinkedHashMap<>();
        if(webhookId!=null){sql.append(WebhookQueries.DELIVERIES_AND_01);params.put("webhook",webhookId);}
        if(status!=null&&!status.isBlank()){sql.append(WebhookQueries.DELIVERIES_AND_02);params.put("status",status.strip());}
        if(eventType!=null&&!eventType.isBlank()){sql.append(WebhookQueries.DELIVERIES_AND_03);params.put("event",eventType.strip());}
        sql.append(WebhookQueries.DELIVERIES_ORDER_BY_01);params.put("limit",Math.max(1,Math.min(1000,limit)));
        return repository.query(sql.toString(),params).stream().map(row -> WebhookDtoMapper.delivery(row)).toList();
    }

    @Transactional
    public OutboundWebhookDeliveryRead retry(AuthenticatedUser actor,long deliveryId){
        Map<String,Object> row=repository.optional(WebhookQueries.RETRY_SELECT_01,Map.of("id",deliveryId)).orElseThrow(()->notFound("Delivery"));
        WebhookHttpClient.Result result=send(requiredString(row,"endpoint_url"),requiredString(row,"payload_json"));
        updateDelivery(deliveryId,result);
        audit.record(actor,"outbound_webhook_delivery",deliveryId,"retry","Retried outbound webhook delivery",Set.of("status"));
        return delivery(deliveryId);
    }

    @Transactional
    public OutboundWebhookDeliveryDeleteResult deleteDelivery(AuthenticatedUser actor,long id){
        int count=repository.update(WebhookQueries.DELETE_DELIVERY_DELETE_01,Map.of("id",id));
        audit.record(actor,"outbound_webhook_delivery",id,"delete","Deleted webhook delivery history record",Set.of());
        return WebhookDtoMapper.deleted(count);
    }

    @Transactional
    public OutboundWebhookDeliveryDeleteResult deleteHistory(AuthenticatedUser actor,Long webhookId,String status,String eventType){
        StringBuilder sql=new StringBuilder(WebhookQueries.DELETE_HISTORY_DELETE_01);
        Map<String,Object> params=new LinkedHashMap<>();
        if(webhookId!=null){sql.append(WebhookQueries.DELETE_HISTORY_AND_01);params.put("webhook",webhookId);}
        if(status!=null&&!status.isBlank()){sql.append(WebhookQueries.DELETE_HISTORY_AND_02);params.put("status",status.strip());}
        if(eventType!=null&&!eventType.isBlank()){sql.append(WebhookQueries.DELETE_HISTORY_AND_03);params.put("event",eventType.strip());}
        int count=repository.update(sql.toString(),params);
        audit.record(actor,"outbound_webhook_delivery","history","delete","Deleted webhook delivery history",Set.of("filters"));
        return WebhookDtoMapper.deleted(count);
    }

    @Transactional
    public void publish(WebhookDomainEvent event) {
        policy.events(List.of(event.eventType()), false);
        for (Map<String, Object> webhook : repository.query(WebhookQueries.AUTOMATION_SELECT_01, Map.of())) {
            if (!events(requiredString(webhook, "event_types_json")).contains(event.eventType())
                    || !matchesScope(webhook, event)) continue;
            try {
                deliver(webhook, event, render(webhook, event), blank(string(webhook, "discord_username")));
            } catch (RuntimeException ignored) {
                // One invalid destination must not prevent delivery to the remaining subscriptions.
            }
        }
    }

    private OutboundWebhookDeliveryRead deliver(Map<String,Object> webhook,WebhookDomainEvent event,
            String message,String username){
        String deliveryId=UUID.randomUUID().toString();
        Map<String,Object> payload=new LinkedHashMap<>();payload.put("content",message);
        payload.put("allowed_mentions",Map.of("parse",List.of()));
        payload.put("avatar_url",FLEET_AVATAR_URL);
        if(username!=null) payload.put("username",username);
        String payloadJson=write(payload);
        long id=repository.insertReturningId(WebhookQueries.DELIVER_INSERT_01,Map.of("webhook",longValue(webhook,"id"),"delivery",deliveryId,"event",event.eventType(),"type",event.resourceType(),
                        "resource",event.resourceId(),"payload",payloadJson,"now",now()));
        WebhookHttpClient.Result result=send(requiredString(webhook,"endpoint_url"),payloadJson);
        updateDelivery(id,result);
        return delivery(id);
    }

    private String render(Map<String, Object> webhook, WebhookDomainEvent event) {
        String custom = blank(string(webhook, "message_template"));
        String template = custom == null ? WebhookEventCatalog.required(event.eventType()).defaultTemplate() : custom;
        return WebhookTemplateRenderer.render(template, event);
    }

    private static boolean matchesScope(Map<String, Object> webhook, WebhookDomainEvent event) {
        String type = requiredString(webhook, "scope_type");
        if ("global".equals(type)) return true;
        Long id = eu.royalblackwater.api.persistence.RowValues.nullableLong(webhook, "scope_id");
        return type.equals(event.scopeType()) && id != null && id.equals(event.scopeId());
    }

    private WebhookHttpClient.Result send(String storedEndpoint,String payload){
        String endpoint=policy.endpoint(secrets.decrypt(storedEndpoint));
        return http.send(endpoint,payload);
    }

    private void updateDelivery(long id,WebhookHttpClient.Result result){
        LocalDateTime timestamp=now();
        repository.update(WebhookQueries.UPDATE_DELIVERY_UPDATE_01,SqlParameters.ofNullable("id",id,"status",result.success()?"delivered":"failed","response",result.status(),
                        "body",result.body(),"error",result.error(),"now",timestamp,"delivered",result.success()?timestamp:null));
        repository.update(WebhookQueries.UPDATE_DELIVERY_UPDATE_02,Map.of("id",id,"success",result.success(),"now",timestamp));
    }

    private OutboundWebhookDeliveryRead delivery(long id){
        Map<String,Object> row=repository.optional(WebhookQueries.DELIVERY_SELECT_01,Map.of("id",id)).orElseThrow(()->notFound("Delivery"));
        return WebhookDtoMapper.delivery(row);
    }

    private OutboundWebhookRead requiredRead(long id){return toRead(required(id));}
    private Map<String,Object> required(long id){return repository.optional(WebhookQueries.REQUIRED_SELECT_01,Map.of("id",id)).orElseThrow(()->notFound("Webhook"));}
    private OutboundWebhookRead toRead(Map<String,Object> row){
        return WebhookDtoMapper.webhook(row,
                policy.publicEndpoint(requiredString(row, "endpoint_url"), secrets),
                events(requiredString(row, "event_types_json")));
    }

    private WebhookPolicy.Scope validatedScope(String type,Long id){
        WebhookPolicy.Scope scope=policy.scope(type,id);
        if("fleet".equals(scope.type())&&repository.count(WebhookQueries.VALIDATED_SCOPE_SELECT_01,Map.of("id",scope.id()))==0) throw notFound("Fleet");
        if("squad".equals(scope.type())&&repository.count(WebhookQueries.VALIDATED_SCOPE_SELECT_02,Map.of("id",scope.id()))==0) throw notFound("Squad");
        return scope;
    }
    private List<String> events(String value){try{return json.readValue(value,STRINGS);}catch(JacksonException exception){return List.of();}}
    private String write(Object value){try{return json.writeValueAsString(value);}catch(JacksonException exception){throw new IllegalStateException("Could not serialize webhook data",exception);}}
    private LocalDateTime now(){return LocalDateTime.ofInstant(clock.instant(),ZoneOffset.UTC);}
    private static <T>T value(T value,T fallback){return value==null?fallback:value;}
    private static String blank(String value){return value==null||value.isBlank()?null:value.strip();}
    private static ResponseStatusException notFound(String subject){return new ResponseStatusException(NOT_FOUND,subject+" not found.");}
}
