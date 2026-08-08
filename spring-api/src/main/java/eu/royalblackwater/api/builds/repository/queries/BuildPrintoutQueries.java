package eu.royalblackwater.api.builds.repository.queries;

/** SQL statements owned by the BuildPrintoutService persistence boundary. */
public final class BuildPrintoutQueries {
    private BuildPrintoutQueries() { }

    public static final String SAVE_UPDATE_01 = """
                        update builds set printout_cache_key=:cacheKey,printout_checksum=:checksum,
                               printout_size_bytes=:size,printout_source_updated_at=:sourceUpdatedAt,
                               printout_updated_at=:now where id=:id
                        """;

    public static final String CLEAR_UPDATE_01 = """
                        update builds set printout_cache_key=null,printout_checksum=null,
                               printout_size_bytes=null,printout_source_updated_at=null,printout_updated_at=null
                         where id=:id
                        """;

    public static final String CLEAR_IF_MATCH_UPDATE_01 = """
                        update builds set printout_cache_key=null,printout_checksum=null,
                               printout_size_bytes=null,printout_source_updated_at=null,printout_updated_at=null
                         where id=:id
                           and printout_cache_key is not distinct from :cacheKey
                           and printout_checksum=:checksum
                           and printout_source_updated_at is not distinct from :sourceUpdatedAt
                        """;

    public static final String CONTENT_SELECT_01 = "select * from builds where id=:id";
    public static final String CONTENT_LOCK_SELECT_01 = "select * from builds where id=:id for update";
    public static final String CACHE_ROWS_SELECT_01 = """
                        select id,printout_cache_key,printout_checksum,printout_size_bytes,
                               printout_source_updated_at,updated_at
                          from builds where printout_checksum is not null
                        """;
    public static final String GLOBAL_BYTES_SELECT_01 = """
                        select (select coalesce(sum(size_bytes),0) from stored_files)
                             + (select coalesce(sum(printout_size_bytes),0) from builds)
                        """;

}
