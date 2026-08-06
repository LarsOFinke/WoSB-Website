package eu.royalblackwater.api.webhooks.repository.queries;

/** SQL statements owned by the WebhookService persistence boundary. */
public final class WebhookQueries {
    private WebhookQueries() { }

    public static final String LIST_WHERE_01 = " where broadcast_enabled=true";

    public static final String LIST_SELECT_01 = "select * from outbound_webhooks";

    public static final String LIST_ORDER_BY_01 = " order by name,id";

    public static final String SUMMARY_AND_01 = " and broadcast_enabled=true";

    public static final String SUMMARY_SELECT_01 = "select count(*) from outbound_webhooks where is_active=true";

    public static final String SUMMARY_SELECT_02 = "select count(*) from outbound_webhook_deliveries where status='failed'";

    public static final String SUMMARY_SELECT_03 = "select count(*) from outbound_webhooks where last_failure_at is not null and (last_success_at is null or last_failure_at>last_success_at)";

    public static final String SUMMARY_SELECT_04 = "select count(*) from outbound_webhook_deliveries where status='delivered'";

    public static final String SUMMARY_SELECT_05 = "select count(*) from outbound_webhooks where 1=1";

    public static final String CREATE_INSERT_01 = """
                insert into outbound_webhooks(name,endpoint_url,event_types_json,scope_type,scope_id,message_template,
                    discord_username,broadcast_enabled,is_active,created_at,updated_at,created_by_user_id,created_by_username)
                values(:name,:endpoint,:events,:scope,:scopeId,:template,:username,:broadcast,:active,:now,:now,:actorId,:actor) returning id
                """;

    public static final String UPDATE_UPDATE_01 = """
                update outbound_webhooks set name=:name,endpoint_url=:endpoint,event_types_json=:events,scope_type=:scope,
                    scope_id=:scopeId,message_template=:template,discord_username=:username,broadcast_enabled=:broadcast,
                    is_active=:active,updated_at=:now where id=:id
                """;

    public static final String DELETE_DELETE_01 = "delete from outbound_webhooks where id=:id";

    public static final String DELIVERIES_SELECT_01 = """
                select d.*,w.name webhook_name from outbound_webhook_deliveries d
                join outbound_webhooks w on w.id=d.webhook_id where 1=1
                """;

    public static final String DELIVERIES_AND_01 = " and d.webhook_id=:webhook";

    public static final String DELIVERIES_AND_02 = " and d.status=:status";

    public static final String DELIVERIES_AND_03 = " and d.event_type=:event";

    public static final String DELIVERIES_ORDER_BY_01 = " order by d.created_at desc,d.id desc limit :limit";

    public static final String RETRY_SELECT_01 = """
                select d.*,w.name webhook_name,w.endpoint_url,w.discord_username from outbound_webhook_deliveries d
                join outbound_webhooks w on w.id=d.webhook_id where d.id=:id
                """;

    public static final String DELETE_DELIVERY_DELETE_01 = "delete from outbound_webhook_deliveries where id=:id";

    public static final String DELETE_HISTORY_DELETE_01 = "delete from outbound_webhook_deliveries where 1=1";

    public static final String DELETE_HISTORY_AND_01 = " and webhook_id=:webhook";

    public static final String DELETE_HISTORY_AND_02 = " and status=:status";

    public static final String DELETE_HISTORY_AND_03 = " and event_type=:event";

    public static final String DELIVER_INSERT_01 = """
                insert into outbound_webhook_deliveries(webhook_id,delivery_id,event_type,resource_type,resource_id,payload_json,
                    status,attempts,created_at) values(:webhook,:delivery,:event,:type,:resource,:payload,'pending',0,:now) returning id
                """;

    public static final String UPDATE_DELIVERY_UPDATE_01 = """
                update outbound_webhook_deliveries set status=:status,attempts=attempts+1,response_status=:response,
                    response_body=:body,error_message=:error,last_attempt_at=:now,delivered_at=:delivered where id=:id
                """;

    public static final String UPDATE_DELIVERY_UPDATE_02 = """
                update outbound_webhooks set last_success_at=case when :success then :now else last_success_at end,
                    last_failure_at=case when :success then last_failure_at else :now end where id=(select webhook_id from outbound_webhook_deliveries where id=:id)
                """;

    public static final String DELIVERY_SELECT_01 = """
                select d.*,w.name webhook_name from outbound_webhook_deliveries d join outbound_webhooks w on w.id=d.webhook_id where d.id=:id
                """;

    public static final String REQUIRED_SELECT_01 = "select * from outbound_webhooks where id=:id";

    public static final String VALIDATED_SCOPE_SELECT_01 = "select count(*) from fleets where id=:id";

    public static final String VALIDATED_SCOPE_SELECT_02 = "select count(*) from squads where id=:id";

}
