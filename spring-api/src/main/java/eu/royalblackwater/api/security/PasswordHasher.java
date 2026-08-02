package eu.royalblackwater.api.security;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import org.springframework.stereotype.Component;

@Component
public final class PasswordHasher {
    static final String ALGORITHM = "pbkdf2_sha256";
    static final int ITERATIONS = 600_000;
    private static final int SALT_BYTES = 16;
    private static final int HASH_BITS = 256;
    private final SecureRandom random = new SecureRandom();

    public boolean verify(String password, String encoded) {
        try {
            String[] parts = encoded.split("\\$", -1);
            if (parts.length != 4 || !ALGORITHM.equals(parts[0])) return false;
            int iterations = Integer.parseInt(parts[1]);
            if (iterations < 1 || iterations > 2_000_000) return false;
            byte[] salt = decode(parts[2]);
            byte[] expected = decode(parts[3]);
            return MessageDigest.isEqual(expected, derive(password, salt, iterations, expected.length * 8));
        } catch (IllegalArgumentException | GeneralSecurityException exception) {
            return false;
        }
    }

    public boolean needsRehash(String encoded) {
        try {
            String[] parts = encoded.split("\\$", -1);
            return parts.length != 4 || !ALGORITHM.equals(parts[0]) || Integer.parseInt(parts[1]) < ITERATIONS;
        } catch (RuntimeException exception) {
            return true;
        }
    }

    public String hash(String password) {
        byte[] salt = new byte[SALT_BYTES];
        random.nextBytes(salt);
        try {
            byte[] digest = derive(password, salt, ITERATIONS, HASH_BITS);
            return ALGORITHM + "$" + ITERATIONS + "$" + encode(salt) + "$" + encode(digest);
        } catch (GeneralSecurityException exception) {
            throw new IllegalStateException("Password hashing is unavailable.", exception);
        }
    }

    private static byte[] derive(String password, byte[] salt, int iterations, int bits)
            throws GeneralSecurityException {
        PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, iterations, bits);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
        } finally {
            spec.clearPassword();
        }
    }

    private static String encode(byte[] value) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(value);
    }

    private static byte[] decode(String value) {
        return Base64.getUrlDecoder().decode(value.getBytes(StandardCharsets.US_ASCII));
    }
}
