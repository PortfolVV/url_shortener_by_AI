<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import BaseSpinner from '@/atoms/BaseSpinner.vue'
import AnalyticsPanel from '@/organisms/AnalyticsPanel.vue'
import api, { getApiErrorMessage } from '@/services/api'
import DashboardTemplate from '@/templates/DashboardTemplate.vue'

const route = useRoute()

const stats = ref(null)
const loading = ref(true)
const error = ref('')

async function loadStats(shortCode) {
  loading.value = true
  error.value = ''
  stats.value = null
  try {
    const { data } = await api.get(`/stats/${shortCode}`)
    stats.value = data
  } catch (requestError) {
    error.value = getApiErrorMessage(requestError)
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.code,
  (code) => {
    if (code) loadStats(code)
  },
  { immediate: true },
)
</script>

<template>
  <DashboardTemplate>
    <div class="stats-page stack">
      <div class="spread">
        <div>
          <RouterLink :to="{ name: 'dashboard' }" class="back-link">
            ← Ко всем ссылкам
          </RouterLink>
          <h1 class="stats-page__title">
            Статистика
            <span v-if="stats" class="gradient-text mono">
              /l/{{ stats.short_code }}
            </span>
          </h1>
        </div>
        <RouterLink :to="{ name: 'dashboard' }" class="btn btn--ghost btn--sm">
          В кабинет
        </RouterLink>
      </div>

      <div v-if="loading" class="stats-page__loading">
        <BaseSpinner :size="34" />
        <span class="muted">Собираем аналитику…</span>
      </div>

      <div v-else-if="error" class="alert alert--error" role="alert">
        <span class="alert__icon" aria-hidden="true">!</span>
        <span>{{ error }}</span>
      </div>

      <AnalyticsPanel v-else-if="stats" :stats="stats" />
    </div>
  </DashboardTemplate>
</template>

<style scoped>
.stats-page {
  gap: 24px;
}

.stats-page__title {
  margin: 10px 0 0;
  font-size: clamp(1.7rem, 3.6vw, 2.4rem);
  letter-spacing: -0.03em;
}

.back-link {
  color: var(--muted);
  font-size: 0.86rem;
}

.back-link:hover {
  color: var(--text);
}

.stats-page__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 90px 20px;
}
</style>
