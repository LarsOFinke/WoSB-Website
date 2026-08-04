package eu.royalblackwater.api.security;

import eu.royalblackwater.api.config.SecretEncryptionProperties;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Clock;
import java.util.Base64;
import java.util.List;
import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class FernetSecretBox {
    static final String PREFIX = "fernet:v1:";
    private static final byte VERSION = (byte) 0x80;
    private static final int KEY_BYTES = 32;
    private static final int SIGNING_KEY_BYTES = 16;
    private static final int IV_BYTES = 16;
    private static final int HMAC_BYTES = 32;
    private static final int MIN_TOKEN_BYTES = 1 + Long.BYTES + IV_BYTES + 16 + HMAC_BYTES;

    private final List<FernetKey> keys;
    private final SecureRandom random;
    private final Clock clock;

    @Autowired
    public FernetSecretBox(SecretEncryptionProperties properties, Clock clock) {
        this(properties.configuredKeys(), new SecureRandom(), clock);
    }

    FernetSecretBox(List<String> encodedKeys, SecureRandom random, Clock clock) {
        if (encodedKeys.isEmpty()) {
            throw new SecretBoxException("At least one application encryption key is required.");
        }
        this.keys = encodedKeys.stream().map(FernetKey::decode).toList();
        this.random = random;
        this.clock = clock;
    }

    public boolean isEncrypted(String value) {
        return value != null && value.startsWith(PREFIX);
    }

    public String encrypt(String value) {
        if (value == null) {
            throw new SecretBoxException("Application secrets cannot be null.");
        }
        if (isEncrypted(value)) {
            return value;
        }
        return PREFIX + encryptToken(value.getBytes(StandardCharsets.UTF_8), clock.instant().getEpochSecond());
    }

    public String decrypt(String value) {
        if (value == null) {
            throw new SecretBoxException("Stored credential is missing.");
        }
        if (!isEncrypted(value)) {
            return value;
        }
        DecodedSecret decoded = decryptToken(value.substring(PREFIX.length()));
        return new String(decoded.plaintext(), StandardCharsets.UTF_8);
    }

    public boolean needsRotation(String value) {
        if (!isEncrypted(value)) {
            return true;
        }
        byte[] token = decodeToken(value.substring(PREFIX.length()));
        if (keys.getFirst().authenticates(token)) {
            return false;
        }
        requireDecryptingKey(token);
        return true;
    }

    public String rotate(String value) {
        if (!isEncrypted(value)) {
            return encrypt(value);
        }
        if (!needsRotation(value)) {
            return value;
        }
        DecodedSecret decoded = decryptToken(value.substring(PREFIX.length()));
        return PREFIX + encryptToken(decoded.plaintext(), decoded.timestamp());
    }

    private String encryptToken(byte[] plaintext, long timestamp) {
        try {
            byte[] iv = new byte[IV_BYTES];
            random.nextBytes(iv);
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            cipher.init(Cipher.ENCRYPT_MODE, keys.getFirst().encryptionKey(), new IvParameterSpec(iv));
            byte[] ciphertext = cipher.doFinal(plaintext);
            ByteBuffer signed = ByteBuffer.allocate(1 + Long.BYTES + IV_BYTES + ciphertext.length);
            signed.put(VERSION).putLong(timestamp).put(iv).put(ciphertext);
            byte[] signedBytes = signed.array();
            byte[] signature = keys.getFirst().sign(signedBytes);
            ByteBuffer token = ByteBuffer.allocate(signedBytes.length + signature.length);
            token.put(signedBytes).put(signature);
            return Base64.getUrlEncoder().encodeToString(token.array());
        } catch (GeneralSecurityException exception) {
            throw new SecretBoxException("Application secret could not be encrypted.", exception);
        }
    }

    private DecodedSecret decryptToken(String encodedToken) {
        byte[] token = decodeToken(encodedToken);
        FernetKey key = requireDecryptingKey(token);
        try {
            ByteBuffer buffer = ByteBuffer.wrap(token);
            byte version = buffer.get();
            long timestamp = buffer.getLong();
            byte[] iv = new byte[IV_BYTES];
            buffer.get(iv);
            int ciphertextLength = token.length - 1 - Long.BYTES - IV_BYTES - HMAC_BYTES;
            byte[] ciphertext = new byte[ciphertextLength];
            buffer.get(ciphertext);
            if (version != VERSION) {
                throw invalidSecret();
            }
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            cipher.init(Cipher.DECRYPT_MODE, key.encryptionKey(), new IvParameterSpec(iv));
            return new DecodedSecret(cipher.doFinal(ciphertext), timestamp);
        } catch (GeneralSecurityException | RuntimeException exception) {
            if (exception instanceof SecretBoxException secretBoxException) {
                throw secretBoxException;
            }
            throw invalidSecret(exception);
        }
    }

    private FernetKey requireDecryptingKey(byte[] token) {
        for (FernetKey key : keys) {
            if (key.authenticates(token)) {
                return key;
            }
        }
        throw invalidSecret();
    }

    private static byte[] decodeToken(String encodedToken) {
        try {
            byte[] token = Base64.getUrlDecoder().decode(encodedToken);
            if (token.length < MIN_TOKEN_BYTES || token[0] != VERSION) {
                throw invalidSecret();
            }
            return token;
        } catch (IllegalArgumentException exception) {
            throw invalidSecret(exception);
        }
    }

    private static SecretBoxException invalidSecret() {
        return new SecretBoxException("Stored application credential could not be decrypted.");
    }

    private static SecretBoxException invalidSecret(Throwable cause) {
        return new SecretBoxException("Stored application credential could not be decrypted.", cause);
    }

    private record DecodedSecret(byte[] plaintext, long timestamp) { }

    private record FernetKey(SecretKeySpec signingKey, SecretKeySpec encryptionKey) {
        static FernetKey decode(String encoded) {
            try {
                byte[] raw = Base64.getUrlDecoder().decode(encoded);
                if (raw.length != KEY_BYTES) {
                    throw new SecretBoxException("Each encryption key must decode to exactly 32 bytes.");
                }
                byte[] signing = java.util.Arrays.copyOfRange(raw, 0, SIGNING_KEY_BYTES);
                byte[] encryption = java.util.Arrays.copyOfRange(raw, SIGNING_KEY_BYTES, KEY_BYTES);
                return new FernetKey(new SecretKeySpec(signing, "HmacSHA256"),
                        new SecretKeySpec(encryption, "AES"));
            } catch (IllegalArgumentException exception) {
                throw new SecretBoxException("Encryption keys must be URL-safe Base64 values.", exception);
            }
        }

        boolean authenticates(byte[] token) {
            if (token.length < HMAC_BYTES) {
                return false;
            }
            int signedLength = token.length - HMAC_BYTES;
            byte[] expected = sign(java.util.Arrays.copyOf(token, signedLength));
            byte[] actual = java.util.Arrays.copyOfRange(token, signedLength, token.length);
            return MessageDigest.isEqual(expected, actual);
        }

        byte[] sign(byte[] bytes) {
            try {
                Mac mac = Mac.getInstance("HmacSHA256");
                mac.init(signingKey);
                return mac.doFinal(bytes);
            } catch (GeneralSecurityException exception) {
                throw new SecretBoxException("Application secret authentication failed.", exception);
            }
        }
    }
}
