package eu.royalblackwater.api.files.repository.queries;

/** SQL statements owned by the FileAssetService persistence boundary. */
public final class FileAssetQueries {
    private FileAssetQueries() { }

    public static final String LIST_SELECT_01 = "select * from stored_files where owner_id=:ownerId";

    public static final String LIST_AND_01 = " and usage_context=:context";

    public static final String LIST_ORDER_BY_01 = " order by created_at desc,id desc";

    public static final String UPLOAD_INSERT_01 = """
                    insert into stored_files(owner_id,original_name,stored_name,relative_path,mime_type,size_bytes,
                                             usage_context,is_public,created_at)
                    values(:ownerId,:originalName,:storedName,:relativePath,:mimeType,:sizeBytes,:context,:public,:createdAt)
                    returning id
                    """;

    public static final String DELETE_DELETE_01 = "delete from stored_files where id=:id";

    public static final String OWNED_FILES_SELECT_01 = "select * from stored_files where id in (:ids)";

    public static final String ATTACH_DELETE_01 = "delete from ";

    public static final String ATTACH_WHERE_01 = " where ";

    public static final String ATTACH_INSERT_01 = "insert into ";

    public static final String ATTACH_UPDATE_01 = "update stored_files set usage_context=:context,is_public=true where id=:id";

    public static final String ATTACHMENTS_SELECT_01 = "select f.* from ";

    public static final String ATTACHMENTS_BY_OWNERS_SELECT_01 = "select a.";

    public static final String REFRESH_PUBLICATION_SELECT_01 = """
                    select (select count(*) from forum_post_attachments where file_id=:id)
                         + (select count(*) from guide_attachments ga join guides g on g.id=ga.guide_id
                            where ga.file_id=:id and g.is_published=true)
                         + (select count(*) from strategy_plans s
                            where s.background_file_id=:id and s.is_published=true)
                    """;

    public static final String REFRESH_PUBLICATION_UPDATE_01 = "update stored_files set is_public=(usage_context='master-data' or :referenced) where id=:id";

    public static final String RAW_SELECT_01 = "select * from stored_files where id=:id";

    public static final String IS_REFERENCED_SELECT_01 = """
                select (select count(*) from forum_post_attachments where file_id=:id)
                     + (select count(*) from guide_attachments where file_id=:id)
                     + (select count(*) from build_file_attachments where file_id=:id)
                     + (select count(*) from strategy_plans where background_file_id=:id)
                """;

    public static final String EFFECTIVE_LIMIT_SELECT_01 = "select coalesce(sum(size_bytes),0) from stored_files where owner_id=:id";

    public static final String EFFECTIVE_LIMIT_SELECT_02 = """
            select (select coalesce(sum(size_bytes),0) from stored_files)
                 + (select coalesce(sum(printout_size_bytes),0) from builds)
            """;

}
