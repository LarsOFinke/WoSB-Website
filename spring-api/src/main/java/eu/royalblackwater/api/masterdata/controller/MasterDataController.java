package eu.royalblackwater.api.masterdata.controller;

import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.dto.MasterDataOptionRead;
import eu.royalblackwater.api.dto.MasterDataOverview;
import eu.royalblackwater.api.dto.MasterDataSeedRestoreSummary;
import eu.royalblackwater.api.dto.MasterDataShipRead;
import eu.royalblackwater.api.dto.MasterDataTaxonomyRead;
import java.util.List;
import eu.royalblackwater.api.dto.MasterDataCategoryCreate;
import eu.royalblackwater.api.dto.MasterDataCategoryUpdate;
import eu.royalblackwater.api.dto.MasterDataOptionCreate;
import eu.royalblackwater.api.dto.MasterDataOptionUpdate;
import eu.royalblackwater.api.dto.MasterDataShipCreate;
import eu.royalblackwater.api.dto.MasterDataShipUpdate;
import eu.royalblackwater.api.contract.api.AdminMasterDataApi;
import eu.royalblackwater.api.masterdata.service.MasterDataMutationService;
import eu.royalblackwater.api.masterdata.service.MasterDataQueryService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class MasterDataController extends ApiControllerSupport implements AdminMasterDataApi {

    private final MasterDataQueryService queries;
    private final MasterDataMutationService mutations;

    public MasterDataController(MasterDataQueryService queries,MasterDataMutationService mutations){
        this.queries=queries;this.mutations=mutations;
    }

    @Override
    public ResponseEntity<List<MasterDataCategoryRead>> categories() {
        CurrentUser.require();
        return respond(queries.categories(), 200);
    }

    @Override
    public ResponseEntity<MasterDataCategoryRead> postCategory(
            MasterDataCategoryCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.createCategory(actor,body), 201);
    }

    @Override
    public ResponseEntity<Void> deleteCategory(
            long categoryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        mutations.deleteCategory(actor,categoryId); return noContent();
    }

    @Override
    public ResponseEntity<MasterDataCategoryRead> putCategory(
            long categoryId,
            MasterDataCategoryUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.updateCategory(actor,categoryId,body), 200);
    }

    @Override
    public ResponseEntity<MasterDataCategoryRead> restoreCategory(
            long categoryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreCategory(actor,categoryId), 200);
    }

    @Override
    public ResponseEntity<List<MasterDataOptionRead>> options(
            String category,
            String search
    ) {
        CurrentUser.require();
        return respond(queries.options(), 200);
    }

    @Override
    public ResponseEntity<MasterDataOptionRead> postOption(
            MasterDataOptionCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.createOption(actor,body), 201);
    }

    @Override
    public ResponseEntity<Void> deleteOption(
            long optionId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        mutations.deleteOption(actor,optionId); return noContent();
    }

    @Override
    public ResponseEntity<MasterDataOptionRead> putOption(
            long optionId,
            MasterDataOptionUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.updateOption(actor,optionId,body), 200);
    }

    @Override
    public ResponseEntity<MasterDataOptionRead> restoreOption(
            long optionId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreOption(actor,optionId), 200);
    }

    @Override
    public ResponseEntity<MasterDataOverview> overview() {
        CurrentUser.require();
        return respond(queries.overview(), 200);
    }

    @Override
    public ResponseEntity<MasterDataSeedRestoreSummary> restoreSeedDefaults() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreAll(actor), 200);
    }

    @Override
    public ResponseEntity<List<MasterDataShipRead>> ships(
            String search
    ) {
        CurrentUser.require();
        return respond(queries.ships(), 200);
    }

    @Override
    public ResponseEntity<MasterDataShipRead> postShip(
            MasterDataShipCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.createShip(actor,body), 201);
    }

    @Override
    public ResponseEntity<Void> deleteShip(
            long shipId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        mutations.deleteShip(actor,shipId); return noContent();
    }

    @Override
    public ResponseEntity<MasterDataShipRead> putShip(
            long shipId,
            MasterDataShipUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.updateShip(actor,shipId,body), 200);
    }

    @Override
    public ResponseEntity<MasterDataShipRead> restoreShip(
            long shipId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(mutations.restoreShip(actor,shipId), 200);
    }

    @Override
    public ResponseEntity<MasterDataTaxonomyRead> taxonomy() {
        CurrentUser.require();
        return respond(queries.taxonomy(), 200);
    }
}
