package eu.royalblackwater.api;

import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.springframework.boot.SpringApplication;

import static org.mockito.Mockito.mockStatic;

class RbfApiApplicationTest {
    @Test
    void mainDelegatesToSpringApplicationWithoutStartingARealServer() {
        try (MockedStatic<SpringApplication> spring = mockStatic(SpringApplication.class)) {
            String[] args = {"--spring.main.web-application-type=none"};
            RbfApiApplication.main(args);
            spring.verify(() -> SpringApplication.run(RbfApiApplication.class, args));
        }
    }
}
