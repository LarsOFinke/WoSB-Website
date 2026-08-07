package eu.royalblackwater.api.security.service;

public class SecretBoxException extends IllegalStateException {
    private static final long serialVersionUID = 1L;

    public SecretBoxException(String message) {
        super(message);
    }

    public SecretBoxException(String message, Throwable cause) {
        super(message, cause);
    }
}
