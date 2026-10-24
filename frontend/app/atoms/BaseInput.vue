<script setup>
import { useId } from 'vue'

defineProps({
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: 'off' },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const model = defineModel({ type: String, default: '' })
const inputId = useId()
</script>

<template>
  <label class="field" :for="inputId">
    <span v-if="label" class="field__label">{{ label }}</span>
    <input
      :id="inputId"
      v-model="model"
      class="input"
      :class="{ 'input--error': error }"
      :type="type"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :required="required"
      :disabled="disabled"
    />
    <span v-if="error" class="field__error">{{ error }}</span>
    <span v-else-if="hint" class="field__hint">{{ hint }}</span>
  </label>
</template>
