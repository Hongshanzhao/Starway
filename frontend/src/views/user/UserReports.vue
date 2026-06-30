<template>
  <section class="page">
    <GlassCard>
      <h1 class="section-title">{{ title }}</h1>
    </GlassCard>
    <LoadingSkeleton v-if="loading" />
    <div v-else class="report-grid">
        <ReportCard v-for="item in reports" :key="item.id" :report="item" @open="open" />
      <el-empty v-if="!reports.length" description="暂无报告" />
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import ReportCard from '@/components/ReportCard.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const reports = ref([])
const studentId = ref(null)
const kind = computed(() => route.meta.reportKind || 'plans')
const title = computed(() => ({ plans: '我的职业规划报告', interests: '我的兴趣测评报告', matches: '我的匹配报告' }[kind.value]))

async function load() {
  loading.value = true
  try {
    if (kind.value === 'plans') reports.value = await userApi.plans()
    if (kind.value === 'interests') reports.value = await userApi.interests()
    if (kind.value === 'matches') reports.value = await userApi.matches()
    const profile = await userApi.profile().catch(() => null)
    studentId.value = profile?.student_id || null
  } finally {
    loading.value = false
  }
}

function open(item) {
  if (kind.value === 'plans' && item.id) router.push(`/report/${item.id}`)
  if (kind.value === 'interests' && item.id) router.push(`/assessment/result/${item.id}`)
  if (kind.value === 'matches' && item.id) {
    router.push({ path: '/match/stream', query: { student_id: studentId.value || '', job_name: item.targetJob || item.job_name || '', history_id: item.id } })
  }
}

onMounted(load)
watch(kind, load)
</script>

<style scoped>
.page {
  display: grid;
  gap: 18px;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}
</style>
