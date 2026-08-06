package eu.royalblackwater.api.securityops.repository.queries;

/** SQL statements owned by the SecurityDashboardService persistence boundary. */
public final class SecurityDashboardQueries {
    private SecurityDashboardQueries() { }

    public static final String BUILD_SELECT_01 = """
                select s.* from security_signal_buckets s where s.day between :from and :to
                  and not exists(select 1 from ip_blocks b where b.ip_address=s.client_ip and b.unblocked_at is null
                      and (b.expires_at is null or b.expires_at>current_timestamp))
                order by s.day,s.id
                """;

}
