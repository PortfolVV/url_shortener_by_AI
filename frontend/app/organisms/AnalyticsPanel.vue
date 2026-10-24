<script setup>
import { computed } from 'vue'

import GlassCard from '@/atoms/GlassCard.vue'
import StatCard from '@/molecules/StatCard.vue'
import { formatDate, formatNumber } from '@/utils/format'

const props = defineProps({
  stats: { type: Object, required: true },
})

const topSources = computed(() => {
  const counts = new Map()
  for (const click of props.stats.clicks || []) {
    const source = click.referer_source || 'direct'
    counts.set(source, (counts.get(source) || 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
})

const shownClicks = computed(() => props.stats.clicks?.length || 0)

function shorten(value, max = 46) {
  if (!value) return '—'
  return value.length > max ? `${value.slice(0, max)}…` : value
}
</script>

<template>
  <div class="analytics">
    <div class="analytics__cards">
      <StatCard
        label="Всего переходов"
        :value="formatNumber(stats.total_clicks)"
        hint="за всё время"
        accent="violet"
      />
      <StatCard
        label="Последний переход"
        :value="stats.last_clicked_at ? formatDate(stats.last_clicked_at) : '—'"
        hint="по времени сервера"
        accent="cyan"
      />
      <StatCard
        label="Источников"
        :value="formatNumber(topSources.length)"
        hint="уникальные referer"
        accent="green"
      />
      <StatCard
        label="Срок действия"
        :value="stats.expires_at ? formatDate(stats.expires_at) : 'Бессрочно'"
        :hint="stats.expires_at ? 'ссылка истечёт' : 'не истекает'"
        accent="pink"
      />
    </div>

    <GlassCard flat class="analytics__meta">
      <div class="analytics__meta-row">
        <div>
          <span class="analytics__label">Оригинальная ссылка</span>
          <a
            :href="stats.original_url"
            target="_blank"
            rel="noopener"
            class="analytics__link"
          >
            {{ stats.original_url }}
          </a>
        </div>
        <div>
          <span class="analytics__label">Короткая ссылка</span>
          <a
            :href="stats.short_url"
            target="_blank"
            rel="noopener"
            class="analytics__link mono"
          >
            {{ stats.short_url }}
          </a>
        </div>
        <div>
          <span class="analytics__label">Создана</span>
          <span class="analytics__value">{{ formatDate(stats.created_at) }}</span>
        </div>
      </div>

      <hr class="glass-divider" />

      <div class="analytics__sources">
        <span class="analytics__label">Топ источников</span>
        <div v-if="topSources.length" class="row">
          <span
            v-for="[source, count] in topSources"
            :key="source"
            class="badge badge--info"
          >
            {{ source }} · {{ count }}
          </span>
        </div>
        <span v-else class="small muted">Пока нет данных о переходах</span>
      </div>
    </GlassCard>

    <section class="analytics__clicks">
      <div class="spread">
        <div>
          <h2 class="section-title">Переходы</h2>
          <p class="section-subtitle">
            Показано {{ shownClicks }} из {{ formatNumber(stats.total_clicks) }}
            записей
          </p>
        </div>
        <span class="badge">Referer · время · устройство</span>
      </div>

      <div v-if="!shownClicks" class="empty-state glass-card glass-card--flat">
        <span class="empty-state__icon" aria-hidden="true">↗</span>
        <strong>Переходов ещё не было</strong>
        <p class="small muted">
          Откройте короткую ссылку в браузере — событие появится здесь.
        </p>
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Время</th>
              <th>Источник</th>
              <th>Referer</th>
              <th>Устройство</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(click, index) in stats.clicks" :key="index">
              <td class="mono">{{ formatDate(click.clicked_at) }}</td>
              <td>
                <span class="badge badge--info">
                  {{ click.referer_source || 'direct' }}
                </span>
              </td>
              <td :title="click.referer || ''">
                <span class="mono small">{{ shorten(click.referer) }}</span>
              </td>
              <td :title="click.user_agent || ''">
                <span class="small">{{ shorten(click.user_agent, 38) }}</span>
              </td>
              <td class="mono small">{{ click.ip_address || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.analytics {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.analytics__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 16px;
}

.analytics__meta :deep(.glass-card__body) {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 22px 24px;
}

.analytics__meta-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 18px;
}

.analytics__label {
  display: block;
  margin-bottom: 5px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.analytics__value {
  font-size: 0.92rem;
  color: var(--muted-strong);
}

.analytics__link {
  display: block;
  color: #c8bcff;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analytics__link:hover {
  text-decoration: underline;
}

.analytics__sources {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analytics__clicks {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
</style>
