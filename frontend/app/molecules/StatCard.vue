<script setup>
import GlassCard from '@/atoms/GlassCard.vue'

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: '' },
  accent: { type: String, default: 'violet' },
})
</script>

<template>
  <GlassCard flat class="stat-card" :class="`stat-card--${accent}`">
    <span class="stat-card__label">{{ label }}</span>
    <strong class="stat-card__value">{{ value }}</strong>
    <span v-if="hint" class="stat-card__hint">{{ hint }}</span>
  </GlassCard>
</template>

<style scoped>
.stat-card :deep(.glass-card__body) {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 20px 22px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: '';
  position: absolute;
  top: -40px;
  right: -40px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 92, 255, 0.35), transparent 70%);
  filter: blur(12px);
}

.stat-card--cyan::after {
  background: radial-gradient(circle, rgba(53, 214, 255, 0.32), transparent 70%);
}

.stat-card--pink::after {
  background: radial-gradient(circle, rgba(255, 110, 199, 0.3), transparent 70%);
}

.stat-card--green::after {
  background: radial-gradient(circle, rgba(63, 227, 165, 0.3), transparent 70%);
}

.stat-card__label {
  font-size: 0.74rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.stat-card__value {
  font-size: clamp(1.7rem, 3vw, 2.2rem);
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.stat-card__hint {
  font-size: 0.8rem;
  color: var(--muted);
}
</style>
