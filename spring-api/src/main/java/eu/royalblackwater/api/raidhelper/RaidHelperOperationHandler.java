package eu.royalblackwater.api.raidhelper;

import eu.royalblackwater.api.contract.RaidHelperDestinationTestRequest;
import eu.royalblackwater.api.contract.RaidHelperDestinationWrite;
import eu.royalblackwater.api.contract.RaidHelperProfileCreate;
import eu.royalblackwater.api.contract.RaidHelperProfileWrite;
import eu.royalblackwater.api.contract.RaidHelperTemplateWrite;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class RaidHelperOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "profiles_api_admin_raid_helper_profiles_get",
            "profile_create_api_admin_raid_helper_profiles_post",
            "profile_update_api_admin_raid_helper_profiles__profile_id__put",
            "profile_delete_api_admin_raid_helper_profiles__profile_id__delete",
            "profile_test_api_admin_raid_helper_profiles__profile_id__test_post",
            "destinations_api_admin_raid_helper_destinations_get",
            "destination_create_api_admin_raid_helper_destinations_post",
            "destination_update_api_admin_raid_helper_destinations__destination_id__put",
            "destination_delete_api_admin_raid_helper_destinations__destination_id__delete",
            "destination_test_api_admin_raid_helper_destinations__destination_id__test_post",
            "templates_api_admin_raid_helper_templates_get",
            "template_create_api_admin_raid_helper_templates_post",
            "template_update_api_admin_raid_helper_templates__template_id__put",
            "template_delete_api_admin_raid_helper_templates__template_id__delete",
            "options_api_calendar_raid_helper_options_get");

    private final RaidHelperProfileService profiles;
    private final RaidHelperDestinationService destinations;
    private final RaidHelperTemplateService templates;
    private final RaidHelperProbeService probes;
    private final RaidHelperLinkService links;

    public RaidHelperOperationHandler(RaidHelperProfileService profiles,
                                      RaidHelperDestinationService destinations,
                                      RaidHelperTemplateService templates,
                                      RaidHelperProbeService probes, RaidHelperLinkService links) {
        this.profiles = profiles;
        this.destinations = destinations;
        this.templates = templates;
        this.probes = probes;
        this.links = links;
    }

    @Override
    public Set<String> operations() {
        return OPERATIONS;
    }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "profiles_api_admin_raid_helper_profiles_get" -> profiles.list(actor);
            case "profile_create_api_admin_raid_helper_profiles_post" ->
                    profiles.create(actor, body(body, RaidHelperProfileCreate.class));
            case "profile_update_api_admin_raid_helper_profiles__profile_id__put" ->
                    profiles.update(actor, longParameter(parameters, "profile_id"), body(body, RaidHelperProfileWrite.class));
            case "profile_delete_api_admin_raid_helper_profiles__profile_id__delete" -> {
                profiles.delete(actor, longParameter(parameters, "profile_id")); yield null;
            }
            case "profile_test_api_admin_raid_helper_profiles__profile_id__test_post" ->
                    probes.profile(actor, longParameter(parameters, "profile_id"));
            case "destinations_api_admin_raid_helper_destinations_get" -> destinations.list(actor);
            case "destination_create_api_admin_raid_helper_destinations_post" ->
                    destinations.create(actor, body(body, RaidHelperDestinationWrite.class));
            case "destination_update_api_admin_raid_helper_destinations__destination_id__put" ->
                    destinations.update(actor, longParameter(parameters, "destination_id"),
                            body(body, RaidHelperDestinationWrite.class));
            case "destination_delete_api_admin_raid_helper_destinations__destination_id__delete" -> {
                destinations.delete(actor, longParameter(parameters, "destination_id")); yield null;
            }
            case "destination_test_api_admin_raid_helper_destinations__destination_id__test_post" ->
                    probes.destination(actor, longParameter(parameters, "destination_id"),
                            body(body, RaidHelperDestinationTestRequest.class));
            case "templates_api_admin_raid_helper_templates_get" -> templates.list(actor);
            case "template_create_api_admin_raid_helper_templates_post" ->
                    templates.create(actor, body(body, RaidHelperTemplateWrite.class));
            case "template_update_api_admin_raid_helper_templates__template_id__put" ->
                    templates.update(actor, longParameter(parameters, "template_id"), body(body, RaidHelperTemplateWrite.class));
            case "template_delete_api_admin_raid_helper_templates__template_id__delete" -> {
                templates.delete(actor, longParameter(parameters, "template_id")); yield null;
            }
            case "options_api_calendar_raid_helper_options_get" -> links.options(actor,
                    stringParameter(parameters, "category"), nullableLong(parameters.get("squad_id")));
            default -> throw new IllegalStateException("Unsupported Raid-Helper operation: " + operationId);
        };
    }

    private static Long nullableLong(Object value) {
        return value instanceof Number number ? number.longValue() : null;
    }
}
