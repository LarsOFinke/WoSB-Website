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
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class OperationsController extends ApiControllerSupport {

    private final BackupControlService backups;private final SystemUpdateService updates;
    public OperationsController(BackupControlService backups,SystemUpdateService updates){this.backups=backups;this.updates=updates;}

    @DeleteMapping("/api/admin/backups/configuration")
    public ResponseEntity<BackupControlRequestResult> adminDeleteBackupConfiguration(@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.deleteConfiguration(actor,xRBFHostCapability), 202);
    }

    @PutMapping("/api/admin/backups/configuration")
    public ResponseEntity<BackupControlRequestResult> adminConfigureBackupHost(
            @Valid @RequestBody BackupConfigurationRequest body,@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.configure(actor,body,xRBFHostCapability), 202);
    }

    @PostMapping("/api/admin/backups/discover")
    public ResponseEntity<BackupControlRequestResult> adminDiscoverBackupHost(
            @Valid @RequestBody BackupDiscoveryRequest body,@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.discover(actor,body,xRBFHostCapability), 202);
    }

    @PostMapping("/api/admin/backups/enrollment/apply")
    public ResponseEntity<BackupControlRequestResult> adminApplyBackupEnrollment(
            @Valid @RequestBody BackupEnrollmentResponseRequest body,@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.applyEnrollment(actor,body,xRBFHostCapability), 202);
    }

    @PostMapping("/api/admin/backups/enrollment/prepare")
    public ResponseEntity<BackupControlRequestResult> adminPrepareBackupEnrollment(@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.prepareEnrollment(actor,xRBFHostCapability), 202);
    }

    @PostMapping("/api/admin/backups/key/prepare")
    public ResponseEntity<BackupControlRequestResult> adminPrepareBackupUploadKey(@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.prepareKey(actor,xRBFHostCapability), 202);
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
    public ResponseEntity<BackupControlRequestResult> adminScanLocalDatabaseBackups(@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.scan(actor,xRBFHostCapability), 202);
    }

    @PostMapping("/api/admin/backups/run")
    public ResponseEntity<BackupControlRequestResult> adminRunApplicationBackup(@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.run(actor,xRBFHostCapability), 202);
    }

    @GetMapping("/api/admin/backups/status")
    public ResponseEntity<BackupControlStatus> adminBackupStatus() {
        CurrentUser.require();
        return respond(backups.status(), 200);
    }

    @PostMapping("/api/admin/backups/test")
    public ResponseEntity<BackupControlRequestResult> adminTestBackupConnection(@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(backups.test(actor,xRBFHostCapability), 202);
    }

    @GetMapping("/api/admin/system/update")
    public ResponseEntity<SystemUpdateStatus> adminSystemUpdateStatus() {
        CurrentUser.require();
        return respond(updates.status(), 200);
    }

    @PostMapping("/api/admin/system/update")
    public ResponseEntity<SystemUpdateRequestResult> adminRequestSystemUpdate(
            @Valid @RequestBody SystemUpdateRequest body,@RequestHeader("X-RBF-Host-Capability") String xRBFHostCapability
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(updates.request(actor,body.operation(),xRBFHostCapability), 202);
    }
}
