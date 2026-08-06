package eu.royalblackwater.api.raidhelper.repository.queries;

/** SQL statements owned by the RaidHelperProfileService persistence boundary. */
public final class RaidHelperProfileQueries {
    private RaidHelperProfileQueries() { }

    public static final String LIST_SELECT_01 = "select * from raid_helper_profiles order by lower(name), id";

    public static final String CREATE_INSERT_01 = """
                    insert into raid_helper_profiles
                      (name, server_id, api_key_encrypted, api_base_url, timezone, default_leader_id,
                       is_active, created_by_username, created_at, updated_at)
                    values (:name, :serverId, :apiKey, :baseUrl, :timezone, :leaderId,
                            :active, :username, :now, :now)
                    returning id
                    """;

    public static final String UPDATE_UPDATE_01 = """
                    update raid_helper_profiles set name=:name, server_id=:serverId,
                      api_key_encrypted=:apiKey, api_base_url=:baseUrl, timezone=:timezone,
                      default_leader_id=:leaderId, is_active=:active, updated_at=:now
                    where id=:id
                    """;

    public static final String DELETE_DELETE_01 = "delete from raid_helper_profiles where id=:id";

    public static final String ROW_SELECT_01 = "select * from raid_helper_profiles where id=:id";

    public static final String HAS_LINKS_SELECT_01 = """
                select count(*) from raid_helper_event_links l
                join raid_helper_destinations d on d.id=l.destination_id
                where d.profile_id=:id
                """;

}
