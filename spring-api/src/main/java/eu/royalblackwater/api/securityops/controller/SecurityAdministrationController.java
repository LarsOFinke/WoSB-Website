package eu.royalblackwater.api.securityops.controller;

import eu.royalblackwater.api.dto.IpBlockCreate;
import eu.royalblackwater.api.dto.IpBlockRead;
import eu.royalblackwater.api.dto.IpBlockSummary;
import eu.royalblackwater.api.dto.IpBlockUnblock;
import eu.royalblackwater.api.dto.SecurityDashboard;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.securityops.service.IpBlockService;
import eu.royalblackwater.api.securityops.service.SecurityDashboardService;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class SecurityAdministrationController extends ApiControllerSupport {

    private final IpBlockService blocks;private final SecurityDashboardService dashboard;
    public SecurityAdministrationController(IpBlockService blocks,SecurityDashboardService dashboard){this.blocks=blocks;this.dashboard=dashboard;}

    @GetMapping("/api/admin/ip-blocks")
    public ResponseEntity<List<IpBlockRead>> adminListIpBlocks(
            @RequestParam(name = "status", defaultValue = "active") String status,
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "limit", defaultValue = "200") long limit
    ) {

        CurrentUser.require();
        return respond(blocks.list(status,search,limit), 200);
    }

    @PostMapping("/api/admin/ip-blocks")
    public ResponseEntity<IpBlockRead> adminCreateIpBlock(
            @Valid @RequestBody IpBlockCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(blocks.create(actor,body), 201);
    }

    @GetMapping("/api/admin/ip-blocks/summary")
    public ResponseEntity<IpBlockSummary> adminIpBlockSummary() {
        CurrentUser.require();
        return respond(blocks.summary(), 200);
    }

    @PostMapping("/api/admin/ip-blocks/{block_id}/unblock")
    public ResponseEntity<IpBlockRead> adminUnblockIp(
            @PathVariable("block_id") long blockId,
            @Valid @RequestBody IpBlockUnblock body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(blocks.unblock(actor,blockId,body), 200);
    }

    @GetMapping("/api/admin/logs/security-dashboard")
    public ResponseEntity<SecurityDashboard> adminSecurityDashboard(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) @RequestParam(name = "from_date", required = false) LocalDate fromDate,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) @RequestParam(name = "to_date", required = false) LocalDate toDate,
            @RequestParam(name = "threat_level", required = false) String threatLevel,
            @RequestParam(name = "client_ip", required = false) String clientIp,
            @RequestParam(name = "sort", defaultValue = "threat") String sort,
            @RequestParam(name = "limit", defaultValue = "100") long limit
    ) {

        CurrentUser.require();
        return respond(dashboard.build(fromDate,toDate,
                            threatLevel,clientIp,sort,limit), 200);
    }
}
