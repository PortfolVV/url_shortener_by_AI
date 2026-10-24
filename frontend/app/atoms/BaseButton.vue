<script setup>
defineProps({
  variant: { type: String, default: 'primary' },
  type: { type: String, default: 'button' },
  size: { type: String, default: 'md' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
})
</script>

<template>
  <button
    :type="type"
    class="btn"
    :class="[
      `btn--${variant}`,
      { 'btn--block': block, 'btn--sm': size === 'sm' },
    ]"
    :disabled="disabled || loading"
  >
    <span v-if="loading" class="btn__spinner" aria-hidden="true" />
    <span v-else-if="$slots.icon" class="btn__icon"><slot name="icon" /></span>
    <span><slot /></span>
  </button>
</template>

<style scoped>
.btn__icon {
  display: inline-flex;
  width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
}
</style>
