package eu.royalblackwater.api.security.model;

public class SecretBoxException extends IllegalStateException {
    public SecretBoxException(String message) {
        super(message);
    }

    public SecretBoxException(String message, Throwable cause) {
        super(message, cause);
    }
}
