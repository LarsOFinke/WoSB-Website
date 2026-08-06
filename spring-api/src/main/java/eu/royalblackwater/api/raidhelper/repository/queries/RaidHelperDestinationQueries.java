package eu.royalblackwater.api.raidhelper.repository.queries;

/** SQL statements owned by the RaidHelperDestinationService persistence boundary. */
public final class RaidHelperDestinationQueries {
    private RaidHelperDestinationQueries() { }

    public static final String BASE_QUERY = """
            select d.*, p.name profile_name, s.name squad_name
            from raid_helper_destinations d
            join raid_helper_profiles p on p.id=d.profile_id
            left join squads s on s.id=d.squad_id
            """;

    public static final String LIST_ORDER_BY_01 = " order by lower(d.name), d.id";

    public static final String CREATE_INSERT_01 = """
                    insert into raid_helper_destinations
                      (profile_id, name, channel_id, scope_type, squad_id, is_default, is_active, created_at, updated_at)
                    values (:profileId, :name, :channelId, :scopeType, :squadId, :isDefault, :isActive, :now, :now)
                    returning id
                    """;

    public static final String UPDATE_UPDATE_01 = """
                    update raid_helper_destinations set profile_id=:profileId, name=:name,
                      channel_id=:channelId, scope_type=:scopeType, squad_id=:squadId,
                      is_default=:isDefault, is_active=:isActive, updated_at=:now
                    where id=:id
                    """;

    public static final String DELETE_DELETE_01 = "delete from raid_helper_destinations where id=:id";

    public static final String DETAIL_WHERE_01 = " where d.id=:id";

    public static final String ROW_SELECT_01 = "select * from raid_helper_destinations where id=:id";

    public static final String READ_SELECT_01 = """
                select category from raid_helper_destination_categories
                where destination_id=:id order by category
                """;

    public static final String VALIDATE_SELECT_01 = "select count(*) from raid_helper_profiles where id=:id";

    public static final String VALIDATE_SELECT_02 = "select count(*) from squads where id=:id and is_active=true";

    public static final String REPLACE_CATEGORIES_DELETE_01 = "delete from raid_helper_destination_categories where destination_id=:id";

    public static final String REPLACE_CATEGORIES_INSERT_01 = """
                    insert into raid_helper_destination_categories (destination_id, category)
                    values (:id, :category)
                    """;

    public static final String HAS_LINKS_SELECT_01 = "select count(*) from raid_helper_event_links where destination_id=:id";

}
