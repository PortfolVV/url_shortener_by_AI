<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function handleExpired() {
  auth.logout()
  router.push({ name: 'login', query: { expired: '1' } })
}

onMounted(async () => {
  window.addEventListener('auth:expired', handleExpired)
  if (auth.token && !auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('auth:expired', handleExpired)
})
</script>

<template>
  <div class="app-shell">
    <div class="app-background" aria-hidden="true">
      <span class="orb orb--violet"></span>
      <span class="orb orb--cyan"></span>
      <span class="orb orb--pink"></span>
      <span class="app-background__grain"></span>
    </div>
    <RouterView v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </div>
</template>
