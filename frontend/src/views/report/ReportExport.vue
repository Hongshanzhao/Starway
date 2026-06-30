<template>
  <section class="page-shell page">
    <GlassCard>
      <h1 class="section-title">导出中心</h1>
      <p class="muted">当前后端提供 Markdown Blob 导出。打开报告详情后可直接导出。</p>
      <el-button type="primary" @click="router.push('/user/plans')">查看我的报告</el-button>
    </GlassCard>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import GlassCard from '@/components/GlassCard.vue'

const router = useRouter()
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
}
</style>
