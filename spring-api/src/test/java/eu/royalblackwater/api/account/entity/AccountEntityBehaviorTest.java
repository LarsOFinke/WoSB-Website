package eu.royalblackwater.api.account.entity;

import java.time.LocalDateTime;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.assertj.core.api.Assertions.assertThat;

class AccountEntityBehaviorTest {
    private static final LocalDateTime CREATED = LocalDateTime.of(2030, 1, 15, 12, 0);
    private static final LocalDateTime UPDATED = CREATED.plusHours(2);

    @Test
    void registrationApprovalPersistsDecisionAndScrubsPasswordSecret() {
        RegistrationRequestEntity request = new RegistrationRequestEntity(
                "captain", "secret-hash", "Captain", true, 7, "application", CREATED);

        request.approve(11, 99, "welcome", UPDATED);

        assertThat(request.getStatus()).isEqualTo("approved");
        assertThat(request.getDecisionNote()).isEqualTo("welcome");
        assertThat(request.getReviewedById()).isEqualTo(11);
        assertThat(request.getCreatedUserId()).isEqualTo(99);
        assertThat(request.getPasswordHash()).isEqualTo("!reviewed-registration-secret-removed!");
        assertThat(request.getReviewedAt()).isEqualTo(UPDATED);
        assertThat(request.getUpdatedAt()).isEqualTo(UPDATED);
        assertThat(request.getUsername()).isEqualTo("captain");
        assertThat(request.getDisplayName()).isEqualTo("Captain");
        assertThat(request.isWantsFleetMembership()).isTrue();
        assertThat(request.getFleetId()).isEqualTo(7);
        assertThat(request.getFleetApplicationNote()).isEqualTo("application");
        assertThat(request.getCreatedAt()).isEqualTo(CREATED);
    }

    @Test
    void registrationRejectionPersistsDecisionAndDoesNotCreateUser() {
        RegistrationRequestEntity request = new RegistrationRequestEntity(
                "captain", "secret-hash", "Captain", false, null, null, CREATED);

        request.reject(12, "not now", UPDATED);

        assertThat(request.getStatus()).isEqualTo("rejected");
        assertThat(request.getDecisionNote()).isEqualTo("not now");
        assertThat(request.getReviewedById()).isEqualTo(12);
        assertThat(request.getCreatedUserId()).isNull();
        assertThat(request.getPasswordHash()).isEqualTo("!reviewed-registration-secret-removed!");
        assertThat(request.getReviewedAt()).isEqualTo(UPDATED);
    }

    @Test
    void userLifecycleCreatesUpdatesAndRestoresItsProfile() {
        SiteRoleEntity role = role("user", false, false, 10);
        UserEntity user = new UserEntity("captain", "hash", role, "Captain", CREATED);

        assertThat(user.getUsername()).isEqualTo("captain");
        assertThat(user.getPasswordHash()).isEqualTo("hash");
        assertThat(user.getSiteRole()).isSameAs(role);
        assertThat(user.isActive()).isTrue();
        assertThat(user.isBootstrapAdmin()).isFalse();
        assertThat(user.getCreatedAt()).isEqualTo(CREATED);
        assertThat(user.getUpdatedAt()).isEqualTo(CREATED);
        assertThat(user.getProfile().getDisplayName()).isEqualTo("Captain");
        assertThat(user.getFleetMemberships()).isEmpty();

        user.setPasswordHash("new-hash");
        SiteRoleEntity moderator = role("moderator", true, false, 20);
        user.setSiteRole(moderator);
        user.setActive(false);
        user.touch(UPDATED);
        assertThat(user.getPasswordHash()).isEqualTo("new-hash");
        assertThat(user.getSiteRole()).isSameAs(moderator);
        assertThat(user.isActive()).isFalse();
        assertThat(user.getUpdatedAt()).isEqualTo(UPDATED);

        UserProfileEntity existing = user.ensureProfile(UPDATED);
        assertThat(existing).isSameAs(user.getProfile());

        ReflectionTestUtils.setField(user, "profile", null);
        UserProfileEntity recreated = user.ensureProfile(UPDATED);
        assertThat(recreated.getDisplayName()).isEqualTo("captain");
        assertThat(user.getProfile()).isSameAs(recreated);
    }

    @Test
    void profileUpdateAndPreferenceReplacementAreOrderedAndReplaceOldState() {
        UserEntity user = new UserEntity("captain", "hash", role("user", false, false, 10), "Captain", CREATED);
        UserProfileEntity profile = user.getProfile();

        profile.update("Admiral", "Blackwater", "PvP", "evenings", "Europe/Berlin", "captain#1", "note", UPDATED);
        assertThat(profile.getDisplayName()).isEqualTo("Admiral");
        assertThat(profile.getExternalFleetName()).isEqualTo("Blackwater");
        assertThat(profile.getPreferredFocus()).isEqualTo("PvP");
        assertThat(profile.getAvailability()).isEqualTo("evenings");
        assertThat(profile.getTimezone()).isEqualTo("Europe/Berlin");
        assertThat(profile.getDiscordHandle()).isEqualTo("captain#1");
        assertThat(profile.getNote()).isEqualTo("note");

        profile.replaceShipPreferences(List.of(8, 3, 5));
        assertThat(profile.getShipPreferences()).extracting(UserProfileShipPreferenceEntity::getShipId)
                .containsExactly(8, 3, 5);
        assertThat(profile.getShipPreferences()).extracting(value -> ReflectionTestUtils.getField(value, "sortOrder"))
                .containsExactly(10, 20, 30);

        profile.replaceShipPreferences(List.of(9));
        assertThat(profile.getShipPreferences()).extracting(UserProfileShipPreferenceEntity::getShipId)
                .containsExactly(9);

        profile.replaceRolePreferences(List.of(4, 2));
        assertThat(profile.getRolePreferences()).extracting(UserProfileRolePreferenceEntity::getFleetRoleId)
                .containsExactly(4, 2);
        assertThat(profile.getRolePreferences()).extracting(value -> ReflectionTestUtils.getField(value, "sortOrder"))
                .containsExactly(10, 20);

        profile.replaceRolePreferences(List.of());
        assertThat(profile.getRolePreferences()).isEmpty();
    }

    @Test
    void siteRoleFlagsRemainAuthoritative() {
        SiteRoleEntity admin = role("admin", true, true, 100);
        ReflectionTestUtils.setField(admin, "id", 1);
        ReflectionTestUtils.setField(admin, "label", "Administrator");

        assertThat(admin.getId()).isEqualTo(1);
        assertThat(admin.getCode()).isEqualTo("admin");
        assertThat(admin.getLabel()).isEqualTo("Administrator");
        assertThat(admin.getRank()).isEqualTo(100);
        assertThat(admin.isStaff()).isTrue();
        assertThat(admin.canManageSystem()).isTrue();
    }

    private static SiteRoleEntity role(String code, boolean staff, boolean system, int rank) {
        SiteRoleEntity role = new SiteRoleEntity();
        ReflectionTestUtils.setField(role, "code", code);
        ReflectionTestUtils.setField(role, "staff", staff);
        ReflectionTestUtils.setField(role, "canManageSystem", system);
        ReflectionTestUtils.setField(role, "rank", rank);
        return role;
    }
}
