<script setup>
import HeaderBar from '@/organisms/HeaderBar.vue'
</script>

<template>
  <div class="template">
    <HeaderBar />
    <main class="page">
      <slot />
    </main>
    <footer class="site-footer">
      <div class="site-footer__inner">
        <span>Shortly · FastAPI + Vue 3</span>
        <span class="site-footer__dot" aria-hidden="true">✦</span>
        <span>Glassmorphism UI · QR · Analytics</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.template {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.site-footer {
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(7, 11, 24, 0.4);
  backdrop-filter: blur(14px);
}

.site-footer__inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  max-width: 1160px;
  margin: 0 auto;
  padding: 22px 24px;
  color: var(--muted);
  font-size: 0.82rem;
}

.site-footer__dot {
  color: var(--primary-soft);
}
</style>
