package eu.royalblackwater.api.raidhelper.controller;

import eu.royalblackwater.api.dto.RaidHelperDestinationRead;
import eu.royalblackwater.api.dto.RaidHelperOptionDestination;
import eu.royalblackwater.api.dto.RaidHelperProfileRead;
import eu.royalblackwater.api.dto.RaidHelperProfileTestResult;
import eu.royalblackwater.api.dto.RaidHelperTemplateRead;
import java.util.List;
import eu.royalblackwater.api.dto.RaidHelperDestinationTestRequest;
import eu.royalblackwater.api.dto.RaidHelperDestinationWrite;
import eu.royalblackwater.api.dto.RaidHelperProfileCreate;
import eu.royalblackwater.api.dto.RaidHelperProfileWrite;
import eu.royalblackwater.api.dto.RaidHelperTemplateWrite;
import eu.royalblackwater.api.contract.api.AdminRaidHelperApi;
import eu.royalblackwater.api.contract.api.CalendarRaidHelperApi;
import eu.royalblackwater.api.raidhelper.service.RaidHelperDestinationService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperLinkService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperProbeService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperProfileService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperTemplateService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class RaidHelperController extends ApiControllerSupport implements AdminRaidHelperApi, CalendarRaidHelperApi {

    private final RaidHelperProfileService profiles;
    private final RaidHelperDestinationService destinations;
    private final RaidHelperTemplateService templates;
    private final RaidHelperProbeService probes;
    private final RaidHelperLinkService links;

    public RaidHelperController(RaidHelperProfileService profiles,
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
    public ResponseEntity<List<RaidHelperDestinationRead>> destinations() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(destinations.list(actor), 200);
    }

    @Override
    public ResponseEntity<RaidHelperDestinationRead> destinationCreate(
            RaidHelperDestinationWrite body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(destinations.create(actor, body), 201);
    }

    @Override
    public ResponseEntity<Void> destinationDelete(
            long destinationId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        destinations.delete(actor, destinationId); return noContent();
    }

    @Override
    public ResponseEntity<RaidHelperDestinationRead> destinationUpdate(
            long destinationId,
            RaidHelperDestinationWrite body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(destinations.update(actor, destinationId,
                                    body), 200);
    }

    @Override
    public ResponseEntity<RaidHelperProfileTestResult> destinationTest(
            long destinationId,
            RaidHelperDestinationTestRequest body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(probes.destination(actor, destinationId,
                                    body), 200);
    }

    @Override
    public ResponseEntity<List<RaidHelperProfileRead>> profiles() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(profiles.list(actor), 200);
    }

    @Override
    public ResponseEntity<RaidHelperProfileRead> profileCreate(
            RaidHelperProfileCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(profiles.create(actor, body), 201);
    }

    @Override
    public ResponseEntity<Void> profileDelete(
            long profileId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        profiles.delete(actor, profileId); return noContent();
    }

    @Override
    public ResponseEntity<RaidHelperProfileRead> profileUpdate(
            long profileId,
            RaidHelperProfileWrite body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(profiles.update(actor, profileId, body), 200);
    }

    @Override
    public ResponseEntity<RaidHelperProfileTestResult> profileTest(
            long profileId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(probes.profile(actor, profileId), 200);
    }

    @Override
    public ResponseEntity<List<RaidHelperTemplateRead>> templates() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(templates.list(actor), 200);
    }

    @Override
    public ResponseEntity<RaidHelperTemplateRead> templateCreate(
            RaidHelperTemplateWrite body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(templates.create(actor, body), 201);
    }

    @Override
    public ResponseEntity<Void> templateDelete(
            long templateId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        templates.delete(actor, templateId); return noContent();
    }

    @Override
    public ResponseEntity<RaidHelperTemplateRead> templateUpdate(
            long templateId,
            RaidHelperTemplateWrite body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(templates.update(actor, templateId, body), 200);
    }

    @Override
    public ResponseEntity<List<RaidHelperOptionDestination>> options(
            String category,
            Long squadId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(links.options(actor,
                            category, squadId), 200);
    }
}
