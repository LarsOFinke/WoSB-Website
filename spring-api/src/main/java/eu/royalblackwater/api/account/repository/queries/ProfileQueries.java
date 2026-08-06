package eu.royalblackwater.api.account.repository.queries;

/** SQL statements owned by the ProfileService persistence boundary. */
public final class ProfileQueries {
    private ProfileQueries() { }

    public static final String OPTIONS_SELECT_01 = """
                        select id, name, rate
                          from ships
                         where is_active = true
                         order by rate, name, id
                        """;

    public static final String OPTIONS_SELECT_02 = """
                        select id, code, label
                          from fleet_roles
                         order by rank desc, label, id
                        """;

    public static final String VALIDATE_IDS_SELECT_01 = "select count(*) from ships where is_active = true and id in (:ids)";

    public static final String VALIDATE_IDS_SELECT_02 = "select count(*) from fleet_roles where id in (:ids)";

}
