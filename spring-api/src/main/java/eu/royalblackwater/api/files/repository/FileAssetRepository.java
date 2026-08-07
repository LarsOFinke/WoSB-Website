package eu.royalblackwater.api.files.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the files domain. */
@Repository
public class FileAssetRepository extends JdbcRepositorySupport {
    public FileAssetRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
