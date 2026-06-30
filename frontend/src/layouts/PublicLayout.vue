<template>
  <div class="layout">
    <AppNavbar />
    <main>
      <RouterView />
    </main>
    <BackButton v-if="$route.path !== '/'" />
    <AppFooter />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'
import BackButton from '@/components/BackButton.vue'
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

main {
  min-height: calc(100vh - 180px);
}
</style>
