package eu.royalblackwater.api.securityops.controller;

import eu.royalblackwater.api.dto.IpBlockRead;
import eu.royalblackwater.api.dto.IpBlockSummary;
import eu.royalblackwater.api.dto.SecurityDashboard;
import java.util.List;
import eu.royalblackwater.api.dto.IpBlockCreate;
import eu.royalblackwater.api.dto.IpBlockUnblock;
import eu.royalblackwater.api.contract.api.AdminIpBlocksApi;
import eu.royalblackwater.api.contract.api.AdminLogsApi;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.securityops.service.IpBlockService;
import eu.royalblackwater.api.securityops.service.SecurityDashboardService;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class SecurityAdministrationController extends ApiControllerSupport implements AdminIpBlocksApi, AdminLogsApi {

    private final IpBlockService blocks;private final SecurityDashboardService dashboard;
    public SecurityAdministrationController(IpBlockService blocks,SecurityDashboardService dashboard){this.blocks=blocks;this.dashboard=dashboard;}

    @Override
    public ResponseEntity<List<IpBlockRead>> adminListIpBlocks(
            String status,
            String search,
            long limit
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(blocks.list(status,search,limit), 200);
    }

    @Override
    public ResponseEntity<IpBlockRead> adminCreateIpBlock(
            IpBlockCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(blocks.create(actor,body), 201);
    }

    @Override
    public ResponseEntity<IpBlockSummary> adminIpBlockSummary() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(blocks.summary(), 200);
    }

    @Override
    public ResponseEntity<IpBlockRead> adminUnblockIp(
            long blockId,
            IpBlockUnblock body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(blocks.unblock(actor,blockId,body), 200);
    }

    @Override
    public ResponseEntity<SecurityDashboard> adminSecurityDashboard(
            LocalDate fromDate,
            LocalDate toDate,
            String threatLevel,
            String clientIp,
            String sort,
            long limit
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(dashboard.build(fromDate,toDate,
                            threatLevel,clientIp,sort,limit), 200);
    }
    private static LocalDate date(Map<String,Object> parameters,String key){return parameters.get(key) instanceof LocalDate value?value:null;}
}
