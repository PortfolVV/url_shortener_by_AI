<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseBadge from '@/atoms/BaseBadge.vue'
import BaseButton from '@/atoms/BaseButton.vue'
import { copyToClipboard } from '@/utils/clipboard'
import { formatDate, formatNumber } from '@/utils/format'

const props = defineProps({
  link: { type: Object, required: true },
})

const emit = defineEmits(['delete'])

const router = useRouter()
const copied = ref(false)

const expired = computed(() => {
  if (!props.link.expires_at) return false
  return new Date(props.link.expires_at).getTime() <= Date.now()
})

async function copy() {
  if (await copyToClipboard(props.link.short_url)) {
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}
</script>

<template>
  <article class="link-item">
    <div class="link-item__top">
      <a
        :href="link.short_url"
        target="_blank"
        rel="noopener"
        class="link-item__code mono"
      >
        /l/{{ link.short_code }}
      </a>

      <BaseBadge v-if="expired" tone="warning">Истекла</BaseBadge>
      <BaseBadge v-else-if="!link.expires_at" tone="success">Бессрочная</BaseBadge>
      <BaseBadge v-else tone="neutral">{{ formatDate(link.expires_at) }}</BaseBadge>
    </div>

    <p class="link-item__original" :title="link.original_url">
      {{ link.original_url }}
    </p>

    <div class="link-item__meta">
      <span class="link-item__clicks">
        <strong>{{ formatNumber(link.clicks_count) }}</strong>
        <span class="muted small">переходов</span>
      </span>
      <span class="muted small">создана {{ formatDate(link.created_at) }}</span>
    </div>

    <div class="link-item__actions">
      <BaseButton size="sm" variant="ghost" @click="copy">
        {{ copied ? 'Скопировано' : 'Копировать' }}
      </BaseButton>
      <BaseButton
        size="sm"
        variant="ghost"
        @click="router.push({ name: 'stats', params: { code: link.short_code } })"
      >
        Аналитика
      </BaseButton>
      <BaseButton size="sm" variant="danger" @click="emit('delete', link)">
        Удалить
      </BaseButton>
    </div>
  </article>
</template>

<style scoped>
.link-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-soft);
  background: linear-gradient(
    150deg,
    rgba(255, 255, 255, 0.075),
    rgba(255, 255, 255, 0.025)
  );
  backdrop-filter: blur(16px);
  transition:
    border-color 0.22s ease,
    transform 0.22s ease;
}

.link-item:hover {
  border-color: rgba(160, 140, 255, 0.35);
  transform: translateY(-2px);
}

.link-item__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.link-item__code {
  font-size: 1.08rem;
  font-weight: 650;
  color: #c8bcff;
}

.link-item__code:hover {
  text-decoration: underline;
}

.link-item__original {
  margin: 0;
  color: var(--muted);
  font-size: 0.86rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-item__meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.link-item__clicks {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.link-item__clicks strong {
  font-size: 1.25rem;
  color: var(--text);
}

.link-item__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
