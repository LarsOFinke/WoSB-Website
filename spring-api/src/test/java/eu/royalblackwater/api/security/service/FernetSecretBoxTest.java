package eu.royalblackwater.api.security.service;

import java.security.SecureRandom;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FernetSecretBoxTest {
    private static final String KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=";
    private static final String PYTHON_TOKEN = "gAAAAABlU_EAAMcZuutefT3D19YvEhTrsg6B8pyFxnTTxGciM7MS78KSmLkay2uDje9i2ocYzlH3mgmFwUtpEPj4HcVczwucfUVYjGhriakW5sixBYoz3xE=";

    @Test
    void decryptsTheExistingPythonFernetFormat() {
        FernetSecretBox box = box(List.of(KEY));
        assertThat(box.decrypt("fernet:v1:" + PYTHON_TOKEN)).isEqualTo("compatibility-secret");
    }

    @Test
    void encryptsAuthenticatedCiphertextAndRejectsTampering() {
        FernetSecretBox box = box(List.of(KEY));
        String encrypted = box.encrypt("new secret");
        assertThat(encrypted).startsWith("fernet:v1:");
        assertThat(box.decrypt(encrypted)).isEqualTo("new secret");
        String tampered = encrypted.substring(0, encrypted.length() - 2) + "AA";
        assertThatThrownBy(() -> box.decrypt(tampered)).isInstanceOf(SecretBoxException.class);
    }

    @Test
    void rotatesCiphertextToThePrimaryKey() {
        String newer = "YWJjZGVmMDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODk=";
        FernetSecretBox oldBox = box(List.of(KEY));
        String oldCiphertext = oldBox.encrypt("rotating secret");
        FernetSecretBox rotating = box(List.of(newer, KEY));
        assertThat(rotating.needsRotation(oldCiphertext)).isTrue();
        String rotated = rotating.rotate(oldCiphertext);
        assertThat(rotating.decrypt(rotated)).isEqualTo("rotating secret");
        assertThat(rotating.needsRotation(rotated)).isFalse();
    }

    private static FernetSecretBox box(List<String> keys) {
        return new FernetSecretBox(keys, new SecureRandom(),
                Clock.fixed(Instant.parse("2026-08-04T06:00:00Z"), ZoneOffset.UTC));
    }
}
