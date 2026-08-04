package eu.royalblackwater.api.squads;

import eu.royalblackwater.api.contract.SquadCreate;
import eu.royalblackwater.api.contract.SquadMemberCreate;
import eu.royalblackwater.api.contract.SquadMemberUpdate;
import eu.royalblackwater.api.contract.SquadUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class SquadOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_squads_api_squads_get",
            "post_squad_api_squads_post",
            "get_my_squads_api_squads_mine_get",
            "get_squad_roster_api_squads_roster_get",
            "delete_squad_api_squads__squad_id__delete",
            "get_squad_detail_api_squads__squad_id__get",
            "put_squad_api_squads__squad_id__put",
            "post_squad_member_api_squads__squad_id__members_post",
            "delete_squad_member_api_squads__squad_id__members__member_id__delete",
            "put_squad_member_api_squads__squad_id__members__member_id__put");
    private final SquadService squads;

    public SquadOperationHandler(SquadService squads) {
        this.squads = squads;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody,
                             MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        long squadId = parameters.containsKey("squad_id") ? longParameter(parameters, "squad_id") : 0L;
        return switch (operationId) {
            case "get_squads_api_squads_get" -> squads.list(actor, SquadListFilter.from(parameters));
            case "post_squad_api_squads_post" -> squads.create(body(requestBody, SquadCreate.class), actor);
            case "get_my_squads_api_squads_mine_get" -> squads.list(actor, SquadListFilter.mine());
            case "get_squad_roster_api_squads_roster_get" -> squads.roster(actor);
            case "delete_squad_api_squads__squad_id__delete" -> {
                squads.archive(squadId, actor);
                yield null;
            }
            case "get_squad_detail_api_squads__squad_id__get" -> squads.get(squadId, actor);
            case "put_squad_api_squads__squad_id__put" -> squads.update(
                    squadId, body(requestBody, SquadUpdate.class), actor);
            case "post_squad_member_api_squads__squad_id__members_post" -> squads.addMember(
                    squadId, body(requestBody, SquadMemberCreate.class), actor);
            case "delete_squad_member_api_squads__squad_id__members__member_id__delete" -> squads.removeMember(
                    squadId, longParameter(parameters, "member_id"), actor);
            case "put_squad_member_api_squads__squad_id__members__member_id__put" -> squads.updateMember(
                    squadId, longParameter(parameters, "member_id"),
                    body(requestBody, SquadMemberUpdate.class), actor);
            default -> throw new IllegalStateException("Unsupported squad operation: " + operationId);
        };
    }

}
