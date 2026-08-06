package eu.royalblackwater.api.account.repository.queries;

/** SQL statements owned by the UserReferenceService persistence boundary. */
public final class UserReferenceQueries {
    private UserReferenceQueries() { }

    public static final String READ_MANY_SELECT_01 = """
                select u.id,coalesce(nullif(up.display_name,''),u.username) display_name
                  from users u
                  left join user_profiles up on up.user_id=u.id
                 where u.id in (:ids)
                 order by u.id
                """;

}
