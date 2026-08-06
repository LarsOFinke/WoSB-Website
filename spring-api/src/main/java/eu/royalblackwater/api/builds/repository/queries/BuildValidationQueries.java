package eu.royalblackwater.api.builds.repository.queries;

/** SQL statements owned by the BuildValidationService persistence boundary. */
public final class BuildValidationQueries {
    private BuildValidationQueries() { }

    public static final String PREPARE_SELECT_01 = "select count(*) from build_roles where slug=:slug";

}
