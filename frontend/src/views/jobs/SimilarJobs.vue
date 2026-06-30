<template>
  <section class="page-shell page">
    <GlassCard>
      <el-page-header @back="router.back()">
        <template #content>相似岗位</template>
      </el-page-header>
      <div class="toolbar topbar">
        <el-switch v-model="includeSameTitle" active-text="包含同名岗位" @change="load" />
      </div>
    </GlassCard>
    <LoadingSkeleton v-if="loading" />
    <div v-else class="job-grid">
      <JobCard v-for="job in jobs" :key="job.job_id" :job="{ ...job, id: job.job_id }" @open="openJob" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { jobsApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'
import JobCard from '@/components/JobCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const includeSameTitle = ref(false)
const jobs = ref([])

async function load() {
  loading.value = true
  try {
    const data = await jobsApi.similar(route.params.jobId, { top_k: 12, include_same_title: includeSameTitle.value })
    jobs.value = data.data || []
  } finally {
    loading.value = false
  }
}

function openJob(job) {
  router.push(`/jobs/${job.job_id || job.id}`)
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.topbar {
  margin-top: 18px;
}

.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}
</style>
