package eu.royalblackwater.api.raidhelper.repository.queries;

/** SQL statements owned by the RaidHelperDeliveryWorker persistence boundary. */
public final class RaidHelperDeliveryQueries {
    private RaidHelperDeliveryQueries() { }

    public static final String CLAIM_WITH_01 = """
                    with candidate as (
                      select id from raid_helper_event_links where status='queued'
                      order by updated_at,id for update skip locked limit 1
                    )
                    update raid_helper_event_links l set status='processing',attempts=attempts+1,
                      last_attempt_at=:now,updated_at=:now from candidate c where l.id=c.id
                    returning l.id
                    """;

    public static final String DETAIL_SELECT_01 = """
                select l.*,e.title,e.category,e.description,e.location,e.start_at,e.end_at,e.all_day,e.squad_id,
                       s.name squad_name,d.channel_id,d.is_active destination_active,
                       p.server_id,p.api_key_encrypted,p.api_base_url,p.timezone,p.default_leader_id,
                       p.is_active profile_active,t.raid_template_id,t.title_template,t.description_template,
                       t.announcement_template,t.payload_template_json,t.is_active template_active
                from raid_helper_event_links l join fleet_events e on e.id=l.event_id
                left join squads s on s.id=e.squad_id
                join raid_helper_destinations d on d.id=l.destination_id
                join raid_helper_profiles p on p.id=d.profile_id
                join raid_helper_templates t on t.id=l.template_id
                where l.id=:id
                """;

    public static final String RECOVER_ABANDONED_CLAIMS_UPDATE_01 = """
                update raid_helper_event_links set status='queued',
                  error_message='Previous delivery attempt was interrupted and has been re-queued.',updated_at=:now
                where status='processing' and last_attempt_at < :cutoff
                """;

    public static final String SUCCEED_UPDATE_01 = """
                update raid_helper_event_links set status='delivered',external_event_id=:externalId,
                  response_status=:responseStatus,last_operation=:operation,error_message=null,
                  synced_at=:now,updated_at=:now where id=:id
                """;

    public static final String FAIL_UPDATE_01 = """
                update raid_helper_event_links set status='failed',response_status=:responseStatus,
                  error_message=:message,updated_at=:now where id=:id
                """;

    public static final String DELETE_LINK_DELETE_01 = "delete from raid_helper_event_links where id=:id";

}
