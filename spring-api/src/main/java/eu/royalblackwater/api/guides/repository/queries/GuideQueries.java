package eu.royalblackwater.api.guides.repository.queries;

/** SQL statements owned by the GuideService persistence boundary. */
public final class GuideQueries {
    private GuideQueries() { }

    public static final String SUMMARY = """
            select g.id,g.title,g.category,g.summary,g.owner_id,g.created_at,g.updated_at,
                   coalesce((select count(*) from guide_attachments a where a.guide_id=g.id),0) attachment_count,
                   coalesce((select count(*) from guide_build_references r where r.guide_id=g.id),0) build_reference_count
              from guides g
            """;

    public static final String LIST_WHERE_01 = " where g.is_published=true";

    public static final String LIST_AND_01 = " and (g.title ilike :search or coalesce(g.summary,'') ilike :search or g.body ilike :search)";

    public static final String LIST_AND_02 = " and g.category=:category";

    public static final String LIST_ORDER_BY_01 = " order by g.updated_at desc,g.id desc limit :limit offset :offset";

    public static final String GET_WHERE_01 = " where g.id=:id and g.is_published=true";

    public static final String GET_SELECT_01 = "select body from guides where id=:id";

    public static final String CREATE_INSERT_01 = """
                insert into guides(title,category,summary,body,owner_id,is_published,created_at,updated_at)
                values(:title,:category,:summary,:body,:ownerId,true,:now,:now) returning id
                """;

    public static final String UPDATE_UPDATE_01 = """
                update guides set title=:title,category=:category,summary=:summary,body=:body,updated_at=:now
                 where id=:id and is_published=true
                """;

    public static final String DELETE_UPDATE_01 = "update guides set is_published=false,updated_at=:now where id=:id and is_published=true";

    public static final String REPLACE_LINKS_DELETE_01 = "delete from guide_build_references where guide_id=:id";

    public static final String REPLACE_LINKS_INSERT_01 = """
                    insert into guide_build_references(guide_id,build_id,sort_order)
                    values(:guideId,:buildId,:sortOrder)
                    """;

    public static final String LINKED_BUILDS_SELECT_01 = """
                select build_id from guide_build_references where guide_id=:id order by sort_order,id
                """;

    public static final String RAW_SELECT_01 = "select * from guides where id=:id and is_published=true";

    public static final String ATTACHMENT_IDS_SELECT_01 = "select file_id from guide_attachments where guide_id=:id";

}
