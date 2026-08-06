package eu.royalblackwater.api.files.dto;

/** Internal DTO passed from the file module to content modules after ownership validation. */
public record StoredFileDto(long id, Long ownerId) {
}
