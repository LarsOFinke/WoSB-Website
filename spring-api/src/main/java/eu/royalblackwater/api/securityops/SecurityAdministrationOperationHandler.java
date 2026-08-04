package eu.royalblackwater.api.securityops;

import eu.royalblackwater.api.contract.IpBlockCreate;
import eu.royalblackwater.api.contract.IpBlockUnblock;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.time.LocalDate;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class SecurityAdministrationOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS=Set.of(
            "admin_list_ip_blocks_api_admin_ip_blocks_get","admin_create_ip_block_api_admin_ip_blocks_post",
            "admin_ip_block_summary_api_admin_ip_blocks_summary_get","admin_unblock_ip_api_admin_ip_blocks__block_id__unblock_post",
            "admin_security_dashboard_api_admin_logs_security_dashboard_get");
    private final IpBlockService blocks;private final SecurityDashboardService dashboard;
    public SecurityAdministrationOperationHandler(IpBlockService blocks,SecurityDashboardService dashboard){this.blocks=blocks;this.dashboard=dashboard;}
    @Override public Set<String> operations(){return OPERATIONS;}
    @Override protected Object execute(String operationId,Map<String,Object> parameters,Object request,MultipartFile upload){
        AuthenticatedUser actor=CurrentUser.require();
        return switch(operationId){
            case "admin_list_ip_blocks_api_admin_ip_blocks_get" -> blocks.list(stringParameter(parameters,"status"),stringParameter(parameters,"search"),longParameter(parameters,"limit"));
            case "admin_create_ip_block_api_admin_ip_blocks_post" -> blocks.create(actor,body(request,IpBlockCreate.class));
            case "admin_ip_block_summary_api_admin_ip_blocks_summary_get" -> blocks.summary();
            case "admin_unblock_ip_api_admin_ip_blocks__block_id__unblock_post" -> blocks.unblock(actor,longParameter(parameters,"block_id"),body(request,IpBlockUnblock.class));
            case "admin_security_dashboard_api_admin_logs_security_dashboard_get" -> dashboard.build(date(parameters,"from_date"),date(parameters,"to_date"),
                    stringParameter(parameters,"threat_level"),stringParameter(parameters,"client_ip"),stringParameter(parameters,"sort"),longParameter(parameters,"limit"));
            default -> throw new IllegalArgumentException("Unsupported security operation: "+operationId);
        };
    }
    private static LocalDate date(Map<String,Object> parameters,String key){return parameters.get(key) instanceof LocalDate value?value:null;}
}
