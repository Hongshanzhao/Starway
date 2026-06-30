<template>
  <section class="page-shell page">
    <GlassCard class="match-head">
      <div class="head-copy">
        <h1 class="section-title">人岗匹配</h1>
        <p class="muted">用最新学生画像推荐岗位，再选择一个目标岗位生成完整差距分析。</p>
      </div>
      <div class="toolbar">
        <label>
          <span>画像 ID</span>
          <el-input-number v-model="studentId" :min="1" :disabled="profileLoading" />
        </label>
        <label class="job-input">
          <span>目标岗位</span>
          <el-input v-model="manualJob" placeholder="可输入岗位，或从下方卡片选择" />
        </label>
        <el-button type="primary" :loading="loading || profileLoading" @click="load">刷新推荐</el-button>
      </div>
    </GlassCard>
    <LoadingSkeleton v-if="loading" />
    <div v-else class="job-grid">
      <JobCard
        v-for="job in jobs"
        :key="job.job_name"
        :job="job"
        :selected="selectedJob === job.job_name"
        @open="selectJob"
      />
    </div>
    <div class="fixed-bar glass-panel">
      <span>已选：{{ selectedJob || manualJob || '尚未选择' }}</span>
      <el-button type="primary" :disabled="!(selectedJob || manualJob)" @click="startStream">开始匹配</el-button>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { matchApi, userApi } from '@/api'
import { currentStudentId } from '@/utils/auth'
import GlassCard from '@/components/GlassCard.vue'
import JobCard from '@/components/JobCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const profileLoading = ref(false)
const studentId = ref(route.query.student_id ? Number(route.query.student_id) : null)
const jobs = ref([])
const selectedJob = ref(route.query.job || '')
const manualJob = ref(route.query.job || '')

async function ensureStudentId() {
  if (studentId.value) return studentId.value
  profileLoading.value = true
  try {
    const profile = await userApi.profile()
    studentId.value = currentStudentId(profile)
  } finally {
    profileLoading.value = false
  }
  if (!studentId.value) {
    ElMessage.warning('还没有学生画像，请先完善画像')
    router.push('/profile/create')
    return null
  }
  return studentId.value
}

async function load() {
  const id = await ensureStudentId()
  if (!id) return
  loading.value = true
  try {
    const data = await matchApi.recommend({ student_id: id, limit: 10 })
    jobs.value = data.results || []
  } finally {
    loading.value = false
  }
}

function selectJob(job) {
  selectedJob.value = job.job_name
  manualJob.value = job.job_name
}

function startStream() {
  if (!studentId.value) {
    ElMessage.warning('请先选择学生画像')
    return
  }
  router.push({ path: '/match/stream', query: { student_id: studentId.value, job_name: selectedJob.value || manualJob.value } })
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 26px 0 110px;
  display: grid;
  gap: 18px;
}

.match-head {
  display: grid;
  grid-template-columns: minmax(240px, .8fr) minmax(0, 1.4fr);
  gap: 24px;
  align-items: end;
}

.head-copy p {
  margin-bottom: 0;
}

.toolbar {
  display: grid;
  grid-template-columns: 150px minmax(220px, 1fr) 120px;
  gap: 12px;
  align-items: end;
}

.toolbar label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}

.toolbar :deep(.el-input),
.toolbar :deep(.el-input-number) {
  width: 100%;
}

.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.fixed-bar {
  position: fixed;
  left: 50%;
  bottom: 22px;
  transform: translateX(-50%);
  width: min(760px, calc(100vw - 32px));
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  z-index: 20;
}

@media (max-width: 860px) {
  .match-head,
  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
