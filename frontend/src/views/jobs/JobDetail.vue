<template>
  <section class="page-shell page">
    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <GlassCard>
        <el-page-header @back="router.back()">
          <template #content>
            <span>{{ job.job_name || '岗位详情' }}</span>
          </template>
        </el-page-header>
        <div class="hero-detail">
          <div>
            <h1>{{ job.job_name }}</h1>
            <p>{{ job.company }} · {{ job.location || '-' }} · {{ job.industry || job.job_category || '-' }}</p>
          </div>
          <strong>{{ job.salary_range || '薪资面议' }}</strong>
        </div>
        <div class="actions">
          <el-button type="primary" @click="router.push(`/jobs/${jobId}/profile`)">岗位画像</el-button>
          <el-button @click="router.push(`/jobs/${jobId}/similar`)">相似岗位</el-button>
          <el-button @click="router.push(`/jobs/path/${encodeURIComponent(job.job_name)}`)">职业路径</el-button>
          <el-button @click="goMatch">匹配这个岗位</el-button>
        </div>
      </GlassCard>

      <GlassCard>
        <el-tabs>
          <el-tab-pane label="岗位描述">
            <p class="rich">{{ job.job_description || job.description || '暂无岗位描述' }}</p>
          </el-tab-pane>
          <el-tab-pane label="任职要求">
            <p class="rich">{{ job.requirements || '暂无任职要求' }}</p>
          </el-tab-pane>
          <el-tab-pane label="技能标签">
            <div class="tag-list">
              <el-tag v-for="skill in listify(job.skills)" :key="skill" effect="plain">{{ skill }}</el-tag>
            </div>
          </el-tab-pane>
        </el-tabs>
      </GlassCard>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { jobsApi, userApi } from '@/api'
import { listify } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const route = useRoute()
const router = useRouter()
const jobId = route.params.jobId
const loading = ref(true)
const job = ref({})

async function goMatch() {
  await userApi.addHistory({ title: job.value.job_name, desc: '岗位详情', type: 'job', itemId: jobId }).catch(() => {})
  router.push({ path: '/match/recommend', query: { job: job.value.job_name } })
}

onMounted(async () => {
  try {
    job.value = await jobsApi.detail(jobId)
    userApi.addHistory({ title: job.value.job_name, desc: '岗位详情', type: 'job', itemId: jobId }).catch(() => {})
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.hero-detail {
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
}

h1 {
  margin: 0 0 10px;
  font-size: 34px;
  font-weight: 500;
}

p {
  margin: 0;
  color: var(--muted);
}

strong {
  color: var(--amber);
  font-size: 24px;
  white-space: nowrap;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.rich {
  white-space: pre-wrap;
  color: #4f5862;
  line-height: 1.9;
}
</style>
