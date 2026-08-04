package eu.royalblackwater.api.operations;

import eu.royalblackwater.api.contract.*;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class OperationsOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS=Set.of(
            "admin_apply_backup_enrollment_api_admin_backups_enrollment_apply_post","admin_backup_status_api_admin_backups_status_get",
            "admin_configure_backup_host_api_admin_backups_configuration_put","admin_delete_backup_configuration_api_admin_backups_configuration_delete",
            "admin_discover_backup_host_api_admin_backups_discover_post","admin_prepare_backup_enrollment_api_admin_backups_enrollment_prepare_post",
            "admin_prepare_backup_upload_key_api_admin_backups_key_prepare_post","admin_restore_local_database_backup_api_admin_backups_local_restore_post",
            "admin_restore_local_files_backup_api_admin_backups_local_files_restore_post","admin_run_application_backup_api_admin_backups_run_post",
            "admin_scan_local_database_backups_api_admin_backups_local_scan_post","admin_test_backup_connection_api_admin_backups_test_post",
            "admin_request_system_update_api_admin_system_update_post","admin_system_update_status_api_admin_system_update_get");
    private final BackupControlService backups;private final SystemUpdateService updates;
    public OperationsOperationHandler(BackupControlService backups,SystemUpdateService updates){this.backups=backups;this.updates=updates;}
    @Override public Set<String> operations(){return OPERATIONS;}
    @Override protected Object execute(String operationId,Map<String,Object> parameters,Object request,MultipartFile upload){
        AuthenticatedUser actor=CurrentUser.require();
        return switch(operationId){
            case "admin_backup_status_api_admin_backups_status_get" -> backups.status();
            case "admin_prepare_backup_upload_key_api_admin_backups_key_prepare_post" -> backups.prepareKey(actor);
            case "admin_prepare_backup_enrollment_api_admin_backups_enrollment_prepare_post" -> backups.prepareEnrollment(actor);
            case "admin_apply_backup_enrollment_api_admin_backups_enrollment_apply_post" -> backups.applyEnrollment(actor,body(request,BackupEnrollmentResponseRequest.class));
            case "admin_discover_backup_host_api_admin_backups_discover_post" -> backups.discover(actor,body(request,BackupDiscoveryRequest.class));
            case "admin_configure_backup_host_api_admin_backups_configuration_put" -> backups.configure(actor,body(request,BackupConfigurationRequest.class));
            case "admin_delete_backup_configuration_api_admin_backups_configuration_delete" -> backups.deleteConfiguration(actor);
            case "admin_test_backup_connection_api_admin_backups_test_post" -> backups.test(actor);
            case "admin_run_application_backup_api_admin_backups_run_post" -> backups.run(actor);
            case "admin_scan_local_database_backups_api_admin_backups_local_scan_post" -> backups.scan(actor);
            case "admin_restore_local_database_backup_api_admin_backups_local_restore_post" -> backups.restoreDatabase(actor,body(request,DatabaseRestoreRequest.class));
            case "admin_restore_local_files_backup_api_admin_backups_local_files_restore_post" -> backups.restoreFiles(actor,body(request,FilesRestoreRequest.class));
            case "admin_system_update_status_api_admin_system_update_get" -> updates.status();
            case "admin_request_system_update_api_admin_system_update_post" -> updates.request(actor,body(request,SystemUpdateRequest.class).operation());
            default -> throw new IllegalArgumentException("Unsupported operations request: "+operationId);
        };
    }
}
