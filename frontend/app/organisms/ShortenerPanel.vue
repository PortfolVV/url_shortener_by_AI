<script setup>
import { ref } from 'vue'

import GlassCard from '@/atoms/GlassCard.vue'
import LinkResult from '@/molecules/LinkResult.vue'
import UrlForm from '@/molecules/UrlForm.vue'
import api, { getApiErrorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

defineProps({
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['created'])

const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function shorten(payload) {
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const { data } = await api.post('/links', payload)
    result.value = data
    emit('created', data)
  } catch (requestError) {
    error.value = getApiErrorMessage(requestError)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <GlassCard class="shortener" :class="{ 'shortener--compact': compact }">
    <div class="shortener__heading">
      <div>
        <h2 class="section-title">
          {{ auth.isAuthenticated ? 'Новая короткая ссылка' : 'Сократить ссылку' }}
        </h2>
        <p class="section-subtitle">
          {{
            auth.isAuthenticated
              ? 'Выберите срок жизни или сделайте ссылку бессрочной.'
              : 'Без регистрации. Ссылка сразу с QR-кодом.'
          }}
        </p>
      </div>
      <span v-if="auth.isAuthenticated" class="badge badge--success">Pro</span>
    </div>

    <UrlForm
      :loading="loading"
      :is-authenticated="auth.isAuthenticated"
      @submit="shorten"
    />

    <div v-if="error" class="alert alert--error shortener__alert" role="alert">
      <span class="alert__icon" aria-hidden="true">!</span>
      <span>{{ error }}</span>
    </div>

    <LinkResult v-if="result" :link="result" />
  </GlassCard>
</template>

<style scoped>
.shortener :deep(.glass-card__body) {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: clamp(22px, 4vw, 38px);
}

.shortener__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.shortener__alert {
  margin-top: -6px;
}

.shortener--compact :deep(.glass-card__body) {
  padding: 24px;
}
</style>
