package eu.royalblackwater.api.integration;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.testcontainers.junit.jupiter.Testcontainers;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers(disabledWithoutDocker = true)
class ApplicationIntegrationTest extends ApplicationIntegrationSupport {

    @Test
    void migratesSeedsAndStartsTheCompleteApplication() {
        assertThat(jdbc.count("select count(*) from flyway_schema_history where success=true", Map.of()))
                .isPositive();
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='1'", Map.of()))
                .isZero();
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='2'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='7'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='8'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='9'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='12'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='13'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from information_schema.tables where table_name='warehouse_entries'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from warehouse_ports where is_active=true", Map.of()))
                .isGreaterThanOrEqualTo(38);
        assertThat(jdbc.count("""
                select count(*) from information_schema.columns
                 where table_schema=current_schema() and table_name='builds'
                   and column_name in ('printout_cache_key','printout_source_updated_at')
                """, Map.of())).isEqualTo(2);
        assertThat(jdbc.count("select count(*) from site_roles", Map.of())).isPositive();
        assertThat(jdbc.count("select count(*) from users where is_bootstrap_admin=true", Map.of()))
                .isEqualTo(1);
    }

    @Test
    void bootstrapAdministratorCanLoginWithConfiguredFirstRunCredentials() throws Exception {
        HttpResponse<String> response = post(
                "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"Integration-Test-Admin-Password-42!\"}",
                null, null, localOrigin());

        assertStatus(response, 200, "POST", "/api/auth/login");
        assertThat(response.body()).contains("\"username\":\"admin\"");
        assertThat(response.headers().allValues("set-cookie"))
                .anyMatch(value -> value.startsWith("rbf_hub_session="));

        HttpResponse<String> rejected = post(
                "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"definitely-wrong-password\"}",
                null, null, localOrigin());
        assertStatus(rejected, 401, "POST", "/api/auth/login");
        assertThat(rejected.body()).contains("\"detail\":\"Invalid username or password.\"");
    }

    @Test
    void repairsBootstrapFleetLeadershipAndKeepsInitializationIdempotent() {
        Map<String, Object> membership = bootstrapMembership();
        assertThat(membership).containsEntry("status", "active").containsEntry("role", "fleet_admiral")
                .containsEntry("slug", "royal-blackwater-fleet")
                .containsEntry("can_manage_fleet", true).containsEntry("can_manage_members", true);

        jdbc.update("""
                update fleet_memberships set status='inactive',fleet_role_id=(select id from fleet_roles where code='member')
                where id=:id
                """, Map.of("id", ((Number) membership.get("id")).longValue()));
        bootstrapAdministrator.initialize();
        bootstrapAdministrator.initialize();

        assertThat(bootstrapMembership()).containsEntry("status", "active").containsEntry("role", "fleet_admiral");
        assertThat(jdbc.count("""
                select count(*) from fleet_memberships m join users u on u.id=m.user_id
                where u.is_bootstrap_admin=true
                """, Map.of())).isEqualTo(1);
    }

    @Test
    void preservesMasterDataOverridesDuringStartupSyncAndRestoresThemExplicitly() throws Exception {
        Map<String, Object> category = jdbc.required("""
                select id,label from build_item_categories where seed_key is not null order by id limit 1
                """, Map.of());
        long categoryId = ((Number) category.get("id")).longValue();
        String seedLabel = String.valueOf(category.get("label"));
        long categories = jdbc.count("select count(*) from build_item_categories", Map.of());
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        assertStatus(put("/api/admin/master-data/categories/" + categoryId,
                "{\"label\":\"Local integration override\",\"sort_order\":1,\"is_active\":true}",
                administrator), 200, "PUT", "/api/admin/master-data/categories/{category_id}");
        jdbc.update("update fleet_roles set can_manage_fleet=false where code='fleet_admiral'", Map.of());

        referenceDataSeeder.synchronize(false);
        assertThat(jdbc.required("select label,is_seed_overridden from build_item_categories where id=:id",
                Map.of("id", categoryId))).containsEntry("label", "Local integration override")
                .containsEntry("is_seed_overridden", true);
        assertThat(jdbc.required("select can_manage_fleet from fleet_roles where code='fleet_admiral'", Map.of()))
                .containsEntry("can_manage_fleet", true);
        assertThat(jdbc.count("select count(*) from build_item_categories", Map.of())).isEqualTo(categories);

        assertStatus(post("/api/admin/master-data/categories/" + categoryId + "/restore-seed", "",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                200, "POST", "/api/admin/master-data/categories/{category_id}/restore-seed");
        assertThat(jdbc.required("select label,is_seed_overridden from build_item_categories where id=:id",
                Map.of("id", categoryId))).containsEntry("label", seedLabel).containsEntry("is_seed_overridden", false);
        assertThat(jdbc.count("select count(*) from build_item_categories", Map.of())).isEqualTo(categories);
    }

    @Test
    void bootstrapAdministratorCanLoadFleetManagementWorkspace() throws Exception {
        referenceDataSeeder.synchronize(false);
        bootstrapAdministrator.initialize();
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");

        HttpResponse<String> manageable = get("/api/fleets/manageable", administrator.sessionCookie());
        assertStatus(manageable, 200, "GET", "/api/fleets/manageable");
        long fleetId = jsonId(manageable.body());

        HttpResponse<String> detail = get("/api/fleets/" + fleetId + "/manage", administrator.sessionCookie());
        assertStatus(detail, 200, "GET", "/api/fleets/{fleet_id}/manage");
        assertThat(detail.body()).contains("\"memberships\":[", "\"management\":{");
        assertThat(detail.body()).contains("\"protected\":");
        assertThat(detail.body()).doesNotContain("\"protected_value\":");

        HttpResponse<String> roles = get(
                "/api/fleets/" + fleetId + "/roles?include_inactive=true", administrator.sessionCookie());
        assertStatus(roles, 200, "GET", "/api/fleets/{fleet_id}/roles?include_inactive=true");
        assertThat(roles.body()).contains("\"code\":\"fleet_admiral\"");
    }

    @Test
    void bootstrapFleetManagerCanCreateAndOperateASquadOverHttp() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        long membershipId = ((Number) bootstrapMembership().get("id")).longValue();
        String squadName = "Integration Squadron " + System.nanoTime();
        HttpResponse<String> created = post("/api/squads", "{\"name\":\"" + squadName
                        + "\",\"leader_membership_id\":" + membershipId + ",\"max_members\":8}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(created, 201, "POST", "/api/squads");
        long squadId = jsonId(created.body());

        assertStatus(get("/api/squads/" + squadId, administrator.sessionCookie()),
                200, "GET", "/api/squads/{squad_id}");
        assertStatus(get("/api/squads/mine", administrator.sessionCookie()), 200, "GET", "/api/squads/mine");
        HttpResponse<String> roster = get("/api/squads/roster", administrator.sessionCookie());
        assertStatus(roster, 200, "GET", "/api/squads/roster");
        assertThat(roster.body()).contains("\"fleet_membership_id\":" + membershipId);

        HttpResponse<String> archived = delete("/api/squads/" + squadId,
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(archived, 204, "DELETE", "/api/squads/{squad_id}");
        assertThat(jdbc.count("select count(*) from squads where id=:id and is_active=false", Map.of("id", squadId)))
                .isEqualTo(1);
    }

    @Test
    void createsAndReloadsCoreContentDomainsWithoutServerErrors() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        long nonce = System.nanoTime();

        Map<String, Object> ship = jdbc.required("""
                select id,sailor_minimum from ships where is_active=true order by id limit 1
                """, Map.of());
        long shipId = ((Number) ship.get("id")).longValue();
        long sailorMinimum = ((Number) ship.get("sailor_minimum")).longValue();
        HttpResponse<String> build = post(
                "/api/builds",
                "{\"build_name\":\"Integration Build " + nonce + "\",\"ship_id\":" + shipId
                        + ",\"sailors\":" + sailorMinimum + "}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(build, 201, "POST", "/api/builds");
        long buildId = jsonId(build.body());
        assertStatus(get("/api/builds/" + buildId, administrator.sessionCookie()),
                200, "GET", "/api/builds/{build_id}");

        HttpResponse<String> thread = post(
                "/api/forum/threads",
                "{\"title\":\"Integration Thread " + nonce + "\",\"body\":\"Integration body.\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(thread, 201, "POST", "/api/forum/threads");
        long threadId = jsonId(thread.body());
        assertStatus(get("/api/forum/threads/" + threadId, administrator.sessionCookie()),
                200, "GET", "/api/forum/threads/{thread_id}");

        HttpResponse<String> guide = post(
                "/api/guides",
                "{\"title\":\"Integration Guide " + nonce + "\",\"body\":\"Integration guide body.\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(guide, 201, "POST", "/api/guides");
        long guideId = jsonId(guide.body());
        assertStatus(get("/api/guides/" + guideId, administrator.sessionCookie()),
                200, "GET", "/api/guides/{guide_id}");

        HttpResponse<String> group = post(
                "/api/groups",
                "{\"title\":\"Integration Group " + nonce + "\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(group, 201, "POST", "/api/groups");
        long groupId = jsonId(group.body());
        assertStatus(get("/api/groups/" + groupId, administrator.sessionCookie()),
                200, "GET", "/api/groups/{group_id}");

        long categoryId = ((Number) jdbc.required(
                "select id from build_item_categories order by id limit 1", Map.of()).get("id")).longValue();
        HttpResponse<String> option = post(
                "/api/admin/master-data/options",
                "{\"category_id\":" + categoryId + ",\"name\":\"Integration Option " + nonce + "\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(option, 201, "POST", "/api/admin/master-data/options");
        long optionId = jsonId(option.body());
        assertStatus(delete("/api/admin/master-data/options/" + optionId,
                        administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                204, "DELETE", "/api/admin/master-data/options/{option_id}");
        assertThat(jdbc.count("select count(*) from build_item_options where id=:id", Map.of("id", optionId)))
                .isZero();
    }

    @Test
    void membersReadWarehouseWhileStaffManageVersionedAuditLifecycle() throws Exception {
        long nonce = Math.abs(System.nanoTime());
        String moderatorPassword = "Warehouse-Moderator-Password-42!";
        createUser("warehouse-moderator-" + nonce, moderatorPassword, "moderator");
        SessionCookies moderator = login("warehouse-moderator-" + nonce, moderatorPassword);
        String memberPassword = "Warehouse-Member-Password-42!";
        createMember("warehouse-member-" + nonce, memberPassword);
        SessionCookies member = login("warehouse-member-" + nonce, memberPassword);
        long fleetId = ((Number) bootstrapMembership().get("fleet_id")).longValue();
        String createBody = "{\"fleet_id\":" + fleetId
                + ",\"custom_holder_name\":\"Blackwater\",\"port\":\"Tortuga\","
                + "\"resource\":\"Iron\",\"amount\":650,\"reserved\":false}";
        HttpResponse<String> created = post("/api/warehouse", createBody,
                moderator.cookieHeader(), moderator.csrfToken(), localOrigin());
        assertStatus(created, 201, "POST", "/api/warehouse");
        long entryId = jsonId(created.body());
        assertThat(created.body()).contains("\"holder_name\":\"Blackwater\"", "\"version\":1");

        HttpResponse<String> listed = get("/api/warehouse?fleet_id=" + fleetId,
                member.sessionCookie());
        assertStatus(listed, 200, "GET", "/api/warehouse?fleet_id={fleet_id}");
        assertThat(listed.body()).contains("\"matching_stock\":650", "\"available_stock\":650");
        assertStatus(post("/api/warehouse", createBody,
                        member.cookieHeader(), member.csrfToken(), localOrigin()),
                403, "POST", "/api/warehouse member mutation");

        String updateBody = "{\"fleet_id\":" + fleetId
                + ",\"custom_holder_name\":\"Blackwater\",\"port\":\"Tortuga\","
                + "\"resource\":\"Iron\",\"amount\":1250,\"reserved\":false,\"version\":1}";
        HttpResponse<String> updated = put("/api/warehouse/" + entryId, updateBody, moderator);
        assertStatus(updated, 200, "PUT", "/api/warehouse/{entry_id}");
        assertThat(updated.body()).contains("\"amount\":1250", "\"version\":2");

        assertStatus(put("/api/warehouse/" + entryId, updateBody, moderator),
                409, "PUT", "/api/warehouse/{entry_id} stale version");
        String reserveBody = updateBody.replace("\"reserved\":false,\"version\":1",
                "\"reserved\":true,\"version\":2");
        HttpResponse<String> reserved = put("/api/warehouse/" + entryId, reserveBody, moderator);
        assertStatus(reserved, 200, "PUT", "/api/warehouse/{entry_id} reservation");
        long version = jsonLong(reserved.body(), "version");
        assertThat(reserved.body()).contains("\"reserved\":true");
        assertThat(jdbc.count("select count(*) from audit_logs where entity_type='warehouse_entry' and action='reservation' and entity_id=:id",
                Map.of("id", String.valueOf(entryId)))).isEqualTo(1);

        assertStatus(delete("/api/warehouse/" + entryId + "?version=" + version,
                moderator.cookieHeader(), moderator.csrfToken(), localOrigin()),
                204, "DELETE", "/api/warehouse/{entry_id}");
        assertThat(jdbc.count("select count(*) from warehouse_entries where id=:id", Map.of("id", entryId))).isZero();
    }

    @Test
    void administratorsManageWarehousePortsWhileMembersUseTheActiveCatalog() throws Exception {
        long nonce = Math.abs(System.nanoTime());
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        String memberPassword = "Warehouse-Port-Member-Password-42!";
        String memberName = "warehouse-port-member-" + nonce;
        createMember(memberName, memberPassword);
        SessionCookies member = login(memberName, memberPassword);

        assertStatus(get("/api/admin/master-data/warehouse-ports", member.sessionCookie()),
                403, "GET", "/api/admin/master-data/warehouse-ports member");
        String name = "Integration Harbor " + nonce;
        HttpResponse<String> created = post("/api/admin/master-data/warehouse-ports",
                "{\"name\":\"" + name + "\",\"sort_order\":900,\"is_active\":true}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(created, 201, "POST", "/api/admin/master-data/warehouse-ports");
        long portId = jsonId(created.body());
        assertThat(get("/api/warehouse/ports", member.sessionCookie()).body()).contains(name);

        String renamed = "Renamed Harbor " + nonce;
        assertStatus(put("/api/admin/master-data/warehouse-ports/" + portId,
                "{\"name\":\"" + renamed + "\",\"sort_order\":901,\"is_active\":true}", administrator),
                200, "PUT", "/api/admin/master-data/warehouse-ports/{port_id}");
        assertThat(get("/api/warehouse/ports", member.sessionCookie()).body()).contains(renamed).doesNotContain(name);

        assertStatus(delete("/api/admin/master-data/warehouse-ports/" + portId,
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                204, "DELETE", "/api/admin/master-data/warehouse-ports/{port_id}");
        assertThat(get("/api/warehouse/ports", member.sessionCookie()).body()).doesNotContain(renamed);
    }

    @Test
    void exposesHealthAndReadinessButProtectsMemberApis() throws Exception {
        HttpResponse<String> health = get("/api/health");
        HttpResponse<String> readiness = get("/api/health/ready");
        HttpResponse<String> protectedApi = get("/api/builds");

        assertThat(health.statusCode()).isEqualTo(200);
        assertThat(health.body()).contains("\"status\":\"ok\"");
        assertThat(readiness.statusCode()).isEqualTo(200);
        assertThat(readiness.body()).contains("\"status\":\"ready\"");
        assertThat(protectedApi.statusCode()).isEqualTo(401);
    }

    @Test
    void exposesRegistrationAndOfficialFleetWithoutAuthentication() throws Exception {
        HttpResponse<String> fleet = get("/api/fleets/public/official");
        assertStatus(fleet, 200, "GET", "/api/fleets/public/official");
        assertThat(fleet.body()).contains("\"slug\":\"royal-blackwater-fleet\"")
                .contains("\"role\":\"fleet_admiral\"");

        HttpResponse<String> csrfBootstrap = get("/api/auth/me");
        String setCookie = csrfBootstrap.headers().firstValue("set-cookie").orElseThrow();
        var xsrfMatcher = Pattern.compile("(?:^|;\\s*)XSRF-TOKEN=([^;]+)").matcher(setCookie);
        assertThat(xsrfMatcher.find()).isTrue();
        String xsrf = xsrfMatcher.group(1);
        HttpRequest register = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/auth/register"))
                .header("Content-Type", "application/json")
                .header("Cookie", "XSRF-TOKEN=" + xsrf)
                .header("X-XSRF-TOKEN", xsrf)
                .POST(HttpRequest.BodyPublishers.ofString(
                        "{\"username\":\"integration-public-route\",\"password\":\"Integration-Password-42!\","
                                + "\"display_name\":\"Integration Public Route\",\"wants_fleet_membership\":false}"))
                .build();
        HttpResponse<String> registration = HttpClient.newHttpClient().send(register, HttpResponse.BodyHandlers.ofString());
        assertThat(registration.statusCode()).isIn(202, 409);
    }

    @Test
    void reviewsRegistrationRequestsAcrossApproveRejectAndAllStatusLifecycles() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        long nonce = Math.abs(System.nanoTime());
        long fleetId = ((Number) bootstrapMembership().get("fleet_id")).longValue();

        String approvedUsername = "review-approve-" + nonce;
        String approvedPassword = "Review-Approved-Password-42!";
        assertStatus(submitPublicRegistration(approvedUsername, approvedPassword,
                        "Approved Review User", true, fleetId, "Please review fleet access."),
                202, "POST", "/api/auth/register");

        HttpResponse<String> pending = get(
                "/api/admin/registration-requests?status=pending&search=" + approvedUsername,
                administrator.sessionCookie());
        assertStatus(pending, 200, "GET", "/api/admin/registration-requests?status=pending");
        assertThat(pending.body()).contains(approvedUsername, "\"status\":\"pending\"");
        long approvedRequestId = jsonId(pending.body());

        HttpResponse<String> all = get(
                "/api/admin/registration-requests?status=all&search=" + approvedUsername,
                administrator.sessionCookie());
        assertStatus(all, 200, "GET", "/api/admin/registration-requests?status=all");
        assertThat(all.body()).contains(approvedUsername);

        HttpResponse<String> approved = post(
                "/api/admin/registration-requests/" + approvedRequestId + "/approve",
                "{\"note\":\"Approved by integration access review.\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(approved, 200, "POST", "/api/admin/registration-requests/{request_id}/approve");
        assertThat(approved.body()).contains("\"status\":\"approved\"",
                "\"created_user\":{", "\"reviewed_by\":{");
        assertThat(jdbc.count("select count(*) from users where username=:username",
                Map.of("username", approvedUsername))).isEqualTo(1);
        assertThat(jdbc.count("""
                select count(*) from fleet_memberships m join users u on u.id=m.user_id
                where u.username=:username and m.fleet_id=:fleetId and m.status='pending'
                """, Map.of("username", approvedUsername, "fleetId", fleetId))).isEqualTo(1);
        assertStatus(post("/api/auth/login",
                        "{\"username\":\"" + approvedUsername + "\",\"password\":\""
                                + approvedPassword + "\"}", null, null, localOrigin()),
                200, "POST", "/api/auth/login");
        assertStatus(get("/api/admin/registration-requests?status=approved&search=" + approvedUsername,
                        administrator.sessionCookie()),
                200, "GET", "/api/admin/registration-requests?status=approved");
        assertStatus(post("/api/admin/registration-requests/" + approvedRequestId + "/approve",
                        "{}", administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                400, "POST", "/api/admin/registration-requests/{request_id}/approve repeated");

        String rejectedUsername = "review-reject-" + nonce;
        assertStatus(submitPublicRegistration(rejectedUsername, "Review-Rejected-Password-42!",
                        "Rejected Review User", false, null, null),
                202, "POST", "/api/auth/register");
        HttpResponse<String> rejectPending = get(
                "/api/admin/registration-requests?status=pending&search=" + rejectedUsername,
                administrator.sessionCookie());
        assertStatus(rejectPending, 200, "GET", "/api/admin/registration-requests?status=pending");
        long rejectedRequestId = jsonId(rejectPending.body());
        HttpResponse<String> rejected = post(
                "/api/admin/registration-requests/" + rejectedRequestId + "/reject",
                "{\"note\":\"Rejected by integration access review.\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(rejected, 200, "POST", "/api/admin/registration-requests/{request_id}/reject");
        assertThat(rejected.body()).contains("\"status\":\"rejected\"", "\"reviewed_by\":{");
        assertThat(jdbc.count("select count(*) from users where username=:username",
                Map.of("username", rejectedUsername))).isZero();
        assertStatus(get("/api/admin/registration-requests?status=rejected&search=" + rejectedUsername,
                        administrator.sessionCookie()),
                200, "GET", "/api/admin/registration-requests?status=rejected");
        assertStatus(post("/api/admin/registration-requests/" + rejectedRequestId + "/reject",
                        "{}", administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                400, "POST", "/api/admin/registration-requests/{request_id}/reject repeated");
    }

    @Test
    void roundTripsAdministrativeAccountBuildRolePrivacyAndIpBlockWorkflows() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        long nonce = Math.abs(System.nanoTime());

        String moderatorUsername = "integration-mod-" + nonce;
        HttpResponse<String> moderator = post("/api/admin/moderators",
                "{\"username\":\"" + moderatorUsername
                        + "\",\"password\":\"Integration-Moderator-Password-42!\","
                        + "\"display_name\":\"Integration Moderator\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(moderator, 201, "POST", "/api/admin/moderators");
        long moderatorId = jsonId(moderator.body());
        assertStatus(put("/api/admin/users/" + moderatorId,
                        "{\"role\":\"user\",\"is_active\":true}", administrator),
                200, "PUT", "/api/admin/users/{user_id}");
        assertStatus(get("/api/admin/users?search=" + moderatorUsername, administrator.sessionCookie()),
                200, "GET", "/api/admin/users?search");

        String roleSlug = "integration-" + Long.toString(nonce, 36);
        HttpResponse<String> role = post("/api/admin/build-roles",
                "{\"slug\":\"" + roleSlug
                        + "\",\"label\":\"Integration Role\",\"sort_order\":9000}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(role, 201, "POST", "/api/admin/build-roles");
        assertStatus(put("/api/admin/build-roles/" + roleSlug,
                        "{\"label\":\"Integration Role Updated\",\"description\":\"Stateful API regression.\",\"sort_order\":9001}",
                        administrator),
                200, "PUT", "/api/admin/build-roles/{slug}");
        assertStatus(delete("/api/admin/build-roles/" + roleSlug,
                        administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                204, "DELETE", "/api/admin/build-roles/{slug}");

        jdbc.update("delete from data_subject_requests where subject_user_id=(select id from users where username='admin') and request_type='correction'", Map.of());
        HttpResponse<String> privacyRequest = post("/api/privacy/requests",
                "{\"request_type\":\"correction\",\"details\":\"Stateful integration correction request.\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(privacyRequest, 201, "POST", "/api/privacy/requests");
        long privacyRequestId = jsonId(privacyRequest.body());
        assertStatus(put("/api/admin/privacy-requests/" + privacyRequestId,
                        "{\"decision\":\"complete\",\"resolution_note\":\"Handled by integration review.\"}",
                        administrator),
                200, "PUT", "/api/admin/privacy-requests/{request_id}");

        String contactEmail = "privacy-" + nonce + "@example.test";
        HttpResponse<String> contact = post("/api/privacy/contact",
                "{\"reply_email\":\"" + contactEmail
                        + "\",\"subject\":\"Integration privacy review\","
                        + "\"message\":\"This is a stateful privacy contact integration request.\"}",
                null, null, localOrigin());
        assertStatus(contact, 201, "POST", "/api/privacy/contact");
        long contactId = ((Number) jdbc.required(
                "select id from privacy_contact_requests where reply_email=:email order by id desc limit 1",
                Map.of("email", contactEmail)).get("id")).longValue();
        assertStatus(put("/api/admin/privacy-requests/contacts/" + contactId,
                        "{\"decision\":\"reject\",\"resolution_note\":\"Closed by integration review.\"}",
                        administrator),
                200, "PUT", "/api/admin/privacy-requests/contacts/{request_id}");

        String blockedIp = "198.51.100." + (20 + (nonce % 200));
        HttpResponse<String> block = post("/api/admin/ip-blocks",
                "{\"ip_address\":\"" + blockedIp
                        + "\",\"reason\":\"Integration security review\",\"notes\":\"Stateful no-5xx regression.\"}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(block, 201, "POST", "/api/admin/ip-blocks");
        long blockId = jsonId(block.body());
        assertStatus(post("/api/admin/ip-blocks/" + blockId + "/unblock",
                        "{\"reason\":\"Integration cleanup\"}",
                        administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                200, "POST", "/api/admin/ip-blocks/{block_id}/unblock");

        assertStatus(get("/api/admin/audit-logs?actor=admin&limit=100", administrator.sessionCookie()),
                200, "GET", "/api/admin/audit-logs");
    }

    @Test
    void enforcesAuthenticationAdminRoleRequestBoundaryAndCsrf() throws Exception {
        assertThat(get("/api/admin/users").statusCode()).isEqualTo(401);

        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        assertThat(get("/api/admin/users", administrator.sessionCookie()).statusCode()).isEqualTo(200);

        String memberUsername = "integration-member";
        String memberPassword = "Integration-Member-Password-42!";
        createMember(memberUsername, memberPassword);
        SessionCookies member = login(memberUsername, memberPassword);
        assertThat(get("/api/admin/users", member.sessionCookie()).statusCode()).isEqualTo(403);

        HttpResponse<String> missingCsrf = post(
                "/api/auth/change-password",
                "{\"current_password\":\"wrong\",\"new_password\":\"Different-Password-42!\"}",
                member.sessionCookie(), null, localOrigin());
        assertThat(missingCsrf.statusCode()).isEqualTo(403);

        HttpResponse<String> invalidCurrentPassword = post(
                "/api/auth/change-password",
                "{\"current_password\":\"wrong\",\"new_password\":\"Different-Password-42!\"}",
                member.cookieHeader(), member.csrfToken(), localOrigin());
        assertThat(invalidCurrentPassword.statusCode()).isEqualTo(400);
        assertThat(invalidCurrentPassword.body()).doesNotContain("Exception", "stackTrace");

        HttpResponse<String> crossSiteLogin = post(
                "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"Integration-Test-Admin-Password-42!\"}",
                null, null, "https://untrusted.example");
        assertThat(crossSiteLogin.statusCode()).isEqualTo(403);
    }

    @Test
    void reservesSharedContentMutationsForModeratorsAndAdministrators() throws Exception {
        String memberPassword = "Read-Only-Member-Password-42!";
        createUser("integration-read-only", memberPassword, "user");
        SessionCookies member = login("integration-read-only", memberPassword);

        for (String path : new String[] {
                "/api/builds", "/api/builds/1/upvote", "/api/calendar/events", "/api/files",
                "/api/fleets", "/api/forum/threads", "/api/forum/threads/1/posts",
                "/api/groups", "/api/groups/1/close", "/api/guides", "/api/squads",
                "/api/squads/1/members", "/api/strategies"
        }) {
            assertThat(post(path, "{}", member.cookieHeader(), member.csrfToken(), localOrigin()).statusCode())
                    .as("member POST %s", path).isEqualTo(403);
        }
        for (String path : new String[] {
                "/api/builds/mine/1", "/api/builds/1/printout", "/api/calendar/events/1",
                "/api/fleets/1", "/api/forum/posts/1", "/api/forum/threads/1", "/api/guides/1",
                "/api/newcomer-guide", "/api/squads/1", "/api/strategies/1",
                "/api/strategies/1/publication"
        }) {
            assertThat(put(path, "{}", member).statusCode())
                    .as("member PUT %s", path).isEqualTo(403);
        }
        for (String path : new String[] {
                "/api/builds/mine/1", "/api/calendar/events/1", "/api/files/1",
                "/api/forum/posts/1", "/api/guides/1", "/api/squads/1", "/api/strategies/1"
        }) {
            assertThat(delete(path, member.cookieHeader(), member.csrfToken(), localOrigin()).statusCode())
                    .as("member DELETE %s", path).isEqualTo(403);
        }

        assertThat(put("/api/profile", "{}", member).statusCode()).isNotEqualTo(403);
        assertThat(post("/api/fleets/join", "{}", member.cookieHeader(), member.csrfToken(), localOrigin()).statusCode())
                .isNotEqualTo(403);
        assertThat(post("/api/groups/999999/join", "{}", member.cookieHeader(), member.csrfToken(), localOrigin()).statusCode())
                .isNotEqualTo(403);

        long fleetId = ((Number) bootstrapMembership().get("fleet_id")).longValue();
        assertThat(get("/api/fleets", member.sessionCookie()).statusCode()).isEqualTo(200);
        assertThat(get("/api/squads", member.sessionCookie()).statusCode()).isEqualTo(200);
        assertThat(get("/api/fleets/manageable", member.sessionCookie()).statusCode()).isEqualTo(403);
        assertThat(get("/api/fleets/" + fleetId + "/manage", member.sessionCookie()).statusCode()).isEqualTo(403);
        assertThat(get("/api/fleets/" + fleetId + "/roles", member.sessionCookie()).statusCode()).isEqualTo(403);
        assertThat(get("/api/squads/roster", member.sessionCookie()).statusCode()).isEqualTo(403);

        String moderatorPassword = "Content-Moderator-Password-42!";
        createUser("integration-content-moderator", moderatorPassword, "moderator");
        SessionCookies moderator = login("integration-content-moderator", moderatorPassword);
        assertThat(post("/api/builds", "{}", moderator.cookieHeader(), moderator.csrfToken(), localOrigin()).statusCode())
                .isNotEqualTo(403);
        assertThat(get("/api/admin/users", moderator.sessionCookie()).statusCode()).isEqualTo(403);
    }

    @Test
    void rejectsInvalidPublicMutationWithoutLeakingImplementationDetails() throws Exception {
        HttpResponse<String> response = post("/api/auth/register", "{}", null, null, localOrigin());

        assertThat(response.statusCode()).isEqualTo(400);
        assertThat(response.body()).contains("\"detail\":");
        assertThat(response.body()).doesNotContain("Exception", "stackTrace", "org.springframework");
    }

    @Test
    void acceptsIsoDatesAndUtcTimestampsProducedByTheFrontend() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");

        for (String path : new String[] {
                "/api/admin/registration-requests?from_date=2030-01-01&to_date=2030-02-01",
                "/api/admin/audit-logs?from_date=2030-01-01&to_date=2030-02-01",
                "/api/admin/logs/security-dashboard?from_date=2030-01-01&to_date=2030-02-01"
        }) {
            assertStatus(get(path, administrator.sessionCookie()), 200, "GET", path);
        }

        HttpResponse<String> calendar = get(
                "/api/calendar/events?start=2030-01-01T00:00:00.000Z&end=2030-02-01T00:00:00.000Z",
                administrator.sessionCookie());
        assertStatus(calendar, 200, "GET", "/api/calendar/events");

        HttpResponse<String> invalidCalendar = get(
                "/api/calendar/events?start=not-a-timestamp", administrator.sessionCookie());
        assertStatus(invalidCalendar, 400, "GET", "/api/calendar/events?start=not-a-timestamp");
        assertThat(invalidCalendar.body()).doesNotContain("Exception", "stackTrace", "org.springframework");

        HttpResponse<String> created = post(
                "/api/calendar/events",
                "{\"title\":\"UTC contract integration event\",\"category\":\"other\","
                        + "\"start_at\":\"2030-01-15T18:00:00.000Z\","
                        + "\"end_at\":\"2030-01-15T20:00:00.000Z\","
                        + "\"raid_helper_enabled\":false}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertThat(created.statusCode()).isEqualTo(201);
        assertThat(created.body()).contains("\"title\":\"UTC contract integration event\"");

        long eventId = jsonId(created.body());
        assertStatus(get("/api/calendar/events/" + eventId, administrator.sessionCookie()),
                200, "GET", "/api/calendar/events/{event_id}");
    }

    @Test
    void loadsEveryStaffOverviewDataSourceWithoutServerErrors() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");

        for (String path : new String[] {
                "/api/admin/registration-requests?status=pending",
                "/api/calendar/events?start=2030-01-01T00:00:00.000Z&end=2030-04-01T00:00:00.000Z",
                "/api/admin/forum/threads",
                "/api/admin/guides",
                "/api/groups",
                "/api/admin/builds",
                "/api/admin/build-roles",
                "/api/admin/users",
                "/api/admin/master-data/overview",
                "/api/admin/master-data/taxonomy",
                "/api/admin/master-data/categories",
                "/api/admin/master-data/options",
                "/api/admin/master-data/ships",
                "/api/admin/logs/security-dashboard?sort=threat&limit=100",
                "/api/admin/ip-blocks/summary"
        }) {
            assertStatus(get(path, administrator.sessionCookie()), 200, "GET", path);
        }
    }

    @Test
    void persistsAndReloadsAnonymousCookieConsent() throws Exception {
        HttpResponse<String> initial = get("/api/privacy/cookie-consent");
        assertThat(initial.statusCode()).isEqualTo(200);
        assertThat(initial.headers().firstValue("cache-control")).hasValue("no-store, private");
        assertThat(initial.body()).contains("\"has_decision\":false");

        HttpResponse<String> saved = post(
                "/api/privacy/cookie-consent",
                "{\"necessary\":true,\"preferences\":true,\"analytics\":false,\"external_media\":true}",
                null, null, localOrigin());
        assertThat(saved.statusCode()).isEqualTo(200);
        assertThat(saved.headers().firstValue("cache-control")).hasValue("no-store, private");
        assertThat(saved.body()).contains("\"has_decision\":true", "\"preferences\":true", "\"external_media\":true");

        HttpResponse<String> reloaded = get(
                "/api/privacy/cookie-consent", cookie(saved, "rbf_cookie_consent"));
        assertThat(reloaded.statusCode()).isEqualTo(200);
        assertThat(reloaded.headers().firstValue("cache-control")).hasValue("no-store, private");
        assertThat(reloaded.body()).contains("\"has_decision\":true", "\"preferences\":true", "\"analytics\":false",
                "\"external_media\":true");
    }

}
