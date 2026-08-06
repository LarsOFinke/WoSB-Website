package eu.royalblackwater.api.raidhelper.repository.queries;

/** SQL statements owned by the RaidHelperTemplateService persistence boundary. */
public final class RaidHelperTemplateQueries {
    private RaidHelperTemplateQueries() { }

    public static final String BASE_QUERY = """
            select t.*, p.name profile_name
            from raid_helper_templates t join raid_helper_profiles p on p.id=t.profile_id
            """;

    public static final String LIST_ORDER_BY_01 = " order by lower(t.name), t.id";

    public static final String CREATE_INSERT_01 = """
                    insert into raid_helper_templates
                      (profile_id, name, raid_template_id, scope_type, title_template, description_template,
                       announcement_template, payload_template_json, uses_premium_features,
                       is_default, is_active, created_at, updated_at)
                    values (:profileId, :name, :raidTemplateId, :scopeType, :titleTemplate, :descriptionTemplate,
                            :announcementTemplate, :payloadTemplate, :premium, :isDefault, :isActive, :now, :now)
                    returning id
                    """;

    public static final String UPDATE_UPDATE_01 = """
                    update raid_helper_templates set profile_id=:profileId, name=:name,
                      raid_template_id=:raidTemplateId, scope_type=:scopeType, title_template=:titleTemplate,
                      description_template=:descriptionTemplate, announcement_template=:announcementTemplate,
                      payload_template_json=:payloadTemplate, uses_premium_features=:premium,
                      is_default=:isDefault, is_active=:isActive, updated_at=:now
                    where id=:id
                    """;

    public static final String DELETE_DELETE_01 = "delete from raid_helper_templates where id=:id";

    public static final String DETAIL_WHERE_01 = " where t.id=:id";

    public static final String ROW_SELECT_01 = "select * from raid_helper_templates where id=:id";

    public static final String READ_SELECT_01 = """
                select category from raid_helper_template_categories where template_id=:id order by category
                """;

    public static final String VALIDATE_SELECT_01 = "select count(*) from raid_helper_profiles where id=:id";

    public static final String REPLACE_CATEGORIES_DELETE_01 = "delete from raid_helper_template_categories where template_id=:id";

    public static final String REPLACE_CATEGORIES_INSERT_01 = "insert into raid_helper_template_categories (template_id, category) values (:id, :category)";

    public static final String HAS_LINKS_SELECT_01 = "select count(*) from raid_helper_event_links where template_id=:id";

}
