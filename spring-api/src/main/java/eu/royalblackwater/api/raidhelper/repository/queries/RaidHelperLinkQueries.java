package eu.royalblackwater.api.raidhelper.repository.queries;

/** SQL statements owned by the RaidHelperLinkService persistence boundary. */
public final class RaidHelperLinkQueries {
    private RaidHelperLinkQueries() { }

    public static final String OPTIONS_SELECT_01 = """
                select d.id destination_id,d.name destination_name,d.profile_id,d.scope_type,d.squad_id,
                       d.is_default destination_default,p.name profile_name,p.default_leader_id,
                       t.id template_id,t.name template_name,t.raid_template_id,t.is_default template_default
                from raid_helper_destinations d
                join raid_helper_profiles p on p.id=d.profile_id and p.is_active=true
                join raid_helper_templates t on t.profile_id=p.id and t.is_active=true
                where d.is_active=true and d.scope_type=:scope
                  and (cast(:squadId as integer) is null and d.squad_id is null or d.squad_id=:squadId)
                  and t.scope_type in ('both',:scope)
                  and (not exists(select 1 from raid_helper_destination_categories dc where dc.destination_id=d.id)
                       or exists(select 1 from raid_helper_destination_categories dc where dc.destination_id=d.id and dc.category=:category))
                  and (not exists(select 1 from raid_helper_template_categories tc where tc.template_id=t.id)
                       or exists(select 1 from raid_helper_template_categories tc where tc.template_id=t.id and tc.category=:category))
                order by d.is_default desc,lower(d.name),d.id,t.is_default desc,lower(t.name),t.id
                """;

    public static final String CONFIGURE_SELECT_01 = "select * from raid_helper_event_links where event_id=:id order by id";

    public static final String CONFIGURE_INSERT_01 = """
                        insert into raid_helper_event_links
                          (event_id,destination_id,template_id,leader_id_override,status,last_operation,attempts,
                           created_at,updated_at)
                        values (:eventId,:destinationId,:templateId,:leaderId,'queued','create',0,:now,:now)
                        returning id
                        """;

    public static final String CONFIGURE_UPDATE_01 = """
                        update raid_helper_event_links set template_id=:templateId,leader_id_override=:leaderId,
                          status='queued',last_operation=:operation,error_message=null,updated_at=:now
                        where id=:id
                        """;

    public static final String CONFIGURE_DELETE_01 = "delete from raid_helper_event_links where id=:id";

    public static final String CONFIGURE_UPDATE_02 = """
                        update raid_helper_event_links set status='queued',last_operation='delete',
                          error_message=null,updated_at=:now where id=:id
                        """;

    public static final String LINKS_BY_EVENT_IDS_SELECT_01 = """
                select l.*,d.name destination_name,p.name profile_name,t.name template_name
                from raid_helper_event_links l join raid_helper_destinations d on d.id=l.destination_id
                join raid_helper_profiles p on p.id=d.profile_id
                join raid_helper_templates t on t.id=l.template_id
                where l.event_id in (:ids) order by l.event_id,l.id
                """;

    public static final String QUEUE_RETRY_UPDATE_01 = """
                update raid_helper_event_links set status='queued',
                  last_operation=case when external_event_id is null then 'create' else 'update' end,
                  error_message=null,updated_at=:now where event_id=:id
                """;

    public static final String QUEUE_CANCELLATION_UPDATE_01 = """
                update raid_helper_event_links set status='queued',last_operation='delete',
                  error_message=null,updated_at=:now where event_id=:id
                """;

    public static final String CAN_MANAGE_SELECT_01 = "select fleet_id,is_active from squads where id=:id";

    public static final String OFFICIAL_FLEET_ID_SELECT_01 = """
                select id from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end,sort_order,id limit 1
                """;

}
