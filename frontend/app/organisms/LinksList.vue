<script setup>
import BaseSpinner from '@/atoms/BaseSpinner.vue'
import LinkItem from '@/molecules/LinkItem.vue'

defineProps({
  links: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
})

const emit = defineEmits(['delete'])
</script>

<template>
  <section class="links-list">
    <div class="spread links-list__header">
      <div>
        <h2 class="section-title">Мои ссылки</h2>
        <p class="section-subtitle">
          {{ total ? `Всего: ${total}` : 'Здесь появятся ваши сокращённые ссылки' }}
        </p>
      </div>
      <slot name="actions" />
    </div>

    <div v-if="loading" class="links-list__loading">
      <BaseSpinner :size="32" />
      <span class="muted">Загружаем ссылки…</span>
    </div>

    <div v-else-if="!links.length" class="empty-state glass-card glass-card--flat">
      <span class="empty-state__icon" aria-hidden="true">∞</span>
      <strong>Пока пусто</strong>
      <p class="small muted">
        Сократите первую ссылку выше — она появится здесь вместе со статистикой.
      </p>
    </div>

    <div v-else class="links-list__grid">
      <LinkItem
        v-for="link in links"
        :key="link.short_code"
        :link="link"
        @delete="emit('delete', $event)"
      />
    </div>
  </section>
</template>

<style scoped>
.links-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.links-list__header {
  align-items: flex-end;
}

.links-list__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 48px;
  border-radius: var(--radius-lg);
  border: 1px dashed var(--border-soft);
}

.links-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 16px;
}
</style>
