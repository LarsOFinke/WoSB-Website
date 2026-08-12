package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.repository.BuildRepository;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.time.Clock;
import java.util.List;
import org.junit.jupiter.api.Test;

import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class BuildRepositoryFilterTest {
    @Test
    void pageFiltersBuildsByExactShipRate() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.query(contains("from builds b"), org.mockito.ArgumentMatchers.anyMap())).thenReturn(List.of());
        BuildRepository repository = new BuildRepository(jdbc, Clock.systemUTC());

        repository.page("fleet", "gunnery", "port_battle", 2L, null, 7L, 50, 0);

        verify(jdbc).query(contains("s.rate=:shipRate"), argThat(parameters ->
                parameters.get("shipRate").equals(2L)
                        && parameters.get("type").equals("gunnery")
                        && parameters.get("classification").equals("port_battle")));
        verify(jdbc).count(contains("s.rate=:shipRate"), argThat(parameters ->
                parameters.get("shipRate").equals(2L)));
    }
}
