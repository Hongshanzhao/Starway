<template>
  <div class="glass-card skeleton-card">
    <el-skeleton :rows="rows" animated />
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Number, default: 5 },
})
</script>

<style scoped>
.skeleton-card {
  padding: 22px;
}
</style>
