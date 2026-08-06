package eu.royalblackwater.api.builds.repository.queries;

/** SQL statements owned by the BuildPrintoutService persistence boundary. */
public final class BuildPrintoutQueries {
    private BuildPrintoutQueries() { }

    public static final String SAVE_UPDATE_01 = """
                        update builds set printout_checksum=:checksum,printout_size_bytes=:size,
                               printout_updated_at=:now,updated_at=:now where id=:id
                        """;

    public static final String CONTENT_SELECT_01 = "select * from builds where id=:id";

}
