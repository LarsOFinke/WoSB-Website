package eu.royalblackwater.api.security;

import eu.royalblackwater.api.security.service.SessionTokenService;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class SessionTokenServiceTest {
    @Test
    void usesTheSharedSha256TokenContract() {
        SessionTokenService service = new SessionTokenService();
        assertThat(service.hash("abc")).isEqualTo(
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        assertThat(service.create()).hasSizeGreaterThanOrEqualTo(43).doesNotContain("=");
    }
}
