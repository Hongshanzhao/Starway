<template>
  <section class="page-shell page">
    <GlassCard>
      <h1 class="section-title">流式匹配分析</h1>
      <p class="muted">目标岗位：{{ jobName }} · 学生画像：{{ studentId || '读取中' }}</p>
      <el-button type="primary" :loading="streaming" @click="run">重新分析</el-button>
    </GlassCard>
    <div class="grid">
      <GlassCard class="score-panel">
        <h2>综合得分</h2>
        <div class="score-ring">
          <el-progress type="dashboard" :percentage="Math.round(base.overall_score || 0)" :width="150" />
          <p>{{ scoreSummary }}</p>
        </div>
        <div class="metric-list">
          <div v-for="item in scoreItems" :key="item.label" class="metric-row">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <el-progress :percentage="Number(item.value) || 0" :stroke-width="8" :show-text="false" />
          </div>
        </div>
        <div class="insight-box">
          <h3>优先处理</h3>
          <article v-for="item in priorityItems" :key="item.title">
            <strong>{{ item.title }}</strong>
            <p>{{ item.text }}</p>
          </article>
        </div>
        <div class="skill-snapshot">
          <span>已匹配技能</span>
          <div class="tag-list">
            <el-tag v-for="item in matchedSkills" :key="item" size="small" type="success">{{ item }}</el-tag>
            <p v-if="!matchedSkills.length" class="muted">暂无明显匹配技能</p>
          </div>
          <span>缺口技能</span>
          <div class="tag-list">
            <el-tag v-for="item in missingSkills" :key="item" size="small" type="warning">{{ item }}</el-tag>
            <p v-if="!missingSkills.length" class="muted">暂无明显缺口</p>
          </div>
        </div>
      </GlassCard>
      <GlassCard>
        <h2>差距建议</h2>
        <article v-if="aiDraft" class="ai-card ai-live">
          <span>AI 实时分析</span>
          <p>{{ aiDraft }}</p>
        </article>
        <div class="ai-sections">
          <article v-for="(item, index) in gaps" :key="index" class="ai-card">
            <span>{{ labelOf(item.field) }}</span>
            <p>{{ item.text }}</p>
          </article>
        </div>
        <el-empty v-if="!gaps.length && !aiDraft" description="等待流式分析" />
      </GlassCard>
    </div>
    <GlassCard v-if="done">
      <el-result icon="success" title="分析完成" sub-title="匹配结果已写入后端历史">
        <template #extra>
          <el-button type="primary" @click="router.push({ path: '/report/generate', query: { student_id: studentId, job_name: jobName } })">生成生涯规划报告</el-button>
        </template>
      </el-result>
    </GlassCard>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { matchApi, userApi } from '@/api'
import { streamRequest } from '@/api/http'
import { currentStudentId } from '@/utils/auth'
import GlassCard from '@/components/GlassCard.vue'

const route = useRoute()
const router = useRouter()
const studentId = ref(route.query.student_id ? Number(route.query.student_id) : null)
const jobName = String(route.query.job_name || '')
const historyId = route.query.history_id
const streaming = ref(false)
const done = ref(false)
const base = ref({})
const gaps = ref([])
const aiDraft = ref('')
const scoreItems = computed(() => [
  { label: '技能匹配', value: base.value.skill_fit ?? 0 },
  { label: '方向匹配', value: base.value.direction_fit ?? 0 },
  { label: '学历基础', value: base.value.education_score ?? 0 },
  { label: '经历基础', value: base.value.experience_score ?? 0 },
])
const scoreSummary = computed(() => {
  const score = Number(base.value.overall_score || 0)
  if (!score) return '等待分析结果'
  if (score >= 75) return '匹配度较高，重点把优势写成作品和简历证据。'
  if (score >= 55) return '具备部分基础，需要补齐关键技能和岗位表达。'
  return '当前差距较明显，建议先按 30/60/90 天拆解训练计划。'
})
const matchedSkills = computed(() => base.value.debug_info?.matched_skills || [])
const missingSkills = computed(() => base.value.debug_info?.missing_skills || [])
const priorityItems = computed(() => {
  const items = []
  if (Number(base.value.skill_fit || 0) < 60) {
    items.push({ title: '先补技能证据', text: `优先补 ${missingSkills.value.slice(0, 3).join('、') || '岗位高频技能'}，每项配一个小作品。` })
  }
  if (Number(base.value.direction_fit || 0) < 50) {
    items.push({ title: '确认岗位方向', text: '当前目标和画像方向跨度较大，建议优先选择专业、技能或项目经历能迁移的相邻岗位。' })
  }
  if (Number(base.value.experience_score || 0) < 70) {
    items.push({ title: '补经历表达', text: '把课程项目、社团任务或练习项目改写成岗位语言，写清动作和结果。' })
  }
  return items.slice(0, 3)
})

const labels = {
  base: '基础判断',
  skills: '技能补齐',
  quality: '职业素养',
  potential: '成长节奏',
  recommended_resources: '资源与作品',
}

async function run() {
  const id = await ensureStudentId()
  if (!id || !jobName) {
    ElMessage.warning('缺少 student_id 或 job_name')
    return
  }
  streaming.value = true
  done.value = false
  base.value = {}
  gaps.value = []
  aiDraft.value = ''
  try {
    await streamRequest('/api/match/match-stream', { student_id: id, job_name: jobName }, (event) => {
      if (event.type === 'base') base.value = event.data || {}
      if (event.type === 'gap') gaps.value.push({ field: event.field, text: event.text })
      if (event.type === 'gap_stream') aiDraft.value += event.text || ''
      if (event.type === 'done') done.value = true
    })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    streaming.value = false
  }
}

async function ensureStudentId() {
  if (studentId.value) return studentId.value
  const profile = await userApi.profile().catch(() => null)
  studentId.value = currentStudentId(profile)
  if (!studentId.value) {
    ElMessage.warning('还没有学生画像，请先完善画像')
    router.push('/profile/create')
    return null
  }
  return studentId.value
}

async function loadHistoryOrRun() {
  const id = await ensureStudentId()
  if (!id) return
  if (historyId && id) {
    const data = await matchApi.history(id).catch(() => null)
    const row = data?.history?.find((item) => String(item.id) === String(historyId))
    if (row?.details) {
      try {
        const detail = JSON.parse(row.details)
        base.value = detail
        gaps.value = Object.entries(detail.gap_analysis || {}).map(([field, text]) => ({ field, text }))
        aiDraft.value = ''
        done.value = true
        return
      } catch {
        // Fall through to a fresh stream if stored details are malformed.
      }
    }
  }
  run()
}

onMounted(loadHistoryOrRun)

function labelOf(field) {
  return labels[field] || field
}
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.grid {
  display: grid;
  grid-template-columns: minmax(300px, .7fr) minmax(0, 1.3fr);
  gap: 18px;
}

h2 {
  margin: 0 0 18px;
  font-weight: 500;
}

.score-panel {
  align-self: start;
}

.score-ring {
  display: grid;
  justify-items: center;
  gap: 12px;
}

.score-ring p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
  text-align: center;
}

.metric-list {
  margin-top: 20px;
  display: grid;
  gap: 14px;
}

.insight-box,
.skill-snapshot {
  margin-top: 18px;
  display: grid;
  gap: 10px;
}

.insight-box h3 {
  margin: 0;
  font-size: 17px;
}

.insight-box article,
.skill-snapshot {
  border-radius: 16px;
  padding: 14px;
  background: rgba(255,255,255,.58);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.insight-box strong,
.skill-snapshot span {
  color: #68778a;
  font-weight: 700;
}

.insight-box p {
  margin: 6px 0 0;
  color: var(--muted);
  line-height: 1.65;
}

.skill-snapshot .tag-list {
  margin: 8px 0 12px;
}

.metric-row {
  display: grid;
  grid-template-columns: 88px 46px 1fr;
  gap: 10px;
  align-items: center;
}

.metric-row span {
  color: #59616b;
}

.metric-row strong {
  font-weight: 600;
}

.ai-sections {
  display: grid;
  gap: 14px;
}

.ai-card {
  border-radius: 20px;
  padding: 18px;
  background: rgba(255,255,255,.58);
  box-shadow: 0 12px 30px rgba(79,88,102,.08);
  animation: reveal .35s ease both;
}

.ai-card span {
  display: inline-flex;
  margin-bottom: 8px;
  color: var(--amber);
  font-weight: 700;
}

.ai-live {
  margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(255,255,255,.76), rgba(165,181,178,.18));
}

.ai-card p {
  margin: 0;
  color: #4f5862;
  line-height: 1.85;
  white-space: pre-wrap;
}

@keyframes reveal {
  from { opacity: 0; transform: translateY(14px); }
}

@media (max-width: 860px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
