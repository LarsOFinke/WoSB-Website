package eu.royalblackwater.api.builds.repository.queries;

/** SQL statements owned by the BuildRoleAdministrationService persistence boundary. */
public final class BuildRoleAdministrationQueries {
    private BuildRoleAdministrationQueries() { }

    public static final String LIST_SELECT_01 = "select * from build_roles order by sort_order,lower(label),slug";

    public static final String CREATE_SELECT_01 = "select count(*) from build_roles where slug=:slug";

    public static final String CREATE_INSERT_01 = """
                insert into build_roles(slug,label,description,sort_order,created_at,updated_at)
                values(:slug,:label,:description,:sortOrder,:now,:now)
                """;

    public static final String UPDATE_UPDATE_01 = """
                update build_roles set label=:label,description=:description,sort_order=:sortOrder,updated_at=:now
                 where slug=:slug
                """;

    public static final String DELETE_SELECT_01 = "select count(*) from build_roles";

    public static final String DELETE_SELECT_02 = "select count(*) from builds where build_type=:slug";

    public static final String DELETE_DELETE_01 = "delete from build_roles where slug=:slug";

    public static final String REQUIRED_SELECT_01 = "select * from build_roles where slug=:slug";

}
