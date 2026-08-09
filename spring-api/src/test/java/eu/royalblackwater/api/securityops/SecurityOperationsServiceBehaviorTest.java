package eu.royalblackwater.api.securityops;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.securityops.repository.SecurityOperationsRepository;
import eu.royalblackwater.api.securityops.service.IpBlockService;
import eu.royalblackwater.api.securityops.service.SecuritySignalService;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

class SecurityOperationsServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-08-08T12:00:00Z"), ZoneOffset.UTC);

    @Test
    void ipBlockServiceRejectsHostnamesAndTreatsBlankAddressAsNotBlocked() {
        SecurityOperationsRepository repository = mock(SecurityOperationsRepository.class);
        IpBlockService service = new IpBlockService(repository, mock(AuditService.class), CLOCK);

        assertFalse(service.isBlocked("   "));
        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.isBlocked("example.com"));

        assertEquals(400, error.getStatusCode().value());
        verify(repository, never()).count(anyString(), anyMap());
    }

    @Test
    void securitySignalServiceBoundsAndSanitizesUntrustedFields() {
        SecurityOperationsRepository repository = mock(SecurityOperationsRepository.class);
        SecuritySignalService service = new SecuritySignalService(repository, CLOCK);
        String longIp = "1".repeat(60);
        String longTarget = "/" + "a".repeat(250) + "?unsafe=<script>";

        service.record(longIp, "auth_failure", " bad reason! ", longTarget);

        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> values = ArgumentCaptor.forClass(Map.class);
        verify(repository).update(anyString(), values.capture());
        assertEquals(45, String.valueOf(values.getValue().get("ip")).length());
        assertEquals("bad_reason_", values.getValue().get("reason"));
        assertEquals(180, String.valueOf(values.getValue().get("target")).length());
    }
}
