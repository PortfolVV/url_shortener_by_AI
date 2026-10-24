<script setup>
import GlassCard from '@/atoms/GlassCard.vue'
import DefaultTemplate from '@/templates/DefaultTemplate.vue'
</script>

<template>
  <DefaultTemplate>
    <GlassCard class="not-found">
      <p class="not-found__code gradient-text mono">404</p>
      <h1 class="section-title">Страница не найдена</h1>
      <p class="section-subtitle">
        Возможно, ссылка истекла или адрес введён с ошибкой.
      </p>
      <RouterLink :to="{ name: 'home' }" class="btn btn--primary">
        На главную
      </RouterLink>
    </GlassCard>
  </DefaultTemplate>
</template>

<style scoped>
.not-found :deep(.glass-card__body) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: clamp(40px, 8vw, 80px) 24px;
  text-align: center;
}

.not-found {
  max-width: 560px;
  margin: 40px auto;
}

.not-found__code {
  margin: 0;
  font-size: clamp(3.4rem, 10vw, 5.5rem);
  font-weight: 800;
  letter-spacing: -0.05em;
}

.not-found .btn {
  margin-top: 10px;
}
</style>
