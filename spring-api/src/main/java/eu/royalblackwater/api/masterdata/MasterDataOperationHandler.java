package eu.royalblackwater.api.masterdata;

import eu.royalblackwater.api.contract.*;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class MasterDataOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS=Set.of(
            "overview_api_admin_master_data_overview_get","taxonomy_api_admin_master_data_taxonomy_get",
            "categories_api_admin_master_data_categories_get","post_category_api_admin_master_data_categories_post",
            "put_category_api_admin_master_data_categories__category_id__put","delete_category_api_admin_master_data_categories__category_id__delete",
            "restore_category_api_admin_master_data_categories__category_id__restore_seed_post",
            "options_api_admin_master_data_options_get","post_option_api_admin_master_data_options_post",
            "put_option_api_admin_master_data_options__option_id__put","delete_option_api_admin_master_data_options__option_id__delete",
            "restore_option_api_admin_master_data_options__option_id__restore_seed_post",
            "ships_api_admin_master_data_ships_get","post_ship_api_admin_master_data_ships_post",
            "put_ship_api_admin_master_data_ships__ship_id__put","delete_ship_api_admin_master_data_ships__ship_id__delete",
            "restore_ship_api_admin_master_data_ships__ship_id__restore_seed_post",
            "restore_seed_defaults_api_admin_master_data_restore_seed_defaults_post");
    private final MasterDataQueryService queries;
    private final MasterDataMutationService mutations;

    public MasterDataOperationHandler(MasterDataQueryService queries,MasterDataMutationService mutations){
        this.queries=queries;this.mutations=mutations;
    }
    @Override public Set<String> operations(){return OPERATIONS;}

    @Override protected Object execute(String operationId,Map<String,Object> parameters,Object request,MultipartFile upload){
        AuthenticatedUser actor=CurrentUser.require();
        return switch(operationId){
            case "overview_api_admin_master_data_overview_get" -> queries.overview();
            case "taxonomy_api_admin_master_data_taxonomy_get" -> queries.taxonomy();
            case "categories_api_admin_master_data_categories_get" -> queries.categories();
            case "post_category_api_admin_master_data_categories_post" -> mutations.createCategory(actor,body(request,MasterDataCategoryCreate.class));
            case "put_category_api_admin_master_data_categories__category_id__put" -> mutations.updateCategory(actor,longParameter(parameters,"category_id"),body(request,MasterDataCategoryUpdate.class));
            case "delete_category_api_admin_master_data_categories__category_id__delete" -> { mutations.deleteCategory(actor,longParameter(parameters,"category_id")); yield null; }
            case "restore_category_api_admin_master_data_categories__category_id__restore_seed_post" -> mutations.restoreCategory(actor,longParameter(parameters,"category_id"));
            case "options_api_admin_master_data_options_get" -> queries.options();
            case "post_option_api_admin_master_data_options_post" -> mutations.createOption(actor,body(request,MasterDataOptionCreate.class));
            case "put_option_api_admin_master_data_options__option_id__put" -> mutations.updateOption(actor,longParameter(parameters,"option_id"),body(request,MasterDataOptionUpdate.class));
            case "delete_option_api_admin_master_data_options__option_id__delete" -> { mutations.deleteOption(actor,longParameter(parameters,"option_id")); yield null; }
            case "restore_option_api_admin_master_data_options__option_id__restore_seed_post" -> mutations.restoreOption(actor,longParameter(parameters,"option_id"));
            case "ships_api_admin_master_data_ships_get" -> queries.ships();
            case "post_ship_api_admin_master_data_ships_post" -> mutations.createShip(actor,body(request,MasterDataShipCreate.class));
            case "put_ship_api_admin_master_data_ships__ship_id__put" -> mutations.updateShip(actor,longParameter(parameters,"ship_id"),body(request,MasterDataShipUpdate.class));
            case "delete_ship_api_admin_master_data_ships__ship_id__delete" -> { mutations.deleteShip(actor,longParameter(parameters,"ship_id")); yield null; }
            case "restore_ship_api_admin_master_data_ships__ship_id__restore_seed_post" -> mutations.restoreShip(actor,longParameter(parameters,"ship_id"));
            case "restore_seed_defaults_api_admin_master_data_restore_seed_defaults_post" -> mutations.restoreAll(actor);
            default -> throw new IllegalArgumentException("Unsupported master-data operation: "+operationId);
        };
    }
}
