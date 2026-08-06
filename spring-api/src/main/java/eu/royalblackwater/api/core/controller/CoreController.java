package eu.royalblackwater.api.core.controller;

import eu.royalblackwater.api.dto.HealthStatusRead;
import eu.royalblackwater.api.dto.HomeRead;
import eu.royalblackwater.api.contract.api.HealthApi;
import eu.royalblackwater.api.contract.api.HomeApi;
import eu.royalblackwater.api.core.service.CoreService;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class CoreController extends ApiControllerSupport implements HealthApi, HomeApi {
    private final CoreService service;

    public CoreController(CoreService service) {
        this.service = service;
    }

    @Override
    public ResponseEntity<HealthStatusRead> healthCheck() {
        return respond(service.health(), 200);
    }

    @Override
    public ResponseEntity<HealthStatusRead> readinessCheck() {
        return respond(service.readiness(), 200);
    }

    @Override
    public ResponseEntity<HomeRead> getHome() {
        return respond(service.home(), 200);
    }
}
