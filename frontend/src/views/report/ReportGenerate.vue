<template>
  <section class="page-shell page">
    <GlassCard class="generate-head">
      <div>
        <h1 class="section-title">生成职业报告</h1>
        <p class="muted">选择目标岗位后，系统会结合画像、人岗匹配和岗位数据实时生成一份可导出的规划报告。</p>
      </div>
      <div class="toolbar">
        <label>
          <span>画像 ID</span>
          <el-input-number v-model="studentId" :min="1" :disabled="profileLoading" />
        </label>
        <label>
          <span>岗位库</span>
          <el-select v-model="jobName" filterable remote reserve-keyword placeholder="选择岗位" :remote-method="loadNames">
          <el-option v-for="item in names" :key="item" :label="item" :value="item" />
          </el-select>
        </label>
        <label>
          <span>目标岗位</span>
          <el-input v-model="jobName" placeholder="或手动输入岗位名称" />
        </label>
        <el-button type="primary" :loading="streaming" @click="generate">流式生成</el-button>
      </div>
    </GlassCard>
    <div class="workspace">
      <GlassCard class="preview-card">
        <div class="preview-head">
          <div>
            <h2>报告正文</h2>
            <p>{{ streaming ? 'AI 正在逐段生成，内容会实时出现。' : reportId ? '报告已生成，可继续查看详情或导出。' : '生成前可先确认画像和目标岗位。' }}</p>
          </div>
          <el-tag v-if="streaming" type="success">生成中</el-tag>
          <el-tag v-else-if="reportId" type="success">已完成</el-tag>
          <el-tag v-else>待生成</el-tag>
        </div>
      <div class="report-preview" :class="{ active: content }">
          <pre>{{ content || placeholderText }}</pre>
      </div>
      <el-button v-if="reportId" type="primary" @click="router.push(`/report/${reportId}`)">查看报告详情</el-button>
      </GlassCard>
      <GlassCard class="guide-card">
        <h2>生成前检查</h2>
        <ul>
          <li>画像里应有专业、年级、技能、项目或实习经历。</li>
          <li>目标岗位越具体，报告越能给出可执行计划。</li>
          <li>生成后可进入详情页查看图表、路线和导出版本。</li>
        </ul>
      </GlassCard>
    </div>
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
const placeholderText = '这里会实时展示职业报告正文。生成前不会强行占满页面，你可以先在右侧确认画像信息是否完整。'

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

.generate-head {
  display: grid;
  gap: 18px;
}

.generate-head .muted {
  margin: 6px 0 0;
}

.toolbar {
  display: grid;
  grid-template-columns: 150px minmax(220px, 1fr) minmax(220px, 1fr) 120px;
  gap: 12px;
  align-items: end;
}

.toolbar label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}

.toolbar :deep(.el-select), .toolbar :deep(.el-input), .toolbar :deep(.el-input-number) {
  width: 100%;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 18px;
  align-items: start;
}

.preview-head {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.preview-head h2,
.guide-card h2 {
  margin: 0 0 8px;
}

.preview-head p {
  margin: 0;
  color: var(--muted);
}

.report-preview {
  min-height: 260px;
  max-height: 62vh;
  overflow: auto;
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
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.8;
  color: #4f5862;
}

.guide-card ul {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
  line-height: 1.9;
}

@media (max-width: 920px) {
  .toolbar,
  .workspace {
    grid-template-columns: 1fr;
  }
}
</style>
