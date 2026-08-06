package eu.royalblackwater.api.shared.dto;

import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.http.ContentDisposition;
import org.springframework.http.MediaType;

/** Typed service-to-controller DTO for streamed binary responses. */
public record BinaryDownloadDto(
        Resource resource,
        MediaType contentType,
        long contentLength,
        ContentDisposition contentDisposition,
        CacheControl cacheControl,
        String etag) {
}
