package eu.royalblackwater.api.onboarding.repository.queries;

/** SQL statements owned by the NewcomerGuideService persistence boundary. */
public final class NewcomerGuideQueries {
    private NewcomerGuideQueries() { }

    public static final String REPLACE_UPDATE_01 = """
                update newcomer_guide_pages set title=:title,intro=:intro,updated_by_id=:userId,updated_at=:now where id=:id
                """;

    public static final String REPLACE_DELETE_01 = "delete from newcomer_guide_blocks where page_id=:id";

    public static final String REPLACE_INSERT_01 = """
                    insert into newcomer_guide_blocks(page_id,block_type,title,body,sort_order)
                    values(:pageId,:type,:title,:body,:sortOrder) returning id
                    """;

    public static final String REPLACE_INSERT_02 = """
                        insert into newcomer_guide_resources(block_id,resource_type,resource_id,label,description,url,sort_order)
                        values(:blockId,:type,:resourceId,:label,:description,:url,:sortOrder) returning id
                        """;

    public static final String READ_SELECT_01 = """
                select p.*,coalesce(nullif(up.display_name,''),u.username) updated_by
                from newcomer_guide_pages p left join users u on u.id=p.updated_by_id
                left join user_profiles up on up.user_id=u.id where p.id=:id
                """;

    public static final String READ_SELECT_02 = """
                select * from newcomer_guide_blocks where page_id=:id order by sort_order,id
                """;

    public static final String READ_SELECT_03 = """
                    select r.*,g.title guide_title,g.summary guide_summary,g.is_published,
                           b.build_name
                    from newcomer_guide_resources r
                    left join guides g on r.resource_type='guide' and g.id=r.resource_id
                    left join builds b on r.resource_type='build' and b.id=r.resource_id
                    where r.block_id in (:ids) order by r.block_id,r.sort_order,r.id
                    """;

    public static final String VALIDATE_SELECT_01 = "select id from guides where id in (:ids) and is_published=true";

    public static final String VALIDATE_SELECT_02 = "select id from builds where id in (:ids)";

    public static final String ENSURE_PAGE_SELECT_01 = "select count(*) from newcomer_guide_pages where id=:id";

    public static final String ENSURE_PAGE_INSERT_01 = """
                insert into newcomer_guide_pages(id,title,intro,created_at,updated_at)
                values(:id,:title,:intro,:now,:now) on conflict(id) do nothing
                """;

}
