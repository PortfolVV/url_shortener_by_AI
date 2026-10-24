<script setup>
import { useRouter } from 'vue-router'

import BaseButton from '@/atoms/BaseButton.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <header class="site-header">
    <div class="site-header__inner">
      <RouterLink to="/" class="brand">
        <span class="brand__mark" aria-hidden="true">S</span>
        <span class="brand__text">Shortly</span>
      </RouterLink>

      <nav class="site-nav" aria-label="Основная навигация">
        <RouterLink to="/" class="site-nav__link">Главная</RouterLink>

        <template v-if="auth.isAuthenticated">
          <RouterLink :to="{ name: 'dashboard' }" class="site-nav__link">
            Мои ссылки
          </RouterLink>
          <span class="site-nav__email small">{{ auth.user?.email }}</span>
          <BaseButton size="sm" variant="ghost" @click="logout">
            Выйти
          </BaseButton>
        </template>

        <template v-else>
          <RouterLink :to="{ name: 'login' }" class="site-nav__link">
            Войти
          </RouterLink>
          <BaseButton size="sm" @click="router.push({ name: 'register' })">
            Создать аккаунт
          </BaseButton>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(7, 11, 24, 0.55);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
}

.site-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  width: 100%;
  max-width: 1160px;
  min-height: var(--header-height);
  margin: 0 auto;
  padding: 10px 24px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  font-weight: 700;
  font-size: 1.12rem;
  letter-spacing: -0.01em;
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.35), transparent 60%),
    linear-gradient(135deg, #7c5cff, #35d6ff);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 8px 22px rgba(124, 92, 255, 0.4);
  font-weight: 800;
}

.site-nav {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.site-nav__link {
  color: var(--muted);
  font-size: 0.92rem;
  transition: color 0.2s ease;
}

.site-nav__link:hover,
.site-nav__link.router-link-active {
  color: var(--text);
}

.site-nav__email {
  color: var(--muted);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 720px) {
  .site-header__inner {
    padding: 10px 16px;
    gap: 10px;
  }

  .site-nav {
    gap: 10px;
  }

  .site-nav__link {
    display: none;
  }

  .site-nav__email {
    display: none;
  }
}
</style>
