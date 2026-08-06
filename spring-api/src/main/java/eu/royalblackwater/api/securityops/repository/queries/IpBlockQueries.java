package eu.royalblackwater.api.securityops.repository.queries;

/** SQL statements owned by the IpBlockService persistence boundary. */
public final class IpBlockQueries {
    private IpBlockQueries() { }

    public static final String IS_BLOCKED_SELECT_01 = """
                select count(*) from ip_blocks where ip_address=:ip and unblocked_at is null
                  and (expires_at is null or expires_at>:now)
                """;

    public static final String LIST_SELECT_01 = "select * from ip_blocks where 1=1";

    public static final String LIST_AND_01 = " and unblocked_at is null and (expires_at is null or expires_at>:now)";

    public static final String LIST_AND_02 = " and unblocked_at is null and expires_at<=:now";

    public static final String LIST_AND_03 = " and unblocked_at is not null";

    public static final String LIST_AND_04 = " and (ip_address ilike :search or reason ilike :search or coalesce(notes,'') ilike :search)";

    public static final String LIST_ORDER_BY_01 = " order by created_at desc,id desc limit :limit";

    public static final String SUMMARY_SELECT_01 = "select count(*) from ip_blocks where unblocked_at is null and (expires_at is null or expires_at>:now)";

    public static final String SUMMARY_SELECT_02 = "select count(*) from ip_blocks where unblocked_at is null and expires_at<=:now";

    public static final String SUMMARY_SELECT_03 = "select count(*) from ip_blocks where expires_at is null";

    public static final String SUMMARY_SELECT_04 = "select count(*) from ip_blocks where expires_at is not null";

    public static final String SUMMARY_SELECT_05 = "select count(*) from ip_blocks";

    public static final String SUMMARY_SELECT_06 = "select count(*) from ip_blocks where unblocked_at is not null";

    public static final String CREATE_INSERT_01 = """
                insert into ip_blocks(ip_address,reason,notes,created_at,created_by_user_id,created_by_username,expires_at)
                values(:ip,:reason,:notes,:now,:actorId,:actor,:expires) returning id
                """;

    public static final String UNBLOCK_SELECT_01 = "select * from ip_blocks where id=:id";

    public static final String UNBLOCK_UPDATE_01 = """
                update ip_blocks set unblocked_at=:now,unblocked_by_user_id=:actorId,
                    unblocked_by_username=:actor,unblock_reason=:reason where id=:id
                """;

}
