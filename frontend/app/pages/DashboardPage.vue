<script setup>
import { onMounted, ref } from 'vue'

import BaseBadge from '@/atoms/BaseBadge.vue'
import BaseButton from '@/atoms/BaseButton.vue'
import LinksList from '@/organisms/LinksList.vue'
import ShortenerPanel from '@/organisms/ShortenerPanel.vue'
import api, { getApiErrorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import DashboardTemplate from '@/templates/DashboardTemplate.vue'

const auth = useAuthStore()

const links = ref([])
const total = ref(0)
const loading = ref(true)
const error = ref('')

async function loadLinks() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/links', {
      params: { limit: 100, offset: 0 },
    })
    links.value = data.items
    total.value = data.total
  } catch (requestError) {
    error.value = getApiErrorMessage(requestError)
  } finally {
    loading.value = false
  }
}

async function removeLink(link) {
  const confirmed = window.confirm(
    `Удалить ссылку /l/${link.short_code}? Вся статистика переходов тоже будет удалена.`,
  )
  if (!confirmed) return

  try {
    await api.delete(`/links/${link.short_code}`)
    await loadLinks()
  } catch (requestError) {
    error.value = getApiErrorMessage(requestError)
  }
}

onMounted(loadLinks)
</script>

<template>
  <DashboardTemplate>
    <div class="dashboard stack">
      <header class="spread dashboard__header">
        <div>
          <span class="badge badge--info">Личный кабинет</span>
          <h1 class="dashboard__title">Мои ссылки</h1>
          <p class="section-subtitle">
            {{ auth.user?.email }} · ссылки и статистика в PostgreSQL
          </p>
        </div>
        <BaseBadge tone="success">{{ total }} всего</BaseBadge>
      </header>

      <ShortenerPanel compact @created="loadLinks" />

      <div v-if="error" class="alert alert--error" role="alert">
        <span class="alert__icon" aria-hidden="true">!</span>
        <span>{{ error }}</span>
      </div>

      <LinksList
        :links="links"
        :total="total"
        :loading="loading"
        @delete="removeLink"
      >
        <template #actions>
          <BaseButton size="sm" variant="ghost" :loading="loading" @click="loadLinks">
            Обновить
          </BaseButton>
        </template>
      </LinksList>
    </div>
  </DashboardTemplate>
</template>

<style scoped>
.dashboard {
  gap: 28px;
}

.dashboard__header {
  align-items: flex-end;
}

.dashboard__title {
  margin: 10px 0 4px;
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  line-height: 1.1;
  letter-spacing: -0.03em;
}
</style>
