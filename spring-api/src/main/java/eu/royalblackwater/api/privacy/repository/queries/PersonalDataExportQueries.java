package eu.royalblackwater.api.privacy.repository.queries;

/** SQL statements owned by the PersonalDataExportService persistence boundary. */
public final class PersonalDataExportQueries {
    private PersonalDataExportQueries() { }

    public static final String BUILD_SELECT_01 = """
                select u.id, u.username, sr.code as role, u.is_active, u.created_at, u.updated_at
                from users u join site_roles sr on sr.id = u.site_role_id
                where u.id = :userId
                """;

    public static final String BUILD_SELECT_02 = "select * from ";

    public static final String BUILD_WHERE_01 = " where ";

    public static final String VERIFY_MAPPING_SELECT_01 = """
                select count(*) from information_schema.columns
                where table_schema = current_schema() and table_name = :tableName and column_name = :columnName
                """;

}
