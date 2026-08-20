package eu.royalblackwater.api.warehouse.repository.queries;

/** SQL statements owned by the warehouse persistence boundary. */
public final class WarehouseQueries {
    private WarehouseQueries() { }

    public static final String ENTRY_SELECT = """
            select w.*, f.name fleet_name,
                   coalesce(nullif(up.display_name,''), member.username, w.custom_holder_name) holder_name,
                   coalesce(nullif(editor_profile.display_name,''), editor.username) updated_by
            from warehouse_entries w
            join fleets f on f.id=w.fleet_id
            left join users member on member.id=w.member_user_id
            left join user_profiles up on up.user_id=member.id
            left join users editor on editor.id=w.updated_by_id
            left join user_profiles editor_profile on editor_profile.user_id=editor.id
            """;

    public static final String SUMMARY_SELECT = """
            select count(*) total,
                   coalesce(sum(w.amount),0) matching_stock,
                   coalesce(sum(w.amount) filter (where w.reserved),0) reserved_stock,
                   coalesce(sum(w.amount) filter (where not w.reserved),0) available_stock
            from warehouse_entries w
            left join users member on member.id=w.member_user_id
            left join user_profiles up on up.user_id=member.id
            """;

    public static final String FILTER_WHERE_01 = " where 1=1";
    public static final String FILTER_AND_FLEET_01 = " and w.fleet_id=:fleetId";
    public static final String FILTER_AND_HOLDER_01 = " and lower(coalesce(nullif(up.display_name,''),member.username,w.custom_holder_name))=:holder";
    public static final String FILTER_AND_PORT_01 = " and lower(w.port)=:port";
    public static final String FILTER_AND_RESOURCE_01 = " and lower(w.resource)=:resource";
    public static final String FILTER_AND_RESERVED_01 = " and w.reserved=:reserved";
    public static final String LIST_ORDER_LIMIT_01 = " order by lower(f.name),lower(coalesce(nullif(up.display_name,''),member.username,w.custom_holder_name)),lower(w.port),lower(w.resource),w.id limit :limit offset :offset";
    public static final String RAW_WHERE_01 = " where w.id=:id";

    public static final String FACET_HOLDERS_SELECT_01 = """
            select distinct coalesce(nullif(up.display_name,''),member.username,w.custom_holder_name) value
            from warehouse_entries w
            left join users member on member.id=w.member_user_id
            left join user_profiles up on up.user_id=member.id
            where (cast(:fleetId as bigint) is null or w.fleet_id=:fleetId)
            order by value limit 500
            """;

    public static final String FACET_PORTS_SELECT_01 = """
            select distinct w.port value from warehouse_entries w
            where (cast(:fleetId as bigint) is null or w.fleet_id=:fleetId)
            order by value limit 500
            """;

    public static final String FACET_RESOURCES_SELECT_01 = """
            select distinct w.resource value from warehouse_entries w
            where (cast(:fleetId as bigint) is null or w.fleet_id=:fleetId)
            order by value limit 500
            """;

    public static final String FLEET_SELECT_01 = "select id,name from fleets where id=:fleetId and is_active=true";

    public static final String OVERVIEW_SELECT_01 = """
            select w.port,w.resource,
                   coalesce(sum(w.amount),0) total,
                   coalesce(sum(w.amount) filter (where not w.reserved),0) available,
                   coalesce(sum(w.amount) filter (where w.reserved),0) reserved
            from warehouse_entries w
            where w.fleet_id=:fleetId
            group by w.port,w.resource
            order by lower(w.port),lower(w.resource)
            """;

    public static final String MEMBER_SELECT_01 = """
            select u.id,coalesce(nullif(up.display_name,''),u.username) display_name
            from fleet_memberships membership
            join users u on u.id=membership.user_id
            left join user_profiles up on up.user_id=u.id
            where membership.fleet_id=:fleetId and membership.user_id=:memberUserId
              and membership.status='active' and u.is_active=true
            """;

    public static final String CREATE_INSERT_01 = """
            insert into warehouse_entries
                (fleet_id,member_user_id,custom_holder_name,port,resource,amount,reserved,
                 version,created_at,updated_at,updated_by_id)
            values (:fleetId,:memberUserId,:customHolderName,:port,:resource,:amount,:reserved,
                    1,:now,:now,:actorId)
            returning id
            """;

    public static final String UPDATE_UPDATE_01 = """
            update warehouse_entries
            set fleet_id=:fleetId,member_user_id=:memberUserId,custom_holder_name=:customHolderName,
                port=:port,resource=:resource,amount=:amount,reserved=:reserved,
                version=version+1,updated_at=:now,updated_by_id=:actorId
            where id=:id and version=:version
            """;

    public static final String DELETE_DELETE_01 = "delete from warehouse_entries where id=:id and version=:version";

    public static final String ACTIVE_PORTS_SELECT_01 = """
            select * from warehouse_ports where is_active=true order by sort_order,lower(name),id
            """;
    public static final String ALL_PORTS_SELECT_01 = """
            select * from warehouse_ports order by sort_order,lower(name),id
            """;
    public static final String PORT_SELECT_01 = "select * from warehouse_ports where id=:id";
    public static final String ACTIVE_PORT_BY_NAME_SELECT_01 = """
            select id,name from warehouse_ports where is_active=true and lower(name)=lower(:name)
            """;
    public static final String PORT_NAME_EXISTS_SELECT_01 = """
            select count(*) from warehouse_ports where lower(name)=lower(:name)
              and (cast(:id as bigint) is null or id<>:id)
            """;
    public static final String CREATE_PORT_INSERT_01 = """
            insert into warehouse_ports(name,sort_order,is_active,created_at,updated_at)
            values (:name,:sortOrder,:active,:now,:now) returning id
            """;
    public static final String UPDATE_PORT_UPDATE_01 = """
            update warehouse_ports set name=:name,sort_order=:sortOrder,is_active=:active,updated_at=:now
            where id=:id
            """;
    public static final String RENAME_ENTRY_PORTS_UPDATE_01 = """
            update warehouse_entries set port=:name,version=version+1,updated_at=:now,updated_by_id=:actorId
            where lower(port)=lower(:previousName)
            """;
    public static final String DEACTIVATE_PORT_UPDATE_01 = """
            update warehouse_ports set is_active=false,updated_at=:now where id=:id
            """;
}
