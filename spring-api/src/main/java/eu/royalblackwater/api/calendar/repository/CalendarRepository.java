package eu.royalblackwater.api.calendar.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the calendar domain. */
@Repository
public final class CalendarRepository extends JdbcRepositorySupport {
    public CalendarRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
