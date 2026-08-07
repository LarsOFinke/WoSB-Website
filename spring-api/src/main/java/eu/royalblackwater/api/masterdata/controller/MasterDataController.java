package eu.royalblackwater.api.masterdata.controller;

import eu.royalblackwater.api.dto.MasterDataCategoryCreate;
import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.dto.MasterDataCategoryUpdate;
import eu.royalblackwater.api.dto.MasterDataOptionCreate;
import eu.royalblackwater.api.dto.MasterDataOptionRead;
import eu.royalblackwater.api.dto.MasterDataOptionUpdate;
import eu.royalblackwater.api.dto.MasterDataOverview;
import eu.royalblackwater.api.dto.MasterDataSeedRestoreSummary;
import eu.royalblackwater.api.dto.MasterDataShipCreate;
import eu.royalblackwater.api.dto.MasterDataShipRead;
import eu.royalblackwater.api.dto.MasterDataShipUpdate;
import eu.royalblackwater.api.dto.MasterDataTaxonomyRead;
import eu.royalblackwater.api.masterdata.service.MasterDataMutationService;
import eu.royalblackwater.api.masterdata.service.MasterDataQueryService;
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
public class MasterDataController extends ApiControllerSupport {

    private final MasterDataQueryService queries;
    private final MasterDataMutationService mutations;

    public MasterDataController(MasterDataQueryService queries,MasterDataMutationService mutations){
        this.queries=queries;this.mutations=mutations;
    }

    @GetMapping("/api/admin/master-data/categories")
    public ResponseEntity<List<MasterDataCategoryRead>> categories() {
        CurrentUser.require();
        return respond(queries.categories(), 200);
    }

    @PostMapping("/api/admin/master-data/categories")
    public ResponseEntity<MasterDataCategoryRead> postCategory(
            @Valid @RequestBody MasterDataCategoryCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.createCategory(actor,body), 201);
    }

    @DeleteMapping("/api/admin/master-data/categories/{category_id}")
    public ResponseEntity<Void> deleteCategory(
            @PathVariable("category_id") long categoryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        mutations.deleteCategory(actor,categoryId); return noContent();
    }

    @PutMapping("/api/admin/master-data/categories/{category_id}")
    public ResponseEntity<MasterDataCategoryRead> putCategory(
            @PathVariable("category_id") long categoryId,
            @Valid @RequestBody MasterDataCategoryUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.updateCategory(actor,categoryId,body), 200);
    }

    @PostMapping("/api/admin/master-data/categories/{category_id}/restore-seed")
    public ResponseEntity<MasterDataCategoryRead> restoreCategory(
            @PathVariable("category_id") long categoryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreCategory(actor,categoryId), 200);
    }

    @GetMapping("/api/admin/master-data/options")
    public ResponseEntity<List<MasterDataOptionRead>> options(
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "search", required = false) String search
    ) {
        CurrentUser.require();
        return respond(queries.options(), 200);
    }

    @PostMapping("/api/admin/master-data/options")
    public ResponseEntity<MasterDataOptionRead> postOption(
            @Valid @RequestBody MasterDataOptionCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.createOption(actor,body), 201);
    }

    @DeleteMapping("/api/admin/master-data/options/{option_id}")
    public ResponseEntity<Void> deleteOption(
            @PathVariable("option_id") long optionId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        mutations.deleteOption(actor,optionId); return noContent();
    }

    @PutMapping("/api/admin/master-data/options/{option_id}")
    public ResponseEntity<MasterDataOptionRead> putOption(
            @PathVariable("option_id") long optionId,
            @Valid @RequestBody MasterDataOptionUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.updateOption(actor,optionId,body), 200);
    }

    @PostMapping("/api/admin/master-data/options/{option_id}/restore-seed")
    public ResponseEntity<MasterDataOptionRead> restoreOption(
            @PathVariable("option_id") long optionId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreOption(actor,optionId), 200);
    }

    @GetMapping("/api/admin/master-data/overview")
    public ResponseEntity<MasterDataOverview> overview() {
        CurrentUser.require();
        return respond(queries.overview(), 200);
    }

    @PostMapping("/api/admin/master-data/restore-seed-defaults")
    public ResponseEntity<MasterDataSeedRestoreSummary> restoreSeedDefaults() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreAll(actor), 200);
    }

    @GetMapping("/api/admin/master-data/ships")
    public ResponseEntity<List<MasterDataShipRead>> ships(
            @RequestParam(name = "search", required = false) String search
    ) {
        CurrentUser.require();
        return respond(queries.ships(), 200);
    }

    @PostMapping("/api/admin/master-data/ships")
    public ResponseEntity<MasterDataShipRead> postShip(
            @Valid @RequestBody MasterDataShipCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.createShip(actor,body), 201);
    }

    @DeleteMapping("/api/admin/master-data/ships/{ship_id}")
    public ResponseEntity<Void> deleteShip(
            @PathVariable("ship_id") long shipId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        mutations.deleteShip(actor,shipId); return noContent();
    }

    @PutMapping("/api/admin/master-data/ships/{ship_id}")
    public ResponseEntity<MasterDataShipRead> putShip(
            @PathVariable("ship_id") long shipId,
            @Valid @RequestBody MasterDataShipUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.updateShip(actor,shipId,body), 200);
    }

    @PostMapping("/api/admin/master-data/ships/{ship_id}/restore-seed")
    public ResponseEntity<MasterDataShipRead> restoreShip(
            @PathVariable("ship_id") long shipId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreShip(actor,shipId), 200);
    }

    @GetMapping("/api/admin/master-data/taxonomy")
    public ResponseEntity<MasterDataTaxonomyRead> taxonomy() {
        CurrentUser.require();
        return respond(queries.taxonomy(), 200);
    }
}
