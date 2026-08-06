package eu.royalblackwater.api.builds.repository.queries;

/** SQL statements owned by the BuildService persistence boundary. */
public final class BuildQueries {
    private BuildQueries() { }

    public static final String VOTE_INSERT_01 = """
                    insert into build_votes(build_id,user_id,created_at) values(:buildId,:userId,:createdAt)
                    on conflict(build_id,user_id) do nothing
                    """;

    public static final String VOTE_DELETE_01 = "delete from build_votes where build_id=:buildId and user_id=:userId";

    public static final String ASSIGN_ROLE_SELECT_01 = "select count(*) from build_roles where slug=:slug";

    public static final String VOTE_STATE_SELECT_01 = "select count(*) from build_votes where build_id=:id";

    public static final String VOTE_STATE_SELECT_02 = "select count(*) from build_votes where build_id=:id and user_id=:userId";

}
