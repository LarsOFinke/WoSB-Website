package eu.royalblackwater.api.legal;

import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/legal-notice")
public class LegalNoticeController {
    private final LegalNoticeRepository repository;

    public LegalNoticeController(LegalNoticeRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public ResponseEntity<LegalNoticeContracts.PublicRead> getPublicNotice() {
        return ResponseEntity.ok(repository.findById(1)
                .map(LegalNoticeContracts::from)
                .orElseGet(() -> LegalNoticeContracts.unpublished(null)));
    }
}
