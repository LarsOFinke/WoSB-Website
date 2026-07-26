<script setup>
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import LinkedBuildList from '@/core/components/LinkedBuildList.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { deleteGuide, getGuide } from '@/modules/guides/api/guides'
import GuideTableOfContents from '@/modules/guides/components/GuideTableOfContents.vue'
import { useGuidePrintActions } from '@/modules/guides/composables/useGuidePrintActions'
import { formatGuideDate, guideHeadingNavigation } from '@/modules/guides/domain/guidePresentation'
import '@/modules/guides/styles/guides.css'
import { unembeddedAttachments, unembeddedBuilds } from '@/shared/content/richTextEmbeds'

const props = defineProps({ id: { type: String, required: true } })
const { t } = useLocale()
const { isStaff, user } = useSession()
const guide = ref(null)
const loading = ref(false)
const deleting = ref(false)
const error = ref('')
const { printBusy, printStatus, printGuide } = useGuidePrintActions(guide, { t })

const canManage = computed(() => guide.value && user.value
  && (guide.value.owner_id === user.value.id || isStaff.value))
const galleryAttachments = computed(() => guide.value
  ? unembeddedAttachments(guide.value.attachments || [], guide.value.body)
  : [])
const linkedBuildCards = computed(() => guide.value
  ? unembeddedBuilds(guide.value.builds || [], guide.value.body)
  : [])
const headings = computed(() => guideHeadingNavigation(guide.value?.body))

async function loadGuide() {
  loading.value = true
  error.value = ''
  try {
    guide.value = await getGuide(props.id)
  } catch (err) {
    error.value = err.message || t('guides.detail.loadError')
  } finally {
    loading.value = false
  }
}

async function submitDelete() {
  if (!guide.value || !window.confirm(t('guides.detail.confirmDelete'))) return
  deleting.value = true
  error.value = ''
  try {
    await deleteGuide(guide.value.id)
    window.location.href = '/guides'
  } catch (err) {
    error.value = err.message || t('guides.detail.deleteError')
  } finally {
    deleting.value = false
  }
}

onMounted(loadGuide)
</script>

<template>
  <section class="guide-reader-page" aria-labelledby="guide-detail-title">
    <div class="guide-module-frame guide-reader-frame">
      <header class="guide-reader-commandbar">
        <RouterLink class="guide-back-action" to="/guides">
          <AppIcon name="chevron-left" :size="18" />
          {{ t('common.back') }}
        </RouterLink>
        <div class="guide-reader-actions">
          <button
            v-if="guide"
            class="guide-toolbar-action"
            data-testid="guide-print-action"
            type="button"
            :disabled="printBusy"
            @click="printGuide"
          >
            {{ printBusy ? t('guides.print.opening') : t('guides.print.action') }}
          </button>
          <RouterLink v-if="canManage" class="guide-primary-action is-compact" :to="`/guides/${guide.id}/edit`">
            <AppIcon name="edit" :size="17" />
            {{ t('guides.detail.edit') }}
          </RouterLink>
        </div>
      </header>

      <p v-if="printStatus" class="guide-inline-status" role="status">{{ printStatus }}</p>
      <p v-if="loading" class="guide-state-message">{{ t('guides.detail.loading') }}</p>
      <p v-else-if="error" class="guide-state-message error-text">{{ error }}</p>

      <template v-else-if="guide">
        <header class="guide-reader-masthead">
          <h1 id="guide-detail-title">{{ guide.title }}</h1>
          <p v-if="guide.summary">{{ guide.summary }}</p>
          <dl class="guide-reader-meta">
            <div>
              <dt>{{ t('masterData.fields.category') }}</dt>
              <dd>{{ t(`guides.categories.${guide.category}`) }}</dd>
            </div>
            <div>
              <dt>{{ t('guides.print.author') }}</dt>
              <dd>{{ guide.owner.display_name }}</dd>
            </div>
            <div>
              <dt>{{ t('guides.print.updated') }}</dt>
              <dd><time :datetime="guide.updated_at || guide.created_at">{{ formatGuideDate(guide.updated_at || guide.created_at) }}</time></dd>
            </div>
          </dl>
        </header>

        <div class="guide-reading-layout">
          <article class="guide-reading-article">
            <RichTextRenderer
              :body="guide.body"
              :attachments="guide.attachments"
              :builds="guide.builds"
              heading-id-prefix="guide-section"
            />

            <section v-if="linkedBuildCards.length || galleryAttachments.length" class="guide-reference-section">
              <div v-if="linkedBuildCards.length" class="guide-reference-group">
                <h2>{{ t('guides.print.linkedBuildsTitle') }}</h2>
                <LinkedBuildList :builds="linkedBuildCards" />
              </div>
              <div v-if="galleryAttachments.length" class="guide-reference-group">
                <h2>{{ t('guides.print.attachmentsTitle') }}</h2>
                <AttachmentGallery :attachments="galleryAttachments" />
              </div>
            </section>
          </article>

          <aside class="guide-reading-aside">
            <GuideTableOfContents :headings="headings" />
          </aside>
        </div>

        <footer v-if="canManage" class="guide-owner-footer">
          <span>{{ t('guides.detail.manageEyebrow') }}</span>
          <button class="danger-action" type="button" :disabled="deleting" @click="submitDelete">
            {{ deleting ? t('guides.detail.deleting') : t('guides.detail.delete') }}
          </button>
        </footer>
      </template>
    </div>
  </section>
</template>
