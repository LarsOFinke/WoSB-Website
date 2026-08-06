package eu.royalblackwater.api.raidhelper.repository.queries;

/** SQL statements owned by the RaidHelperProbeService persistence boundary. */
public final class RaidHelperProbeQueries {
    private RaidHelperProbeQueries() { }

    public static final String DESTINATION_WITH_PROFILE_SELECT_01 = """
                select d.*,p.name profile_name,p.server_id,p.api_key_encrypted,p.api_base_url,p.timezone,
                       p.default_leader_id,p.is_active profile_active,s.name squad_name
                from raid_helper_destinations d join raid_helper_profiles p on p.id=d.profile_id
                left join squads s on s.id=d.squad_id where d.id=:id
                """;

    public static final String TEST_TEMPLATE_SELECT_01 = """
                    select t.*,p.timezone,p.name profile_name from raid_helper_templates t
                    join raid_helper_profiles p on p.id=t.profile_id
                    where t.profile_id=:profileId and t.is_active=true
                    order by t.is_default desc,t.id limit 1
                    """;

    public static final String TEST_EVENT_SELECT_01 = """
                select category from raid_helper_template_categories where template_id=:id order by category limit 1
                """;

    public static final String TEST_EVENT_SELECT_02 = """
                        select category from raid_helper_destination_categories
                        where destination_id=:id order by category limit 1
                        """;

}
