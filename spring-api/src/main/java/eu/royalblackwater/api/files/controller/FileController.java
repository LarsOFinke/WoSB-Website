package eu.royalblackwater.api.files.controller;

import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.util.List;
import org.springframework.core.io.Resource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@Validated
public class FileController extends ApiControllerSupport {

    private final FileAssetService files;

    public FileController(FileAssetService files) {
        this.files = files;
    }

    @GetMapping("/api/files")
    public ResponseEntity<List<FileRead>> getFiles(
            @RequestParam(name = "usage_context", required = false) String usageContext
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(files.list(actor.id(), usageContext), 200);
    }

    @PostMapping(value = "/api/files", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<FileRead> postFile(
            @RequestParam(name = "usage_context", defaultValue = "general") String usageContext,
            @RequestPart("file") MultipartFile upload
    ) {

        return respond(files.upload(
                            upload, usageContext, CurrentUser.require()), 201);
    }

    @DeleteMapping("/api/files/{file_id}")
    public ResponseEntity<Void> deleteOwnFile(
            @PathVariable("file_id") long fileId
    ) {

        files.delete(fileId, CurrentUser.require());
        return noContent();
    }

    @GetMapping("/api/files/{file_id}/content")
    public ResponseEntity<Resource> getFileContent(
            @PathVariable("file_id") long fileId
    ) {

        return download(files.content(
                            fileId, CurrentUser.optional().orElse(null)));
    }
}
