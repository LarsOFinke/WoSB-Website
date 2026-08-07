package eu.royalblackwater.api.operations.controller;

import eu.royalblackwater.api.dto.BackupConfigurationRequest;
import eu.royalblackwater.api.dto.BackupControlRequestResult;
import eu.royalblackwater.api.dto.BackupControlStatus;
import eu.royalblackwater.api.dto.BackupDiscoveryRequest;
import eu.royalblackwater.api.dto.BackupEnrollmentResponseRequest;
import eu.royalblackwater.api.dto.DatabaseRestoreRequest;
import eu.royalblackwater.api.dto.FilesRestoreRequest;
import eu.royalblackwater.api.dto.SystemUpdateRequest;
import eu.royalblackwater.api.dto.SystemUpdateRequestResult;
import eu.royalblackwater.api.dto.SystemUpdateStatus;
import eu.royalblackwater.api.operations.service.BackupControlService;
import eu.royalblackwater.api.operations.service.SystemUpdateService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class OperationsController extends ApiControllerSupport {

    private final BackupControlService backups;private final SystemUpdateService updates;
    public OperationsController(BackupControlService backups,SystemUpdateService updates){this.backups=backups;this.updates=updates;}

    @DeleteMapping("/api/admin/backups/configuration")
    public ResponseEntity<BackupControlRequestResult> adminDeleteBackupConfiguration() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.deleteConfiguration(actor), 202);
    }

    @PutMapping("/api/admin/backups/configuration")
    public ResponseEntity<BackupControlRequestResult> adminConfigureBackupHost(
            @Valid @RequestBody BackupConfigurationRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.configure(actor,body), 202);
    }

    @PostMapping("/api/admin/backups/discover")
    public ResponseEntity<BackupControlRequestResult> adminDiscoverBackupHost(
            @Valid @RequestBody BackupDiscoveryRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.discover(actor,body), 202);
    }

    @PostMapping("/api/admin/backups/enrollment/apply")
    public ResponseEntity<BackupControlRequestResult> adminApplyBackupEnrollment(
            @Valid @RequestBody BackupEnrollmentResponseRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.applyEnrollment(actor,body), 202);
    }

    @PostMapping("/api/admin/backups/enrollment/prepare")
    public ResponseEntity<BackupControlRequestResult> adminPrepareBackupEnrollment() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.prepareEnrollment(actor), 202);
    }

    @PostMapping("/api/admin/backups/key/prepare")
    public ResponseEntity<BackupControlRequestResult> adminPrepareBackupUploadKey() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.prepareKey(actor), 202);
    }

    @PostMapping("/api/admin/backups/local/files/restore")
    public ResponseEntity<BackupControlRequestResult> adminRestoreLocalFilesBackup(
            @Valid @RequestBody FilesRestoreRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.restoreFiles(actor,body), 202);
    }

    @PostMapping("/api/admin/backups/local/restore")
    public ResponseEntity<BackupControlRequestResult> adminRestoreLocalDatabaseBackup(
            @Valid @RequestBody DatabaseRestoreRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.restoreDatabase(actor,body), 202);
    }

    @PostMapping("/api/admin/backups/local/scan")
    public ResponseEntity<BackupControlRequestResult> adminScanLocalDatabaseBackups() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.scan(actor), 202);
    }

    @PostMapping("/api/admin/backups/run")
    public ResponseEntity<BackupControlRequestResult> adminRunApplicationBackup() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.run(actor), 202);
    }

    @GetMapping("/api/admin/backups/status")
    public ResponseEntity<BackupControlStatus> adminBackupStatus() {
        CurrentUser.require();
        return respond(backups.status(), 200);
    }

    @PostMapping("/api/admin/backups/test")
    public ResponseEntity<BackupControlRequestResult> adminTestBackupConnection() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.test(actor), 202);
    }

    @GetMapping("/api/admin/system/update")
    public ResponseEntity<SystemUpdateStatus> adminSystemUpdateStatus() {
        CurrentUser.require();
        return respond(updates.status(), 200);
    }

    @PostMapping("/api/admin/system/update")
    public ResponseEntity<SystemUpdateRequestResult> adminRequestSystemUpdate(
            @Valid @RequestBody SystemUpdateRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(updates.request(actor,body.operation()), 202);
    }
}
