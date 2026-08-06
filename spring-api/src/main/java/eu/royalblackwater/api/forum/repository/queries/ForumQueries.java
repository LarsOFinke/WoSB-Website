package eu.royalblackwater.api.forum.repository.queries;

/** SQL statements owned by the ForumService persistence boundary. */
public final class ForumQueries {
    private ForumQueries() { }

    public static final String SUMMARY_SELECT = """
            select t.id,t.title,t.category,t.owner_id,t.created_at,t.updated_at,
                   coalesce(nullif(up.display_name,''),u.username) owner_name,
                   greatest(t.updated_at,coalesce(max(p.created_at),t.updated_at)) last_activity_at,
                   greatest(count(p.id)-1,0) reply_count
            from forum_threads t join users u on u.id=t.owner_id
            left join user_profiles up on up.user_id=u.id
            left join forum_posts p on p.thread_id=t.id
            """;

    public static final String LIST_WHERE_01 = " where 1=1";

    public static final String LIST_AND_01 = " and (t.title ilike :search or t.category ilike :search)";

    public static final String LIST_AND_02 = " and t.category=:category";

    public static final String LIST_GROUP_BY_01 = " group by t.id,u.username,up.display_name order by t.updated_at desc,t.id desc limit :limit offset :offset";

    public static final String GET_WHERE_01 = " where t.id=:id group by t.id,u.username,up.display_name";

    public static final String GET_SELECT_01 = """
                select p.*,coalesce(nullif(up.display_name,''),u.username) author_name
                from forum_posts p join users u on u.id=p.author_id
                left join user_profiles up on up.user_id=u.id
                where p.thread_id=:id order by p.created_at,p.id
                """;

    public static final String CREATE_INSERT_01 = """
                insert into forum_threads(title,category,owner_id,is_pinned,created_at,updated_at)
                values(:title,:category,:ownerId,false,:now,:now) returning id
                """;

    public static final String CREATE_INSERT_02 = """
                insert into forum_posts(thread_id,author_id,body,created_at,updated_at)
                values(:threadId,:authorId,:body,:now,:now) returning id
                """;

    public static final String UPDATE_THREAD_SELECT_01 = """
                select * from forum_posts where thread_id=:id order by created_at,id limit 1
                """;

    public static final String UPDATE_THREAD_UPDATE_01 = """
                update forum_threads set title=:title,category=:category,updated_at=:now where id=:id
                """;

    public static final String UPDATE_THREAD_UPDATE_02 = "update forum_posts set body=:body,updated_at=:now where id=:id";

    public static final String ADD_POST_UPDATE_01 = "update forum_threads set updated_at=:now where id=:id";

    public static final String DELETE_POST_SELECT_01 = "select id from forum_posts where thread_id=:id order by created_at,id limit 1";

    public static final String DELETE_POST_DELETE_01 = "delete from forum_posts where id=:id";

    public static final String DELETE_THREAD_SELECT_01 = """
                select a.file_id from forum_post_attachments a join forum_posts p on p.id=a.post_id
                where p.thread_id=:id
                """;

    public static final String DELETE_THREAD_DELETE_01 = "delete from forum_threads where id=:id";

    public static final String READ_POST_SELECT_01 = """
                select p.*,coalesce(nullif(up.display_name,''),u.username) author_name
                from forum_posts p join users u on u.id=p.author_id
                left join user_profiles up on up.user_id=u.id where p.id=:id
                """;

    public static final String RAW_THREAD_SELECT_01 = "select * from forum_threads where id=:id";

    public static final String RAW_POST_SELECT_01 = "select * from forum_posts where id=:id";

    public static final String ATTACHMENT_IDS_SELECT_01 = "select file_id from forum_post_attachments where post_id=:id";

}
