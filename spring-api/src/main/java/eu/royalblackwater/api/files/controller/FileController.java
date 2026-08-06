package eu.royalblackwater.api.files.controller;

import eu.royalblackwater.api.dto.FileRead;
import java.util.List;
import org.springframework.core.io.Resource;
import eu.royalblackwater.api.contract.api.FilesApi;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@Validated
public class FileController extends ApiControllerSupport implements FilesApi {

    private final FileAssetService files;

    public FileController(FileAssetService files) {
        this.files = files;
    }

    @Override
    public ResponseEntity<List<FileRead>> getFiles(
            String usageContext
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(files.list(actor.id(), usageContext), 200);
    }

    @Override
    public ResponseEntity<FileRead> postFile(
            String usageContext,
            MultipartFile upload
    ) {

        return respond(files.upload(
                            upload, usageContext, CurrentUser.require()), 201);
    }

    @Override
    public ResponseEntity<Void> deleteOwnFile(
            long fileId
    ) {

        files.delete(fileId, CurrentUser.require());
        return noContent();
    }

    @Override
    public ResponseEntity<Resource> getFileContent(
            long fileId
    ) {

        return download(files.content(
                            fileId, CurrentUser.optional().orElse(null)));
    }
}
