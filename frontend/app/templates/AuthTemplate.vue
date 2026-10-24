<script setup>
import HeaderBar from '@/organisms/HeaderBar.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <div class="auth-template">
    <HeaderBar />

    <main class="page auth-template__main">
      <section class="auth-side">
        <span class="badge badge--info">Личный кабинет</span>
        <h1 class="auth-side__title">
          Все ссылки<br />
          <span class="gradient-text">под контролем</span>
        </h1>
        <p class="auth-side__lead">
          Аналитика переходов, referer, QR-коды и гибкий TTL — в одном
          стеклянном интерфейсе.
        </p>

        <ul class="auth-side__list">
          <li>
            <span class="auth-side__bullet" aria-hidden="true">01</span>
            Ссылки и статистика хранятся в PostgreSQL
          </li>
          <li>
            <span class="auth-side__bullet" aria-hidden="true">02</span>
            Свой срок жизни или бессрочные ссылки
          </li>
          <li>
            <span class="auth-side__bullet" aria-hidden="true">03</span>
            QR-код для каждой ссылки
          </li>
        </ul>
      </section>

      <section class="auth-card glass-card">
        <div class="glass-card__body auth-card__body">
          <div class="auth-card__heading">
            <h2 class="section-title">{{ title }}</h2>
            <p v-if="subtitle" class="section-subtitle">{{ subtitle }}</p>
          </div>
          <slot />
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.auth-template {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.auth-template__main {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  align-items: center;
  gap: clamp(32px, 6vw, 80px);
  max-width: 1060px;
  width: 100%;
  margin: 0 auto;
  padding-top: clamp(40px, 7vw, 90px);
}

.auth-side {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 18px;
}

.auth-side__title {
  margin: 0;
  font-size: clamp(2.1rem, 4.4vw, 3.2rem);
  line-height: 1.08;
  letter-spacing: -0.035em;
  font-weight: 700;
}

.auth-side__lead {
  margin: 0;
  max-width: 430px;
  color: var(--muted);
  font-size: 1.02rem;
}

.auth-side__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 6px 0 0;
  padding: 0;
  list-style: none;
}

.auth-side__list li {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--muted-strong);
  font-size: 0.92rem;
}

.auth-side__bullet {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border-radius: 10px;
  border: 1px solid rgba(124, 92, 255, 0.35);
  background: rgba(124, 92, 255, 0.14);
  color: #cbbcff;
  font-size: 0.7rem;
  font-weight: 700;
  font-family: var(--mono);
}

.auth-card {
  width: 100%;
}

.auth-card__body {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: clamp(24px, 4vw, 36px);
}

.auth-card__heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

@media (max-width: 900px) {
  .auth-template__main {
    grid-template-columns: 1fr;
    max-width: 620px;
    padding-top: 36px;
  }

  .auth-side__list {
    display: none;
  }

  .auth-side__lead {
    display: none;
  }
}
</style>
