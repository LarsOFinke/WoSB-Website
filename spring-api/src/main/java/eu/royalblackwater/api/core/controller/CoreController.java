package eu.royalblackwater.api.core.controller;

import eu.royalblackwater.api.core.service.CoreService;
import eu.royalblackwater.api.dto.HealthStatusRead;
import eu.royalblackwater.api.dto.HomeRead;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class CoreController extends ApiControllerSupport {
    private final CoreService service;

    public CoreController(CoreService service) {
        this.service = service;
    }

    @GetMapping("/api/health")
    public ResponseEntity<HealthStatusRead> healthCheck() {
        return respond(service.health(), 200);
    }

    @GetMapping("/api/health/ready")
    public ResponseEntity<HealthStatusRead> readinessCheck() {
        return respond(service.readiness(), 200);
    }

    @GetMapping("/api/home")
    public ResponseEntity<HomeRead> getHome() {
        return respond(service.home(), 200);
    }
}
