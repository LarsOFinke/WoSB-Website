package eu.royalblackwater.api.squads.repository.queries;

/** SQL statements owned by the SquadAccessPolicy persistence boundary. */
public final class SquadAccessQueries {
    private SquadAccessQueries() { }

    public static final String HAS_MANAGED_SQUAD_SELECT_01 = """
                select count(*) from squad_members sm
                join squads s on s.id=sm.squad_id
                join squad_roles sr on sr.id=sm.squad_role_id
                join fleet_memberships fm on fm.id=sm.fleet_membership_id
                where fm.user_id=:userId and fm.status='active' and s.is_active=true
                  and sr.code in ('leader','officer')
                """;

    public static final String MEMBER_ROLE_SELECT_01 = """
                select sr.code from squad_members sm
                join squad_roles sr on sr.id=sm.squad_role_id
                join fleet_memberships fm on fm.id=sm.fleet_membership_id
                where sm.squad_id=:squadId and fm.user_id=:userId and fm.status='active'
                """;

}
