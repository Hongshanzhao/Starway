<template>
  <section class="glass-card card" :class="{ interactive }">
    <slot />
  </section>
</template>

<script setup>
defineProps({
  interactive: Boolean,
})
</script>

<style scoped>
.card {
  padding: 22px;
  transition: transform 0.35s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.35s;
}

.interactive:hover {
  transform: translateY(-4px);
  box-shadow: 0 26px 56px rgba(79, 88, 102, 0.16);
}
</style>
