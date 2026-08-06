package eu.royalblackwater.api.securityops.repository.queries;

/** SQL statements owned by the SecuritySignalService persistence boundary. */
public final class SecuritySignalQueries {
    private SecuritySignalQueries() { }

    public static final String RECORD_INSERT_01 = """
                insert into security_signal_buckets(day,client_ip,signal,reason,request_target,event_count)
                values(:day,:ip,:signal,:reason,:target,1)
                on conflict(day,client_ip,signal,reason,request_target)
                do update set event_count=security_signal_buckets.event_count+1
                """;

}
