<script setup>
defineProps({
  size: { type: Number, default: 28 },
  label: { type: String, default: 'Загрузка' },
})
</script>

<template>
  <span
    class="spinner"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="status"
    :aria-label="label"
  />
</template>

<style scoped>
.spinner {
  display: inline-block;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.16);
  border-top-color: #9d86ff;
  border-right-color: #35d6ff;
  animation: rotate 0.85s linear infinite;
}

@keyframes rotate {
  to {
    transform: rotate(360deg);
  }
}
</style>
