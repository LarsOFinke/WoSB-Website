package eu.royalblackwater.api.operations.controller;

import eu.royalblackwater.api.dto.BackupControlRequestResult;
import eu.royalblackwater.api.dto.BackupControlStatus;
import eu.royalblackwater.api.dto.SystemUpdateRequestResult;
import eu.royalblackwater.api.dto.SystemUpdateStatus;
import eu.royalblackwater.api.dto.BackupConfigurationRequest;
import eu.royalblackwater.api.dto.BackupDiscoveryRequest;
import eu.royalblackwater.api.dto.BackupEnrollmentResponseRequest;
import eu.royalblackwater.api.dto.DatabaseRestoreRequest;
import eu.royalblackwater.api.dto.FilesRestoreRequest;
import eu.royalblackwater.api.dto.SystemUpdateRequest;
import eu.royalblackwater.api.contract.api.AdminBackupsApi;
import eu.royalblackwater.api.contract.api.AdminSystemApi;
import eu.royalblackwater.api.operations.service.BackupControlService;
import eu.royalblackwater.api.operations.service.SystemUpdateService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class OperationsController extends ApiControllerSupport implements AdminBackupsApi, AdminSystemApi {

    private final BackupControlService backups;private final SystemUpdateService updates;
    public OperationsController(BackupControlService backups,SystemUpdateService updates){this.backups=backups;this.updates=updates;}

    @Override
    public ResponseEntity<BackupControlRequestResult> adminDeleteBackupConfiguration() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.deleteConfiguration(actor), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminConfigureBackupHost(
            BackupConfigurationRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.configure(actor,body), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminDiscoverBackupHost(
            BackupDiscoveryRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.discover(actor,body), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminApplyBackupEnrollment(
            BackupEnrollmentResponseRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.applyEnrollment(actor,body), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminPrepareBackupEnrollment() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.prepareEnrollment(actor), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminPrepareBackupUploadKey() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.prepareKey(actor), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminRestoreLocalFilesBackup(
            FilesRestoreRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.restoreFiles(actor,body), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminRestoreLocalDatabaseBackup(
            DatabaseRestoreRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.restoreDatabase(actor,body), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminScanLocalDatabaseBackups() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.scan(actor), 202);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminRunApplicationBackup() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.run(actor), 202);
    }

    @Override
    public ResponseEntity<BackupControlStatus> adminBackupStatus() {
        CurrentUser.require();
        return respond(backups.status(), 200);
    }

    @Override
    public ResponseEntity<BackupControlRequestResult> adminTestBackupConnection() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.test(actor), 202);
    }

    @Override
    public ResponseEntity<SystemUpdateStatus> adminSystemUpdateStatus() {
        CurrentUser.require();
        return respond(updates.status(), 200);
    }

    @Override
    public ResponseEntity<SystemUpdateRequestResult> adminRequestSystemUpdate(
            SystemUpdateRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(updates.request(actor,body.operation()), 202);
    }
}
