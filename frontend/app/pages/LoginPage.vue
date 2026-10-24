<script setup>
import AuthPanel from '@/organisms/AuthPanel.vue'
import AuthTemplate from '@/templates/AuthTemplate.vue'
</script>

<template>
  <AuthTemplate
    title="С возвращением"
    subtitle="Войдите, чтобы управлять ссылками и смотреть статистику."
  >
    <AuthPanel mode="login" />
  </AuthTemplate>
</template>
