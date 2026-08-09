package eu.royalblackwater.api.webhooks;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.OutboundWebhookCreate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.FernetSecretBox;
import eu.royalblackwater.api.webhooks.repository.WebhookRepository;
import eu.royalblackwater.api.webhooks.dto.WebhookDomainEvent;
import eu.royalblackwater.api.webhooks.service.WebhookHttpClient;
import eu.royalblackwater.api.webhooks.service.WebhookPolicy;
import eu.royalblackwater.api.webhooks.service.WebhookService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.assertj.core.api.Assertions.assertThat;
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

    @Test
    void automaticDeliveryRendersCustomTemplateAndHonorsScope() {
        WebhookRepository repository = mock(WebhookRepository.class);
        WebhookPolicy policy = mock(WebhookPolicy.class);
        WebhookHttpClient http = mock(WebhookHttpClient.class);
        FernetSecretBox secrets = mock(FernetSecretBox.class);
        Map<String, Object> matching = Map.of(
                "id", 3L, "endpoint_url", "encrypted", "event_types_json", "[\"fleet.created\"]",
                "scope_type", "fleet", "scope_id", 42L, "message_template", "Fleet {resource.id}: {data.summary}");
        Map<String, Object> differentFleet = Map.of(
                "id", 4L, "endpoint_url", "other", "event_types_json", "[\"fleet.created\"]",
                "scope_type", "fleet", "scope_id", 99L);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(matching, differentFleet));
        when(repository.insertReturningId(anyString(), anyMap())).thenReturn(8L);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of(
                "attempts", 1L, "created_at", LocalDateTime.of(2026, 8, 9, 20, 0),
                "delivery_id", "delivery", "event_type", "fleet.created", "id", 8L,
                "resource_id", "42", "resource_type", "fleet", "status", "delivered",
                "webhook_id", 3L, "webhook_name", "Fleet events")));
        when(policy.events(List.of("fleet.created"), false)).thenReturn(List.of("fleet.created"));
        when(secrets.decrypt("encrypted")).thenReturn("https://discord.com/api/webhooks/1/token");
        when(policy.endpoint(anyString())).thenAnswer(invocation -> invocation.getArgument(0));
        when(http.send(anyString(), anyString())).thenReturn(new WebhookHttpClient.Result(204, "", true, null));
        WebhookService service = new WebhookService(repository, policy, http, secrets,
                new ObjectMapper(), mock(AuditService.class), CLOCK);

        service.publish(new WebhookDomainEvent("fleet.created", "fleet", "42", "fleet", 42L,
                ACTOR, "Fleet Aurora was created.", LocalDateTime.of(2026, 8, 9, 20, 0)));

        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).insertReturningId(anyString(), parameters.capture());
        String payload = String.valueOf(parameters.getValue().get("payload"));
        assertThat(payload).contains(
                "Fleet 42: Fleet Aurora was created.",
                "allowed_mentions",
                "\"avatar_url\":\"https://royal-blackwater-fleet.eu/rbf-fleet-icon.png\"");
    }

    private static WebhookService service(WebhookRepository repository, WebhookPolicy policy) {
        return new WebhookService(repository, policy, mock(WebhookHttpClient.class), mock(FernetSecretBox.class),
                new ObjectMapper(), mock(AuditService.class), CLOCK);
    }
}
