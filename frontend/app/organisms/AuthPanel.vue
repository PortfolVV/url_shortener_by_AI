<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AuthForm from '@/molecules/AuthForm.vue'
import { getApiErrorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  mode: { type: String, default: 'login' },
})

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const error = ref('')

function getRedirectTarget() {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/')) {
    return redirect
  }
  return { name: 'dashboard' }
}

async function submit(credentials) {
  error.value = ''
  try {
    if (props.mode === 'register') {
      await auth.register(credentials)
    } else {
      await auth.login(credentials)
    }
    router.push(getRedirectTarget())
  } catch (requestError) {
    error.value = getApiErrorMessage(requestError)
  }
}
</script>

<template>
  <div class="auth-panel">
    <div v-if="route.query.expired" class="alert alert--info" role="status">
      Сессия истекла — войдите снова.
    </div>

    <AuthForm :mode="mode" :loading="auth.loading" @submit="submit" />

    <div v-if="error" class="alert alert--error" role="alert">
      <span class="alert__icon" aria-hidden="true">!</span>
      <span>{{ error }}</span>
    </div>

    <p class="auth-panel__switch small">
      <template v-if="mode === 'login'">
        Нет аккаунта?
        <RouterLink :to="{ name: 'register' }">Зарегистрируйтесь</RouterLink>
      </template>
      <template v-else>
        Уже есть аккаунт?
        <RouterLink :to="{ name: 'login' }">Войти</RouterLink>
      </template>
    </p>
  </div>
</template>

<style scoped>
.auth-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.auth-panel__switch {
  margin: 4px 0 0;
  text-align: center;
  color: var(--muted);
}

.auth-panel__switch a {
  color: var(--primary-soft);
  font-weight: 600;
}

.auth-panel__switch a:hover {
  text-decoration: underline;
}
</style>
