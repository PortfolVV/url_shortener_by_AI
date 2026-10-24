<script setup>
import AuthPanel from '@/organisms/AuthPanel.vue'
import AuthTemplate from '@/templates/AuthTemplate.vue'
</script>

<template>
  <AuthTemplate
    title="Создать аккаунт"
    subtitle="Сохраняйте ссылки в PostgreSQL и получайте аналитику переходов."
  >
    <AuthPanel mode="register" />
  </AuthTemplate>
</template>
