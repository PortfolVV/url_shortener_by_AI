<script setup>
defineProps({
  tag: { type: String, default: 'section' },
  flat: { type: Boolean, default: false },
  interactive: { type: Boolean, default: false },
  bodyClass: { type: String, default: '' },
})
</script>

<template>
  <component
    :is="tag"
    class="glass-card"
    :class="{
      'glass-card--flat': flat,
      'glass-card--interactive': interactive,
    }"
  >
    <div class="glass-card__body" :class="bodyClass">
      <slot />
    </div>
  </component>
</template>
