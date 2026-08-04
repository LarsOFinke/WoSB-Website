package eu.royalblackwater.api.forum;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.content.ContentEmbedValidator;
import eu.royalblackwater.api.contract.FileRead;
import eu.royalblackwater.api.contract.ForumPostCreate;
import eu.royalblackwater.api.contract.ForumPostRead;
import eu.royalblackwater.api.contract.ForumPostUpdate;
import eu.royalblackwater.api.contract.ForumThreadCreate;
import eu.royalblackwater.api.contract.ForumThreadRead;
import eu.royalblackwater.api.contract.ForumThreadSummary;
import eu.royalblackwater.api.contract.ForumThreadUpdate;
import eu.royalblackwater.api.contract.UserReferenceRead;
import eu.royalblackwater.api.files.FileAssetService;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.AuthenticatedUser;
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
    private static final String SUMMARY_SELECT = """
            select t.id,t.title,t.category,t.owner_id,t.created_at,t.updated_at,
                   coalesce(nullif(up.display_name,''),u.username) owner_name,
                   greatest(t.updated_at,coalesce(max(p.created_at),t.updated_at)) last_activity_at,
                   greatest(count(p.id)-1,0) reply_count
            from forum_threads t join users u on u.id=t.owner_id
            left join user_profiles up on up.user_id=u.id
            left join forum_posts p on p.thread_id=t.id
            """;
    private final JdbcQueryService jdbc;
    private final FileAssetService files;
    private final ContentEmbedValidator embeds;
    private final AuditService audit;
    private final Clock clock;

    public ForumService(JdbcQueryService jdbc, FileAssetService files, ContentEmbedValidator embeds,
                        AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.files = files;
        this.embeds = embeds;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<ForumThreadSummary> list(String search, String category) {
        StringBuilder sql = new StringBuilder(SUMMARY_SELECT + " where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (search != null && !search.isBlank()) {
            sql.append(" and (t.title ilike :search or t.category ilike :search)");
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (category != null && !category.isBlank()) {
            sql.append(" and t.category=:category");
            parameters.put("category", category(category));
        }
        sql.append(" group by t.id,u.username,up.display_name order by t.updated_at desc,t.id desc limit 500");
        return jdbc.query(sql.toString(), parameters).stream().map(ForumService::summary).toList();
    }

    @Transactional(readOnly = true)
    public ForumThreadRead get(long threadId) {
        ForumThreadSummary summary = jdbc.optional(SUMMARY_SELECT + " where t.id=:id group by t.id,u.username,up.display_name",
                        Map.of("id", threadId)).map(ForumService::summary)
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Thread not found."));
        List<Map<String, Object>> rows = jdbc.query("""
                select p.*,coalesce(nullif(up.display_name,''),u.username) author_name
                from forum_posts p join users u on u.id=p.author_id
                left join user_profiles up on up.user_id=u.id
                where p.thread_id=:id order by p.created_at,p.id
                """, Map.of("id", threadId));
        Map<Long, List<FileRead>> attachments = files.attachmentsByOwners(
                "forum_post_attachments", "post_id", rows.stream().map(row -> RowValues.longValue(row, "id")).toList());
        List<ForumPostRead> posts = rows.stream().map(row -> post(row,
                attachments.getOrDefault(RowValues.longValue(row, "id"), List.of()))).toList();
        return new ForumThreadRead(summary.category(), summary.createdAt(), summary.id(), summary.lastActivityAt(),
                summary.owner(), summary.ownerId(), posts, summary.replyCount(), summary.title(), summary.updatedAt());
    }

    @Transactional
    public ForumThreadRead create(ForumThreadCreate payload, AuthenticatedUser actor) {
        List<Map<String, Object>> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        long threadId = jdbc.insertReturningId("""
                insert into forum_threads(title,category,owner_id,is_pinned,created_at,updated_at)
                values(:title,:category,:ownerId,false,:now,:now) returning id
                """, Map.of("title", payload.title().strip(), "category", category(payload.category()),
                        "ownerId", actor.id(), "now", now));
        long postId = jdbc.insertReturningId("""
                insert into forum_posts(thread_id,author_id,body,created_at,updated_at)
                values(:threadId,:authorId,:body,:now,:now) returning id
                """, Map.of("threadId", threadId, "authorId", actor.id(), "body", payload.body(), "now", now));
        files.attach("forum_post_attachments", "post_id", postId, selected, "forum");
        audit.record(actor, "forum_thread", threadId, "create", "Forum thread created.",
                List.of("title", "category", "body", "file_ids"));
        return get(threadId);
    }

    @Transactional
    public ForumThreadRead updateThread(long threadId, ForumThreadUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> thread = rawThread(threadId);
        requireOwnerOrStaff(RowValues.longValue(thread, "owner_id"), actor);
        Map<String, Object> opening = jdbc.optional("""
                select * from forum_posts where thread_id=:id order by created_at,id limit 1
                """, Map.of("id", threadId)).orElseThrow(() -> bad("Thread has no opening post."));
        long postId = RowValues.longValue(opening, "id");
        Set<Long> previous = attachmentIds(postId);
        List<Map<String, Object>> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        jdbc.update("""
                update forum_threads set title=:title,category=:category,updated_at=:now where id=:id
                """, Map.of("title", payload.title().strip(), "category", category(payload.category()),
                        "now", now, "id", threadId));
        jdbc.update("update forum_posts set body=:body,updated_at=:now where id=:id",
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
        List<Map<String, Object>> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        long postId = jdbc.insertReturningId("""
                insert into forum_posts(thread_id,author_id,body,created_at,updated_at)
                values(:threadId,:authorId,:body,:now,:now) returning id
                """, Map.of("threadId", threadId, "authorId", actor.id(), "body", payload.body(), "now", now));
        files.attach("forum_post_attachments", "post_id", postId, selected, "forum");
        jdbc.update("update forum_threads set updated_at=:now where id=:id", Map.of("now", now, "id", threadId));
        audit.record(actor, "forum_post", postId, "create", "Forum reply created.", List.of("body", "file_ids"));
        return readPost(postId);
    }

    @Transactional
    public ForumPostRead updatePost(long postId, ForumPostUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> post = rawPost(postId);
        requireOwnerOrStaff(RowValues.longValue(post, "author_id"), actor);
        Set<Long> previous = attachmentIds(postId);
        List<Map<String, Object>> selected = files.ownedFiles(payload.fileIds(), actor);
        embeds.validateFiles(payload.body(), ids(selected));
        LocalDateTime now = now();
        jdbc.update("update forum_posts set body=:body,updated_at=:now where id=:id",
                Map.of("body", payload.body(), "now", now, "id", postId));
        jdbc.update("update forum_threads set updated_at=:now where id=:id",
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
        long openingId = RowValues.longValue(jdbc.required(
                "select id from forum_posts where thread_id=:id order by created_at,id limit 1",
                Map.of("id", threadId)), "id");
        if (openingId == postId) throw bad("The opening post must be removed by deleting the thread.");
        Set<Long> attachments = attachmentIds(postId);
        jdbc.update("delete from forum_posts where id=:id", Map.of("id", postId));
        jdbc.update("update forum_threads set updated_at=:now where id=:id", Map.of("now", now(), "id", threadId));
        files.refreshPublication(attachments);
        audit.record(actor, "forum_post", postId, "delete", "Forum post removed.", List.of());
    }

    @Transactional
    public void deleteThread(long threadId, AuthenticatedUser actor) {
        Map<String, Object> thread = rawThread(threadId);
        requireOwnerOrStaff(RowValues.longValue(thread, "owner_id"), actor);
        Set<Long> fileIds = new java.util.LinkedHashSet<>();
        for (Map<String, Object> row : jdbc.query("""
                select a.file_id from forum_post_attachments a join forum_posts p on p.id=a.post_id
                where p.thread_id=:id
                """, Map.of("id", threadId))) fileIds.add(RowValues.longValue(row, "file_id"));
        jdbc.update("delete from forum_threads where id=:id", Map.of("id", threadId));
        files.refreshPublication(fileIds);
        audit.record(actor, "forum_thread", threadId, "delete", "Forum thread removed.", List.of());
    }

    private ForumPostRead readPost(long postId) {
        Map<String, Object> row = jdbc.optional("""
                select p.*,coalesce(nullif(up.display_name,''),u.username) author_name
                from forum_posts p join users u on u.id=p.author_id
                left join user_profiles up on up.user_id=u.id where p.id=:id
                """, Map.of("id", postId)).orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Post not found."));
        return post(row, files.attachments("forum_post_attachments", "post_id", postId));
    }

    private Map<String, Object> rawThread(long id) {
        return jdbc.optional("select * from forum_threads where id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Thread not found."));
    }
    private Map<String, Object> rawPost(long id) {
        return jdbc.optional("select * from forum_posts where id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Post not found."));
    }
    private Set<Long> attachmentIds(long postId) {
        Set<Long> values = new java.util.LinkedHashSet<>();
        for (Map<String, Object> row : jdbc.query("select file_id from forum_post_attachments where post_id=:id",
                Map.of("id", postId))) values.add(RowValues.longValue(row, "file_id"));
        return values;
    }
    private static List<Long> ids(List<Map<String, Object>> rows) {
        return rows.stream().map(row -> RowValues.longValue(row, "id")).toList();
    }
    private static ForumThreadSummary summary(Map<String, Object> row) {
        long ownerId = RowValues.longValue(row, "owner_id");
        return new ForumThreadSummary(category(RowValues.string(row, "category")), RowValues.dateTime(row, "created_at"),
                RowValues.longValue(row, "id"), RowValues.dateTime(row, "last_activity_at"),
                new UserReferenceRead(RowValues.requiredString(row, "owner_name"), ownerId), ownerId,
                RowValues.longValue(row, "reply_count"), RowValues.requiredString(row, "title"),
                RowValues.dateTime(row, "updated_at"));
    }
    private static ForumPostRead post(Map<String, Object> row, List<FileRead> attachments) {
        long authorId = RowValues.longValue(row, "author_id");
        return new ForumPostRead(attachments, new UserReferenceRead(RowValues.requiredString(row, "author_name"), authorId),
                authorId, RowValues.requiredString(row, "body"), RowValues.dateTime(row, "created_at"),
                RowValues.longValue(row, "id"), RowValues.longValue(row, "thread_id"), RowValues.dateTime(row, "updated_at"));
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
