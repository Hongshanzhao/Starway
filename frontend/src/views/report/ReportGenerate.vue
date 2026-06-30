<template>
  <section class="page-shell page">
    <GlassCard>
      <h1 class="section-title">生成职业报告</h1>
      <div class="toolbar">
        <el-input-number v-model="studentId" :min="1" :disabled="profileLoading" />
        <el-select v-model="jobName" filterable remote reserve-keyword placeholder="选择岗位" :remote-method="loadNames">
          <el-option v-for="item in names" :key="item" :label="item" :value="item" />
        </el-select>
        <el-input v-model="jobName" placeholder="或手动输入岗位名称" />
        <el-button type="primary" :loading="streaming" @click="generate">流式生成</el-button>
      </div>
    </GlassCard>
    <GlassCard>
      <div class="report-preview" :class="{ active: content }">
        <pre>{{ content || '报告内容将在这里实时出现。' }}</pre>
      </div>
      <el-button v-if="reportId" type="primary" @click="router.push(`/report/${reportId}`)">查看报告详情</el-button>
    </GlassCard>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { jobsApi, userApi } from '@/api'
import { streamRequest } from '@/api/http'
import { currentStudentId } from '@/utils/auth'
import GlassCard from '@/components/GlassCard.vue'

const route = useRoute()
const router = useRouter()
const studentId = ref(route.query.student_id ? Number(route.query.student_id) : null)
const jobName = ref(route.query.job_name || '')
const names = ref([])
const streaming = ref(false)
const profileLoading = ref(false)
const content = ref('')
const reportId = ref(null)

async function loadNames(keyword = '') {
  const data = await jobsApi.names().catch(() => [])
  names.value = data.filter((item) => !keyword || item.includes(keyword)).slice(0, 80)
}

async function generate() {
  const id = await ensureStudentId()
  if (!id || !jobName.value) {
    ElMessage.warning('请选择学生画像和岗位')
    return
  }
  streaming.value = true
  content.value = ''
  reportId.value = null
  try {
    await streamRequest('/api/report/generate-stream?ai=1', { student_id: id, job_name: jobName.value }, (event) => {
      if (event.chunk) content.value += event.chunk
      if (event.done) reportId.value = event.report_id
    })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    streaming.value = false
  }
}

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

onMounted(loadNames)
onMounted(ensureStudentId)
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.toolbar :deep(.el-select), .toolbar :deep(.el-input) {
  width: 260px;
}

.report-preview {
  min-height: 420px;
  border-radius: 24px;
  padding: 22px;
  background:
    linear-gradient(135deg, rgba(255,255,255,.7), rgba(165,181,178,.16));
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.14);
  transition: transform .3s ease;
}

.report-preview.active {
  transform: translateY(-2px);
}

pre {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #4f5862;
}
</style>
