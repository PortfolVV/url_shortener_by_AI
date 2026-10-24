<script setup>
import HeaderBar from '@/organisms/HeaderBar.vue'
</script>

<template>
  <div class="dashboard-template">
    <HeaderBar />
    <main class="page page--wide dashboard-template__main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.dashboard-template {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.dashboard-template__main {
  padding-top: clamp(28px, 5vw, 52px);
}
</style>
