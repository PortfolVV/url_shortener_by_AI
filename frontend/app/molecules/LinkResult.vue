<script setup>
import { computed, ref } from 'vue'

import BaseBadge from '@/atoms/BaseBadge.vue'
import BaseButton from '@/atoms/BaseButton.vue'
import GlassCard from '@/atoms/GlassCard.vue'
import { copyToClipboard } from '@/utils/clipboard'
import { formatDate } from '@/utils/format'

const props = defineProps({
  link: { type: Object, required: true },
})

const copied = ref(false)
const copyFailed = ref(false)

const expiryLabel = computed(() => {
  if (!props.link.expires_at) return 'Бессрочная ссылка'
  return `До ${formatDate(props.link.expires_at)}`
})

async function copy() {
  const ok = await copyToClipboard(props.link.short_url)
  copied.value = ok
  copyFailed.value = !ok
  if (ok) {
    setTimeout(() => {
      copied.value = false
    }, 2200)
  }
}
</script>

<template>
  <GlassCard flat class="link-result fade-in">
    <div class="link-result__header">
      <div class="row">
        <BaseBadge tone="success">Готово</BaseBadge>
        <BaseBadge v-if="link.reused" tone="info">
          Уже существовала
        </BaseBadge>
        <BaseBadge v-else-if="!link.is_authenticated" tone="neutral">
          Анонимная
        </BaseBadge>
      </div>
      <span class="small muted">{{ expiryLabel }}</span>
    </div>

    <p v-if="link.reused" class="link-result__notice">
      Эта ссылка уже сокращалась ранее — возвращаем существующий код.
    </p>

    <div class="link-result__main">
      <div class="link-result__content">
        <div class="link-result__short">
          <a
            :href="link.short_url"
            target="_blank"
            rel="noopener"
            class="link-result__url mono"
          >
            {{ link.short_url }}
          </a>
          <BaseButton size="sm" variant="ghost" @click="copy">
            {{ copied ? 'Скопировано' : 'Копировать' }}
          </BaseButton>
        </div>

        <p class="link-result__original" :title="link.original_url">
          {{ link.original_url }}
        </p>

        <div class="link-result__actions">
          <a
            :href="link.short_url"
            target="_blank"
            rel="noopener"
            class="btn btn--ghost btn--sm"
          >
            Открыть
          </a>
          <a
            :href="`/api/v1/links/${link.short_code}/qr`"
            target="_blank"
            rel="noopener"
            class="btn btn--ghost btn--sm"
          >
            QR отдельно
          </a>
        </div>
      </div>

      <figure v-if="link.qr_code" class="link-result__qr">
        <img :src="link.qr_code" :alt="`QR-код для ${link.short_url}`" />
        <figcaption class="small muted">Наведите камеру</figcaption>
      </figure>
    </div>

    <p v-if="copyFailed" class="small link-result__copy-error">
      Не удалось скопировать автоматически — выделите ссылку вручную.
    </p>
  </GlassCard>
</template>

<style scoped>
.link-result {
  margin-top: 22px;
}

.link-result__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.link-result__notice {
  margin: 14px 0 0;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(53, 214, 255, 0.08);
  border: 1px solid rgba(53, 214, 255, 0.22);
  color: #bdefff;
  font-size: 0.88rem;
}

.link-result__main {
  display: flex;
  gap: 26px;
  align-items: center;
  margin-top: 18px;
}

.link-result__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.link-result__short {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.link-result__url {
  font-size: clamp(1rem, 2.4vw, 1.35rem);
  font-weight: 600;
  color: #c8bcff;
  overflow-wrap: anywhere;
}

.link-result__url:hover {
  color: #e4dcff;
  text-decoration: underline;
}

.link-result__original {
  margin: 0;
  color: var(--muted);
  font-size: 0.86rem;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow-wrap: anywhere;
}

.link-result__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.link-result__qr {
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 16px 30px rgba(2, 6, 20, 0.35);
}

.link-result__qr img {
  width: 148px;
  height: 148px;
}

.link-result__qr figcaption {
  color: #4b526b;
  font-size: 0.72rem;
}

.link-result__copy-error {
  margin: 12px 0 0;
  color: var(--warning);
}

@media (max-width: 640px) {
  .link-result__main {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .link-result__qr {
    align-self: center;
  }
}
</style>
