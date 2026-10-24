<script setup>
import { ref } from 'vue'

import BaseBadge from '@/atoms/BaseBadge.vue'
import BaseButton from '@/atoms/BaseButton.vue'
import BaseInput from '@/atoms/BaseInput.vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  isAuthenticated: { type: Boolean, default: false },
})

const emit = defineEmits(['submit'])

const url = ref('')
const ttl = ref('604800')
const localError = ref('')

const ttlOptions = [
  { value: '3600', label: '1 час' },
  { value: '86400', label: '1 день' },
  { value: '604800', label: '7 дней' },
  { value: '2592000', label: '30 дней' },
  { value: 'forever', label: 'Бессрочно' },
]

function looksLikeUrl(value) {
  if (/^https?:\/\//i.test(value)) return true
  // Allow bare domains such as "example.com/path"; the backend normalizes them.
  return /^[\w-]+(\.[\w-]+)+(\/\S*)?$/i.test(value)
}

function submit() {
  localError.value = ''
  const value = url.value.trim()

  if (!value) {
    localError.value = 'Вставьте ссылку, которую нужно сократить'
    return
  }
  if (!looksLikeUrl(value)) {
    localError.value = 'Похоже, это не ссылка. Пример: https://example.com/page'
    return
  }

  emit('submit', {
    original_url: value,
    ttl_seconds:
      props.isAuthenticated && ttl.value !== 'forever'
        ? Number(ttl.value)
        : null,
  })
}

function reset() {
  url.value = ''
  localError.value = ''
}

defineExpose({ reset })
</script>

<template>
  <form class="url-form" @submit.prevent="submit">
    <BaseInput
      v-model="url"
      label="Длинная ссылка"
      placeholder="https://example.com/very/long/path"
      autocomplete="url"
      :error="localError"
      :disabled="loading"
    />

    <div class="url-form__footer">
      <div v-if="isAuthenticated" class="url-form__ttl">
        <label class="field">
          <span class="field__label">Время жизни</span>
          <select v-model="ttl" class="select" :disabled="loading">
            <option
              v-for="option in ttlOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>
      </div>

      <div v-else class="url-form__anonymous">
        <BaseBadge tone="info">7 дней</BaseBadge>
        <span class="small muted">
          Анонимные ссылки хранятся в Redis и живут 7 дней
        </span>
      </div>

      <BaseButton type="submit" :loading="loading" class="url-form__submit">
        Сократить
      </BaseButton>
    </div>
  </form>
</template>

<style scoped>
.url-form {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.url-form__footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}

.url-form__ttl {
  flex: 1 1 210px;
  max-width: 240px;
}

.url-form__anonymous {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1 1 260px;
}

.url-form__submit {
  flex: 0 0 auto;
  min-width: 170px;
}

@media (max-width: 620px) {
  .url-form__submit {
    width: 100%;
  }

  .url-form__ttl {
    max-width: none;
  }
}
</style>
