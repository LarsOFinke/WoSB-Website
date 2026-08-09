package eu.royalblackwater.api.config;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class SecretEncryptionPropertiesTest {
    @Test
    void configuredKeysNormalizesWhitespaceDropsEmptyValuesAndDeduplicates() {
        assertThat(new SecretEncryptionProperties(null).configuredKeys()).isEmpty();
        assertThat(new SecretEncryptionProperties("   ").configuredKeys()).isEmpty();
        assertThat(new SecretEncryptionProperties(" key-a, key-b ,,key-a,  key-c ").configuredKeys())
                .containsExactly("key-a", "key-b", "key-c");
    }
}
