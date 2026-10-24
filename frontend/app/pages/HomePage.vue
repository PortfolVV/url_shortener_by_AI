<script setup>
import GlassCard from '@/atoms/GlassCard.vue'
import ShortenerPanel from '@/organisms/ShortenerPanel.vue'
import DefaultTemplate from '@/templates/DefaultTemplate.vue'

const features = [
  {
    title: 'QR-код сразу',
    text: 'Каждая ссылка возвращается вместе с SVG QR-кодом, который можно скачать или показать с экрана.',
  },
  {
    title: 'Аналитика переходов',
    text: 'Время клика, количество переходов и Referer — для ссылок авторизованных пользователей в PostgreSQL.',
  },
  {
    title: 'TTL на выбор',
    text: 'Задайте срок жизни от часа до года или сделайте ссылку бессрочной. Анонимные живут 7 дней.',
  },
]
</script>

<template>
  <DefaultTemplate>
    <section class="hero">
      <span class="hero__eyebrow">
        <span class="hero__pulse" aria-hidden="true" />
        Glassmorphism URL shortener
      </span>
      <h1 class="hero__title">
        Короткие ссылки<br />
        <span class="gradient-text">с характером</span>
      </h1>
      <p class="hero__lead">
        Сократите ссылку за секунду, получите QR-код и следите за переходами.
        Без регистрации — на 7 дней, с аккаунтом — навсегда.
      </p>
      <div class="hero__chips">
        <span class="badge badge--info">Redis · анонимные</span>
        <span class="badge badge--success">PostgreSQL · аккаунт</span>
        <span class="badge">Nginx · 2 реплики</span>
      </div>
    </section>

    <ShortenerPanel class="home__panel" />

    <section class="features">
      <GlassCard
        v-for="feature in features"
        :key="feature.title"
        flat
        interactive
        class="feature-card"
      >
        <h3 class="feature-card__title">{{ feature.title }}</h3>
        <p class="feature-card__text">{{ feature.text }}</p>
      </GlassCard>
    </section>
  </DefaultTemplate>
</template>

<style scoped>
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  text-align: center;
  margin: 10px 0 clamp(28px, 5vw, 46px);
}

.hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(14px);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted-strong);
}

.hero__pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 0 5px rgba(63, 227, 165, 0.16);
}

.hero__title {
  margin: 0;
  font-size: clamp(2.6rem, 6.5vw, 4.6rem);
  line-height: 1.02;
  letter-spacing: -0.045em;
  font-weight: 750;
}

.hero__lead {
  max-width: 640px;
  margin: 0;
  color: var(--muted);
  font-size: clamp(1rem, 1.6vw, 1.12rem);
}

.hero__chips {
  display: flex;
  gap: 9px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 4px;
}

.home__panel {
  max-width: 900px;
  margin: 0 auto;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-top: clamp(32px, 5vw, 56px);
}

.feature-card__title {
  margin: 0 0 8px;
  font-size: 1.03rem;
  font-weight: 650;
}

.feature-card__text {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
}
</style>
