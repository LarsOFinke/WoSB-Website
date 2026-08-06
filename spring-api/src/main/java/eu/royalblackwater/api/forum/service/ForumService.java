package eu.royalblackwater.api.forum.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.content.service.ContentEmbedValidator;
import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.dto.ForumPostCreate;
import eu.royalblackwater.api.dto.ForumPostRead;
import eu.royalblackwater.api.dto.ForumPostUpdate;
import eu.royalblackwater.api.dto.ForumThreadCreate;
import eu.royalblackwater.api.dto.ForumThreadRead;
import eu.royalblackwater.api.dto.ForumThreadSummary;
import eu.royalblackwater.api.dto.ForumThreadUpdate;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.files.dto.StoredFileDto;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.forum.mapper.ForumDtoMapper;
import eu.royalblackwater.api.forum.repository.ForumRepository;
import eu.royalblackwater.api.forum.repository.queries.ForumQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class ForumService {
    private static final Set<String> CATEGORIES = Set.of("general", "builds", "events", "support", "training", "logistics");
    private final ForumRepository repository;
    private final FileAssetService files;
    private final ContentEmbedValidator embeds;
    private final AuditService audit;
    private final Clock clock;

    public ForumService(ForumRepository repository, FileAssetService files, ContentEmbedValidator embeds,
                        AuditService audit, Clock clock) {
        this.repository = repository;
        this.files = files;
        this.embeds = embeds;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<ForumThreadSummary> list(String search, String category, int limit, int offset) {
        StringBuilder sql = new StringBuilder(ForumQueries.SUMMARY_SELECT + ForumQueries.LIST_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (search != null && !search.isBlank()) {
            sql.append(ForumQueries.LIST_AND_01);
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (category != null && !category.isBlank()) {
            sql.append(ForumQueries.LIST_AND_02);
            parameters.put("category", category(category));
        }
        sql.append(ForumQueries.LIST_GROUP_BY_01);
        parameters.put("limit", limit);
        parameters.put("offset", offset);
        return repository.query(sql.toString(), parameters).stream().map(row -> ForumDtoMapper.threadSummary(row, category(RowValues.string(row, "category")))).toList();
    }

    @Transactional(readOnly = true)
    public ForumThreadRead get(long threadId) {
        ForumThreadSummary summary = repository.optional(ForumQueries.SUMMARY_SELECT + ForumQueries.GET_WHERE_01,
                        Map.of("id", threadId)).map(row -> ForumDtoMapper.threadSummary(row, category(RowValues.string(row, "category"))))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Thread not found."));
        List<Map<String, Object>> rows = repository.query(ForumQueries.GET_SELECT_01, Map.of("id", threadId));
        Map<Long, List<FileRead>> attachments = files.attachmentsByOwners(
                "forum_post_attachments", "post_id", rows.stream().map(row -> RowValues.longValue(row, "id")).toList());
        List<ForumPostRead> posts = rows.stream().map(row -> ForumDtoMapper.post(row,
                attachments.getOrDefault(RowValues.longValue(row, "id"), List.of()))).toList();
        return ForumDtoMapper.thread(summary, posts);
    }

    @Transactional
    public ForumThreadRead create(ForumThreadCreate payload, AuthenticatedUser actor) {
        List<StoredFileDto> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        long threadId = repository.insertReturningId(ForumQueries.CREATE_INSERT_01, Map.of("title", payload.title().strip(), "category", category(payload.category()),
                        "ownerId", actor.id(), "now", now));
        long postId = repository.insertReturningId(ForumQueries.CREATE_INSERT_02, Map.of("threadId", threadId, "authorId", actor.id(), "body", payload.body(), "now", now));
        files.attach("forum_post_attachments", "post_id", postId, selected, "forum");
        audit.record(actor, "forum_thread", threadId, "create", "Forum thread created.",
                List.of("title", "category", "body", "file_ids"));
        return get(threadId);
    }

    @Transactional
    public ForumThreadRead updateThread(long threadId, ForumThreadUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> thread = rawThread(threadId);
        requireOwnerOrStaff(RowValues.longValue(thread, "owner_id"), actor);
        Map<String, Object> opening = repository.optional(ForumQueries.UPDATE_THREAD_SELECT_01, Map.of("id", threadId)).orElseThrow(() -> bad("Thread has no opening post."));
        long postId = RowValues.longValue(opening, "id");
        Set<Long> previous = attachmentIds(postId);
        List<StoredFileDto> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        repository.update(ForumQueries.UPDATE_THREAD_UPDATE_01, Map.of("title", payload.title().strip(), "category", category(payload.category()),
                        "now", now, "id", threadId));
        repository.update(ForumQueries.UPDATE_THREAD_UPDATE_02,
                Map.of("body", payload.body(), "now", now, "id", postId));
        files.attach("forum_post_attachments", "post_id", postId, selected, "forum");
        previous.addAll(ids(selected));
        files.refreshPublication(previous);
        audit.record(actor, "forum_thread", threadId, "update", "Forum thread updated.",
                List.of("title", "category", "body", "file_ids"));
        return get(threadId);
    }

    @Transactional
    public ForumPostRead addPost(long threadId, ForumPostCreate payload, AuthenticatedUser actor) {
        rawThread(threadId);
        List<StoredFileDto> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        long postId = repository.insertReturningId(ForumQueries.CREATE_INSERT_02, Map.of("threadId", threadId, "authorId", actor.id(), "body", payload.body(), "now", now));
        files.attach("forum_post_attachments", "post_id", postId, selected, "forum");
        repository.update(ForumQueries.ADD_POST_UPDATE_01, Map.of("now", now, "id", threadId));
        audit.record(actor, "forum_post", postId, "create", "Forum reply created.", List.of("body", "file_ids"));
        return readPost(postId);
    }

    @Transactional
    public ForumPostRead updatePost(long postId, ForumPostUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> post = rawPost(postId);
        requireOwnerOrStaff(RowValues.longValue(post, "author_id"), actor);
        Set<Long> previous = attachmentIds(postId);
        List<StoredFileDto> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        repository.update(ForumQueries.UPDATE_THREAD_UPDATE_02,
                Map.of("body", payload.body(), "now", now, "id", postId));
        repository.update(ForumQueries.ADD_POST_UPDATE_01,
                Map.of("now", now, "id", RowValues.longValue(post, "thread_id")));
        files.attach("forum_post_attachments", "post_id", postId, selected, "forum");
        previous.addAll(ids(selected));
        files.refreshPublication(previous);
        audit.record(actor, "forum_post", postId, "update", "Forum post updated.", List.of("body", "file_ids"));
        return readPost(postId);
    }

    @Transactional
    public void deletePost(long postId, AuthenticatedUser actor) {
        Map<String, Object> post = rawPost(postId);
        requireOwnerOrStaff(RowValues.longValue(post, "author_id"), actor);
        long threadId = RowValues.longValue(post, "thread_id");
        long openingId = RowValues.longValue(repository.required(
                ForumQueries.DELETE_POST_SELECT_01,
                Map.of("id", threadId)), "id");
        if (openingId == postId) throw bad("The opening post must be removed by deleting the thread.");
        Set<Long> attachments = attachmentIds(postId);
        repository.update(ForumQueries.DELETE_POST_DELETE_01, Map.of("id", postId));
        repository.update(ForumQueries.ADD_POST_UPDATE_01, Map.of("now", now(), "id", threadId));
        files.refreshPublication(attachments);
        audit.record(actor, "forum_post", postId, "delete", "Forum post removed.", List.of());
    }

    @Transactional
    public void deleteThread(long threadId, AuthenticatedUser actor) {
        Map<String, Object> thread = rawThread(threadId);
        requireOwnerOrStaff(RowValues.longValue(thread, "owner_id"), actor);
        Set<Long> fileIds = new java.util.LinkedHashSet<>();
        for (Map<String, Object> row : repository.query(ForumQueries.DELETE_THREAD_SELECT_01, Map.of("id", threadId))) fileIds.add(RowValues.longValue(row, "file_id"));
        repository.update(ForumQueries.DELETE_THREAD_DELETE_01, Map.of("id", threadId));
        files.refreshPublication(fileIds);
        audit.record(actor, "forum_thread", threadId, "delete", "Forum thread removed.", List.of());
    }

    private ForumPostRead readPost(long postId) {
        Map<String, Object> row = repository.optional(ForumQueries.READ_POST_SELECT_01, Map.of("id", postId)).orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Post not found."));
        return ForumDtoMapper.post(row, files.attachments("forum_post_attachments", "post_id", postId));
    }

    private Map<String, Object> rawThread(long id) {
        return repository.optional(ForumQueries.RAW_THREAD_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Thread not found."));
    }
    private Map<String, Object> rawPost(long id) {
        return repository.optional(ForumQueries.RAW_POST_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Post not found."));
    }
    private Set<Long> attachmentIds(long postId) {
        Set<Long> values = new java.util.LinkedHashSet<>();
        for (Map<String, Object> row : repository.query(ForumQueries.ATTACHMENT_IDS_SELECT_01,
                Map.of("id", postId))) values.add(RowValues.longValue(row, "file_id"));
        return values;
    }
    private static List<Long> ids(List<StoredFileDto> files) {
        return files.stream().map(StoredFileDto::id).toList();
    }

    private static String category(String value) {
        String normalized = value == null ? "general" : value.strip().toLowerCase(Locale.ROOT).replace(' ', '_').replace('-', '_');
        if (Set.of("logistic", "loistics").contains(normalized)) normalized = "logistics";
        return CATEGORIES.contains(normalized) ? normalized : "general";
    }
    private static void requireOwnerOrStaff(long ownerId, AuthenticatedUser actor) {
        if (ownerId != actor.id() && !actor.staff()) throw new ResponseStatusException(NOT_FOUND, "Content not found.");
    }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
