package eu.royalblackwater.api.persistence;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DatabaseMigrationMainTest {
    @Test
    void acceptsPostgresMaximumIdentifierAndGeneratedRestoreNames() {
        assertThat(DatabaseMigrationMain.identifier("rbf_restore_20260809T162537Z_12345")).isEqualTo("rbf_restore_20260809T162537Z_12345");
        assertThat(DatabaseMigrationMain.identifier("a".repeat(63))).hasSize(63);
    }

    @Test
    void rejectsUnsafeOrOverlongIdentifiers() {
        assertThatThrownBy(() -> DatabaseMigrationMain.identifier("rbf-restore"))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> DatabaseMigrationMain.identifier("a".repeat(64)))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
