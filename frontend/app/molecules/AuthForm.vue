<script setup>
import { ref } from 'vue'

import BaseButton from '@/atoms/BaseButton.vue'
import BaseInput from '@/atoms/BaseInput.vue'

const props = defineProps({
  mode: { type: String, default: 'login' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['submit'])

const email = ref('')
const password = ref('')
const errors = ref({ email: '', password: '' })

const isRegister = props.mode === 'register'

function validate() {
  errors.value = { email: '', password: '' }

  if (!email.value.trim()) {
    errors.value.email = 'Введите email'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    errors.value.email = 'Некорректный email'
  }

  if (!password.value) {
    errors.value.password = 'Введите пароль'
  } else if (isRegister && password.value.length < 8) {
    errors.value.password = 'Минимум 8 символов'
  }

  return !errors.value.email && !errors.value.password
}

function submit() {
  if (!validate()) return
  emit('submit', {
    email: email.value.trim(),
    password: password.value,
  })
}
</script>

<template>
  <form class="auth-form" @submit.prevent="submit">
    <BaseInput
      v-model="email"
      label="Email"
      type="email"
      placeholder="you@example.com"
      autocomplete="email"
      :error="errors.email"
      :disabled="loading"
    />
    <BaseInput
      v-model="password"
      label="Пароль"
      type="password"
      :placeholder="isRegister ? 'Минимум 8 символов' : 'Ваш пароль'"
      :autocomplete="isRegister ? 'new-password' : 'current-password'"
      :error="errors.password"
      :disabled="loading"
    />
    <slot name="hint" />
    <BaseButton type="submit" block :loading="loading">
      {{ isRegister ? 'Создать аккаунт' : 'Войти' }}
    </BaseButton>
  </form>
</template>

<style scoped>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
</style>
