package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.mapper.AccountDtoMapper;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.queries.UserReferenceQueries;
import eu.royalblackwater.api.dto.UserReferenceRead;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class UserReferenceService {
    private final AccountDataRepository repository;

    public UserReferenceService(AccountDataRepository repository) {
        this.repository = repository;
    }

    public UserReferenceRead read(long userId) {
        UserReferenceRead reference = readMany(List.of(userId)).get(userId);
        if (reference == null) {
            throw new java.util.NoSuchElementException("User not found.");
        }
        return reference;
    }

    public Map<Long, UserReferenceRead> readMany(Collection<Long> userIds) {
        List<Long> ids = userIds == null ? List.of() : userIds.stream()
                .filter(java.util.Objects::nonNull)
                .filter(id -> id > 0)
                .distinct()
                .toList();
        if (ids.isEmpty()) {
            return Map.of();
        }
        Map<Long, UserReferenceRead> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(UserReferenceQueries.READ_MANY_SELECT_01, Map.of("ids", ids))) {
            UserReferenceRead reference = AccountDtoMapper.userReference(row);
            result.put(reference.id(), reference);
        }
        return Map.copyOf(result);
    }
}
