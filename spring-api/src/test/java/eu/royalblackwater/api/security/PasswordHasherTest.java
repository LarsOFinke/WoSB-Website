package eu.royalblackwater.api.security;

import eu.royalblackwater.api.security.service.PasswordHasher;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class PasswordHasherTest {
    private final PasswordHasher hasher = new PasswordHasher();

    @Test
    void verifiesExistingPythonPasswordFormat() {
        String existing = "pbkdf2_sha256$600000$AAECAwQFBgcICQoLDA0ODw$"
                + "t3PDqsX5X__CS-knYsTLSF_F4KwcaQk-vrXxUEwaqaM";
        assertThat(hasher.verify("BlackwaterCompatibility123!", existing)).isTrue();
        assertThat(hasher.verify("wrong password", existing)).isFalse();
        assertThat(hasher.needsRehash(existing)).isFalse();
    }

    @Test
    void generatedHashesAreCompatibleAndSalted() {
        String first = hasher.hash("correct horse battery staple");
        String second = hasher.hash("correct horse battery staple");
        assertThat(first).startsWith("pbkdf2_sha256$600000$").isNotEqualTo(second);
        assertThat(hasher.verify("correct horse battery staple", first)).isTrue();
    }

    @Test
    void malformedAndExcessiveWorkFactorsFailClosed() {
        assertThat(hasher.verify("password", "invalid")).isFalse();
        assertThat(hasher.verify("password", "pbkdf2_sha256$999999999$AA$AA")).isFalse();
    }
}
