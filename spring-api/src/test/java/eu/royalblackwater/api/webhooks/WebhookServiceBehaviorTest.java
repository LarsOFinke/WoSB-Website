package eu.royalblackwater.api.webhooks;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.OutboundWebhookCreate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.FernetSecretBox;
import eu.royalblackwater.api.webhooks.repository.WebhookRepository;
import eu.royalblackwater.api.webhooks.service.WebhookHttpClient;
import eu.royalblackwater.api.webhooks.service.WebhookPolicy;
import eu.royalblackwater.api.webhooks.service.WebhookService;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class WebhookServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-08-08T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ACTOR = new AuthenticatedUser(1, "admin", "admin", true, true, true);

    @Test
    void eventCatalogIsAvailableWithoutPersistenceAndIsNotEmpty() {
        WebhookRepository repository = mock(WebhookRepository.class);
        WebhookService service = service(repository, new WebhookPolicy());

        assertFalse(service.eventCatalog().isEmpty());
        verify(repository, never()).query(anyString(), anyMap());
    }

    @Test
    void createRejectsMissingFleetScopeBeforePersistingOrContactingDiscord() {
        WebhookRepository repository = mock(WebhookRepository.class);
        WebhookPolicy policy = mock(WebhookPolicy.class);
        when(policy.scope("fleet", 99L)).thenReturn(new WebhookPolicy.Scope("fleet", 99L));
        WebhookHttpClient http = mock(WebhookHttpClient.class);
        WebhookService service = new WebhookService(repository, policy, http, mock(FernetSecretBox.class),
                new ObjectMapper(), mock(AuditService.class), CLOCK);
        OutboundWebhookCreate input = new OutboundWebhookCreate(false, null,
                "https://discord.com/api/webhooks/123/token", List.of("integration.test"), true,
                null, "Ops", 99L, "fleet");

        ResponseStatusException error = assertThrows(ResponseStatusException.class, () -> service.create(ACTOR, input));

        assertEquals(404, error.getStatusCode().value());
        verify(repository, never()).insertReturningId(anyString(), anyMap());
        verify(http, never()).send(anyString(), anyString());
    }

    private static WebhookService service(WebhookRepository repository, WebhookPolicy policy) {
        return new WebhookService(repository, policy, mock(WebhookHttpClient.class), mock(FernetSecretBox.class),
                new ObjectMapper(), mock(AuditService.class), CLOCK);
    }
}
