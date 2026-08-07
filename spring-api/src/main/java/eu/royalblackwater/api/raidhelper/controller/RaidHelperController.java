package eu.royalblackwater.api.raidhelper.controller;

import eu.royalblackwater.api.dto.RaidHelperDestinationRead;
import eu.royalblackwater.api.dto.RaidHelperDestinationTestRequest;
import eu.royalblackwater.api.dto.RaidHelperDestinationWrite;
import eu.royalblackwater.api.dto.RaidHelperOptionDestination;
import eu.royalblackwater.api.dto.RaidHelperProfileCreate;
import eu.royalblackwater.api.dto.RaidHelperProfileRead;
import eu.royalblackwater.api.dto.RaidHelperProfileTestResult;
import eu.royalblackwater.api.dto.RaidHelperProfileWrite;
import eu.royalblackwater.api.dto.RaidHelperTemplateRead;
import eu.royalblackwater.api.dto.RaidHelperTemplateWrite;
import eu.royalblackwater.api.raidhelper.service.RaidHelperDestinationService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperLinkService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperProbeService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperProfileService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperTemplateService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class RaidHelperController extends ApiControllerSupport {

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

    @GetMapping("/api/admin/raid-helper/destinations")
    public ResponseEntity<List<RaidHelperDestinationRead>> destinations() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(destinations.list(actor), 200);
    }

    @PostMapping("/api/admin/raid-helper/destinations")
    public ResponseEntity<RaidHelperDestinationRead> destinationCreate(
            @Valid @RequestBody RaidHelperDestinationWrite body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(destinations.create(actor, body), 201);
    }

    @DeleteMapping("/api/admin/raid-helper/destinations/{destination_id}")
    public ResponseEntity<Void> destinationDelete(
            @PathVariable("destination_id") long destinationId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        destinations.delete(actor, destinationId); return noContent();
    }

    @PutMapping("/api/admin/raid-helper/destinations/{destination_id}")
    public ResponseEntity<RaidHelperDestinationRead> destinationUpdate(
            @PathVariable("destination_id") long destinationId,
            @Valid @RequestBody RaidHelperDestinationWrite body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(destinations.update(actor, destinationId,
                                    body), 200);
    }

    @PostMapping("/api/admin/raid-helper/destinations/{destination_id}/test")
    public ResponseEntity<RaidHelperProfileTestResult> destinationTest(
            @PathVariable("destination_id") long destinationId,
            @Valid @RequestBody RaidHelperDestinationTestRequest body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(probes.destination(actor, destinationId,
                                    body), 200);
    }

    @GetMapping("/api/admin/raid-helper/profiles")
    public ResponseEntity<List<RaidHelperProfileRead>> profiles() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(profiles.list(actor), 200);
    }

    @PostMapping("/api/admin/raid-helper/profiles")
    public ResponseEntity<RaidHelperProfileRead> profileCreate(
            @Valid @RequestBody RaidHelperProfileCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(profiles.create(actor, body), 201);
    }

    @DeleteMapping("/api/admin/raid-helper/profiles/{profile_id}")
    public ResponseEntity<Void> profileDelete(
            @PathVariable("profile_id") long profileId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        profiles.delete(actor, profileId); return noContent();
    }

    @PutMapping("/api/admin/raid-helper/profiles/{profile_id}")
    public ResponseEntity<RaidHelperProfileRead> profileUpdate(
            @PathVariable("profile_id") long profileId,
            @Valid @RequestBody RaidHelperProfileWrite body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(profiles.update(actor, profileId, body), 200);
    }

    @PostMapping("/api/admin/raid-helper/profiles/{profile_id}/test")
    public ResponseEntity<RaidHelperProfileTestResult> profileTest(
            @PathVariable("profile_id") long profileId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(probes.profile(actor, profileId), 200);
    }

    @GetMapping("/api/admin/raid-helper/templates")
    public ResponseEntity<List<RaidHelperTemplateRead>> templates() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(templates.list(actor), 200);
    }

    @PostMapping("/api/admin/raid-helper/templates")
    public ResponseEntity<RaidHelperTemplateRead> templateCreate(
            @Valid @RequestBody RaidHelperTemplateWrite body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(templates.create(actor, body), 201);
    }

    @DeleteMapping("/api/admin/raid-helper/templates/{template_id}")
    public ResponseEntity<Void> templateDelete(
            @PathVariable("template_id") long templateId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        templates.delete(actor, templateId); return noContent();
    }

    @PutMapping("/api/admin/raid-helper/templates/{template_id}")
    public ResponseEntity<RaidHelperTemplateRead> templateUpdate(
            @PathVariable("template_id") long templateId,
            @Valid @RequestBody RaidHelperTemplateWrite body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(templates.update(actor, templateId, body), 200);
    }

    @GetMapping("/api/calendar/raid-helper/options")
    public ResponseEntity<List<RaidHelperOptionDestination>> options(
            @RequestParam(name = "category", required = true) String category,
            @RequestParam(name = "squad_id", required = false) Long squadId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(links.options(actor,
                            category, squadId), 200);
    }
}
