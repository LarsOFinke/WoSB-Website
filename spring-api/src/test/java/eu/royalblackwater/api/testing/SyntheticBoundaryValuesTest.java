package eu.royalblackwater.api.testing;

import eu.royalblackwater.api.builds.dto.BuildPayload;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.Resource;

import static org.assertj.core.api.Assertions.assertThat;

class SyntheticBoundaryValuesTest {
    @Test
    void nestedGenericArgumentsRemainTypeCorrect() throws Exception {
        Method method = ArgumentFixture.class.getDeclaredMethod("rows", List.class);
        Object value = SyntheticBoundaryValues.argument(method.getGenericParameterTypes()[0], List.class, 0);

        assertThat(value).isInstanceOf(List.class);
        assertThat((List<?>) value).hasSize(1);
        assertThat(((List<?>) value).getFirst()).isInstanceOf(Map.class);
    }

    @Test
    void collaboratorDefaultsUseSafeEmptyShapesAndReturnSavedValues() {
        DependencyFixture dependency = (DependencyFixture) SyntheticBoundaryValues.dependency(
                DependencyFixture.class, DependencyFixture.class);
        Object saved = new Object();

        assertThat(dependency.rows()).isEmpty();
        assertThat(dependency.resources()).isEmpty();
        assertThat(dependency.save(saved)).isSameAs(saved);
    }

    @Test
    void buildPayloadBoundaryPreservesTheEightUpgradeSlotInvariant() {
        BuildPayload payload = (BuildPayload) SyntheticBoundaryValues.argument(BuildPayload.class, BuildPayload.class, 0);

        assertThat(payload.upgrades()).hasSize(8);
    }

    private interface ArgumentFixture {
        void rows(List<Map<String, Object>> rows);
    }

    private interface DependencyFixture {
        List<Map<String, Object>> rows();
        Resource[] resources();
        <T> T save(T value);
    }
}
