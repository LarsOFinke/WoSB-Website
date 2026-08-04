package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.contract.BuildCreate;
import eu.royalblackwater.api.contract.BuildUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class BuildOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_builds_api_builds_get", "post_build_api_builds_post", "get_build_options_api_builds_options_get",
            "get_build_roles_api_builds_roles_get", "post_build_upvote_api_builds__build_id__upvote_post",
            "delete_build_upvote_api_builds__build_id__upvote_delete", "get_my_builds_api_builds_mine_get",
            "put_my_build_api_builds_mine__build_id__put", "delete_my_build_api_builds_mine__build_id__delete",
            "get_build_detail_api_builds__build_id__get", "put_build_printout_api_builds__build_id__printout_put",
            "get_build_printout_api_builds__build_id__printout_get");
    private final BuildService builds;
    private final BuildPrintoutService printouts;

    public BuildOperationHandler(BuildService builds, BuildPrintoutService printouts) {
        this.builds = builds; this.printouts = printouts;
    }

    @Override public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody, MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "get_builds_api_builds_get" -> builds.list(stringParameter(parameters, "search"),
                    stringParameter(parameters, "build_type"), stringParameter(parameters, "classification"),
                    longParameter(parameters, "limit"), longParameter(parameters, "offset"), actor);
            case "post_build_api_builds_post" -> builds.create(body(requestBody, BuildCreate.class), actor);
            case "get_build_options_api_builds_options_get" -> builds.options(nullableLong(parameters, "ship_id"));
            case "get_build_roles_api_builds_roles_get" -> builds.roles();
            case "post_build_upvote_api_builds__build_id__upvote_post" -> builds.vote(longParameter(parameters, "build_id"), actor, true);
            case "delete_build_upvote_api_builds__build_id__upvote_delete" -> builds.vote(longParameter(parameters, "build_id"), actor, false);
            case "get_my_builds_api_builds_mine_get" -> builds.mine(stringParameter(parameters, "search"),
                    stringParameter(parameters, "build_type"), stringParameter(parameters, "classification"),
                    longParameter(parameters, "limit"), longParameter(parameters, "offset"), actor);
            case "put_my_build_api_builds_mine__build_id__put" -> builds.update(longParameter(parameters, "build_id"),
                    body(requestBody, BuildUpdate.class), actor);
            case "delete_my_build_api_builds_mine__build_id__delete" -> { builds.deleteOwned(longParameter(parameters, "build_id"), actor); yield null; }
            case "get_build_detail_api_builds__build_id__get" -> builds.get(longParameter(parameters, "build_id"), actor);
            case "put_build_printout_api_builds__build_id__printout_put" -> printouts.save(longParameter(parameters, "build_id"), upload, actor);
            case "get_build_printout_api_builds__build_id__printout_get" -> printouts.content(longParameter(parameters, "build_id"));
            default -> throw new IllegalStateException("Unsupported build operation: " + operationId);
        };
    }

    private static Long nullableLong(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name); return value instanceof Number number ? number.longValue() : null;
    }
}
