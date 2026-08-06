package eu.royalblackwater.api.shared.web;

import eu.royalblackwater.api.shared.dto.BinaryDownloadDto;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;


/** Shared response and validation helpers for thin, fully typed HTTP controllers. */
public abstract class ApiControllerSupport {
    protected final <T> ResponseEntity<T> respond(T result, int successStatus) {
        if (successStatus == 204) {
            throw new IllegalArgumentException("Use noContent() for HTTP 204 responses.");
        }
        return ResponseEntity.status(HttpStatusCode.valueOf(successStatus)).body(result);
    }

    protected final ResponseEntity<Void> noContent() {
        return ResponseEntity.noContent().build();
    }

    protected final ResponseEntity<Resource> download(BinaryDownloadDto download) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(download.contentType());
        headers.setContentLength(download.contentLength());
        if (download.contentDisposition() != null) {
            headers.setContentDisposition(download.contentDisposition());
        }
        if (download.cacheControl() != null) {
            headers.setCacheControl(download.cacheControl());
        }
        if (download.etag() != null) {
            headers.setETag(download.etag());
        }
        headers.set("X-Content-Type-Options", "nosniff");
        return ResponseEntity.ok().headers(headers).body(download.resource());
    }

}
