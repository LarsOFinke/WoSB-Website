package eu.royalblackwater.api.strategies.repository.queries;

public final class StrategyQueries {
    private StrategyQueries() { }

    public static final String SELECT = """
            select s.id strategy_id,s.owner_id,s.background_file_id,s.title,s.description,s.overlay_json,s.public_id,
                   s.is_published,s.created_at strategy_created_at,s.updated_at strategy_updated_at,
                   s.published_at,f.*
              from strategy_plans s join stored_files f on f.id=s.background_file_id
            """;
    public static final String MINE = SELECT + " where s.owner_id=:ownerId order by s.updated_at desc,s.id desc";
    public static final String OWNED = SELECT + " where s.id=:id and s.owner_id=:ownerId";
    public static final String SHARED = SELECT + " where s.public_id=:publicId and s.is_published=true";
    public static final String CREATE = """
            insert into strategy_plans(owner_id,background_file_id,title,description,overlay_json,public_id,
                                       is_published,created_at,updated_at,published_at)
            values(:ownerId,:backgroundFileId,:title,:description,:overlayJson,:publicId,false,:now,:now,null)
            returning id
            """;
    public static final String UPDATE = """
            update strategy_plans set background_file_id=:backgroundFileId,title=:title,
                   description=:description,overlay_json=:overlayJson,updated_at=:now
             where id=:id and owner_id=:ownerId
            """;
    public static final String DELETE = "delete from strategy_plans where id=:id and owner_id=:ownerId";
    public static final String PUBLISH = """
            update strategy_plans set is_published=:published,published_at=:publishedAt,updated_at=:now
             where id=:id and owner_id=:ownerId
            """;
    public static final String REFERENCES_DELETE = "delete from %s where strategy_id=:id";
    public static final String REFERENCE_INSERT = "insert into %s(strategy_id,%s) values(:id,:referenceId)";
    public static final String EXISTING_SHIPS = "select count(*) from ships where id in (:ids) and is_active=true";
    public static final String BUILD_SHIPS = "select id,ship_id from builds where id in (:ids)";
    public static final String EXISTING_GUIDES = "select count(*) from guides where id in (:ids) and is_published=true";
}
