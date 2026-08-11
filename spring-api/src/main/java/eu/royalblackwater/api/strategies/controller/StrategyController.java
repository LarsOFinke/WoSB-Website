package eu.royalblackwater.api.strategies.controller;

import eu.royalblackwater.api.dto.StrategyCreate;
import eu.royalblackwater.api.dto.StrategyRead;
import eu.royalblackwater.api.dto.StrategySummary;
import eu.royalblackwater.api.dto.StrategyUpdate;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.strategies.service.StrategyService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class StrategyController extends ApiControllerSupport {
    private final StrategyService strategies;

    public StrategyController(StrategyService strategies) {
        this.strategies = strategies;
    }

    @GetMapping("/api/strategies")
    public ResponseEntity<List<StrategySummary>> getStrategies() {
        return respond(strategies.mine(CurrentUser.require()), 200);
    }

    @PostMapping("/api/strategies")
    public ResponseEntity<StrategyRead> postStrategy(@Valid @RequestBody StrategyCreate body) {
        return respond(strategies.create(body, CurrentUser.require()), 201);
    }

    @GetMapping("/api/strategies/{strategy_id}")
    public ResponseEntity<StrategyRead> getStrategy(@PathVariable("strategy_id") long strategyId) {
        return respond(strategies.get(strategyId, CurrentUser.require()), 200);
    }

    @PutMapping("/api/strategies/{strategy_id}")
    public ResponseEntity<StrategyRead> putStrategy(@PathVariable("strategy_id") long strategyId,
                                                     @Valid @RequestBody StrategyUpdate body) {
        return respond(strategies.update(strategyId, body, CurrentUser.require()), 200);
    }

    @DeleteMapping("/api/strategies/{strategy_id}")
    public ResponseEntity<Void> deleteStrategy(@PathVariable("strategy_id") long strategyId) {
        strategies.delete(strategyId, CurrentUser.require());
        return noContent();
    }

    @PutMapping("/api/strategies/{strategy_id}/publication")
    public ResponseEntity<StrategyRead> putStrategyPublication(@PathVariable("strategy_id") long strategyId) {
        return respond(strategies.publication(strategyId, true, CurrentUser.require()), 200);
    }

    @DeleteMapping("/api/strategies/{strategy_id}/publication")
    public ResponseEntity<StrategyRead> deleteStrategyPublication(@PathVariable("strategy_id") long strategyId) {
        return respond(strategies.publication(strategyId, false, CurrentUser.require()), 200);
    }

    @GetMapping("/api/strategies/shared/{public_id}")
    public ResponseEntity<StrategyRead> getSharedStrategy(@PathVariable("public_id") String publicId) {
        return respond(strategies.shared(publicId), 200);
    }
}
