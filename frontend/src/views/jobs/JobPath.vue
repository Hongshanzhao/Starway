<template>
  <section class="page-shell path-page">
    <div class="path-hero">
      <div>
        <el-tag effect="plain">Career Route</el-tag>
        <h1>{{ currentJob }} 的成长路线</h1>
        <p>{{ data.summary || 'AI 正在把岗位拆成阶段、证据和下一步行动。' }}</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="router.push(`/jobs/search?keyword=${encodeURIComponent(currentJob)}`)">查看相关岗位</el-button>
      </div>
    </div>

    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <section class="route-lane">
        <div class="lane-head">
          <h2>纵向成长阶段</h2>
          <span>从能入门，到能独立负责，再到能带方案</span>
        </div>
        <div class="stage-grid">
          <article v-for="(item, index) in verticalStages" :key="`${item.title}-${index}`" class="stage-card">
            <div class="stage-kicker">阶段 {{ index + 1 }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
            <div class="stage-evidence">
              <section>
                <strong>交付物</strong>
                <span v-for="tag in item.outputs" :key="tag">{{ tag }}</span>
              </section>
              <section>
                <strong>检查点</strong>
                <span v-for="tag in item.checkpoints" :key="tag">{{ tag }}</span>
              </section>
            </div>
          </article>
        </div>
      </section>

      <section class="route-lane">
        <div class="lane-head">
          <h2>横向迁移方向</h2>
          <span>当你想换赛道时，优先看能力能迁移到哪里</span>
        </div>
        <div class="path-grid">
          <article v-for="item in lateralCards" :key="item.job_name || item.to_job" class="path-card">
            <div class="path-card-head">
              <div>
                <el-tag effect="plain">{{ item.relation_type === 'promotion' ? '晋升' : '迁移' }}</el-tag>
                <h3>{{ item.job_name || item.to_job }}</h3>
              </div>
              <el-progress v-if="item.match_score || item.readiness_score" type="circle" :width="68" :percentage="Math.round(item.match_score || item.readiness_score)" />
            </div>
            <p>{{ item.description || item.why_recommended }}</p>
            <div class="detail-row">
              <strong>可迁移</strong>
              <span>{{ listText(item.transferable_skills, '需要先补充学生画像后再判断') }}</span>
            </div>
            <div class="detail-row">
              <strong>缺口</strong>
              <span>{{ listText(item.missing_skills, '暂无明显缺口') }}</span>
            </div>
            <el-button text @click="router.push(`/jobs/search?keyword=${encodeURIComponent(item.job_name || item.to_job)}`)">搜索这个方向</el-button>
          </article>
          <el-empty v-if="!lateralCards.length" description="暂无横向迁移建议" />
        </div>
      </section>

      <div class="lower-grid">
        <section class="route-lane">
          <div class="lane-head">
            <h2>90 天推进路线</h2>
            <span>{{ aiLoading ? 'AI 正在生成个性化路线' : '每个阶段都要留下可展示证据' }}</span>
          </div>
          <div v-if="aiLoading && !actionPlan.length" class="ai-generating">
            <LoadingSkeleton />
          </div>
          <div v-else-if="actionPlan.length" class="plan-list">
            <article v-for="item in actionPlan" :key="item.title">
              <strong>{{ item.title }}</strong>
              <p>{{ item.text }}</p>
              <span>{{ item.output }}</span>
            </article>
          </div>
          <el-empty v-else description="AI 暂未返回推进路线，请稍后重试" />
        </section>

        <section class="route-lane">
          <div class="lane-head">
            <h2>风险检查</h2>
            <span>{{ aiLoading ? '正在结合画像识别风险' : '结合你的画像生成' }}</span>
          </div>
          <div v-if="aiLoading && !riskList.length" class="risk-loading">
            <LoadingSkeleton />
          </div>
          <div v-else-if="riskList.length" class="risk-list">
            <article v-for="item in riskList" :key="item.title">
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
              <span>{{ item.mitigation }}</span>
            </article>
          </div>
          <el-empty v-else description="AI 暂未返回风险检查，请稍后重试" />
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { jobsApi, userApi } from '@/api'
import { streamRequest } from '@/api/http'
import { currentStudentId } from '@/utils/auth'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const aiLoading = ref(false)
const aiStreamText = ref('')
const data = ref({})
const currentJob = computed(() => data.value.job_name || route.params.jobName || '目标岗位')

const verticalStages = computed(() => {
  if (data.value.vertical_stages?.length) return normalizeStages(data.value.vertical_stages)
  const raw = data.value.vertical_path || []
  const stages = raw.map((item, index) => ({
    title: `${item.from_job || currentJob.value} → ${item.to_job || `进阶阶段 ${index + 1}`}`,
    description: item.description || item.why_next || `${currentJob.value} 的进阶重点是把基础执行转化为稳定交付，并逐步承担更复杂的问题拆解。`,
    outputs: [
      '岗位能力清单',
      ...(item.transferable_skills || []).slice(0, 2),
      ...(item.learning_plan || []).slice(0, 1),
    ].filter(Boolean),
    checkpoints: normalizeTextList(item.checkpoints || item.transferable_skills || ['能说明能力迁移']),
  }))
  return normalizeStages([
    {
      title: `${currentJob.value} 入门准备`,
      description: '先看真实 JD，确认高频技能、工作任务和交付物。这个阶段的目标是能理解岗位语言，并完成一个小练习证明基础能力。',
      outputs: ['JD 拆解表', '技能优先级', '学习笔记'],
      checkpoints: ['能解释岗位产出', '能完成基础练习'],
    },
    ...stages,
    {
      title: `${currentJob.value} 独立胜任`,
      description: '把学习成果沉淀为一个完整项目或案例，能讲清需求、方案、执行、结果和复盘。到这个阶段才适合更集中地投递。',
      outputs: ['作品集', '简历条目', '面试讲稿'],
      checkpoints: ['能讲清项目过程', '能用结果证明价值'],
    },
  ])
})

const lateralCards = computed(() => data.value.lateral_cards?.length ? data.value.lateral_cards : (data.value.lateral_paths || []))

const isAiPathReady = computed(() => data.value.model_source === 'ai')
const actionPlan = computed(() => isAiPathReady.value && data.value.action_plan?.length
  ? data.value.action_plan.map((item, index) => normalizePlanItem(item, index))
  : [])

const riskList = computed(() => isAiPathReady.value && data.value.risk_list?.length
  ? data.value.risk_list.map((item, index) => normalizeRiskItem(item, index))
  : [])

function listText(value, fallback) {
  const items = normalizeTextList(value)
  return items.length ? items.slice(0, 5).join('、') : fallback
}

function normalizeStages(items) {
  return (Array.isArray(items) ? items : []).map((item, index) => ({
    title: cleanText(item?.title || item?.stage || `阶段 ${index + 1}`),
    description: cleanText(item?.description || item?.text || item?.why_next || '围绕目标岗位完成阶段能力建设。'),
    outputs: normalizeTextList(item?.outputs || item?.output || item?.deliverables).slice(0, 4),
    checkpoints: normalizeTextList(item?.checkpoints || item?.checkpoint || item?.criteria).slice(0, 4),
  })).map((item) => ({
    ...item,
    outputs: item.outputs.length ? item.outputs : ['阶段作品'],
    checkpoints: item.checkpoints.length ? item.checkpoints : ['完成复盘'],
  }))
}

function normalizeTextList(value) {
  if (Array.isArray(value)) {
    return value.flatMap((item) => normalizeTextList(item)).filter(Boolean)
  }
  if (value && typeof value === 'object') {
    return [cleanText(value.title || value.name || value.output || value.text || value.description || value.risk || value.mitigation)]
      .filter(Boolean)
  }
  const text = cleanText(value)
  if (!text) return []
  return text
    .split(/[、,，;；\n]/)
    .map((item) => cleanText(item))
    .filter((item) => item.length > 1)
}

function normalizePlanItem(item, index) {
  if (typeof item === 'string') {
    return { title: `阶段 ${index + 1}`, text: cleanText(item), output: '形成可展示成果' }
  }
  return {
    title: cleanText(item?.title || item?.stage || `阶段 ${index + 1}`),
    text: cleanText(item?.text || item?.description || item?.task || ''),
    output: cleanText(item?.output || item?.deliverable || item?.result || '形成可展示成果'),
  }
}

function normalizeRiskItem(item, index) {
  if (typeof item === 'string') {
    return { title: `风险 ${index + 1}`, description: cleanText(item), mitigation: '用阶段复盘及时调整。' }
  }
  const title = cleanText(item?.risk || item?.title || item?.name || `风险 ${index + 1}`)
  const description = cleanText(item?.description || item?.reason || item?.text || title)
  const mitigation = cleanText(item?.mitigation || item?.solution || item?.action || item?.suggestion || '把风险拆成每周可检查的行动。')
  return { title, description, mitigation }
}

function cleanText(value) {
  return String(value ?? '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/```json|```/gi, '')
    .replace(/您好/g, '你好')
    .replace(/您的/g, '你的')
    .replace(/您/g, '你')
    .trim()
}

onMounted(async () => {
  try {
    const profile = await userApi.profile().catch(() => null)
    const studentId = currentStudentId(profile)
    data.value = await jobsApi.path(route.params.jobName, studentId ? { student_id: studentId } : undefined).catch(() => ({}))
    loading.value = false
    aiLoading.value = true
    aiStreamText.value = ''
    const query = studentId ? `?student_id=${encodeURIComponent(studentId)}` : ''
    await streamRequest(`/api/jobs/${encodeURIComponent(route.params.jobName)}/full-path-ai-stream${query}`, null, (event) => {
      if (event.chunk) aiStreamText.value += event.chunk
      if (event.done && event.data) data.value = event.data
    }, { method: 'GET' }).catch(async () => {
      data.value = await jobsApi.pathAi(route.params.jobName, studentId ? { student_id: studentId } : undefined)
    })
  } finally {
    aiLoading.value = false
    loading.value = false
  }
})
</script>

<style scoped>
.path-page {
  padding: 26px 0 60px;
  display: grid;
  gap: 22px;
}

.path-hero {
  min-height: 260px;
  border-radius: 28px;
  padding: 34px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 22px;
  align-items: start;
  color: white;
  background: linear-gradient(135deg, rgba(127,143,163,.92), rgba(165,181,178,.86), rgba(201,177,176,.78));
  box-shadow: 0 30px 74px rgba(79,88,102,.2);
}

.path-hero h1 {
  max-width: 780px;
  margin: 16px 0;
  font-size: clamp(34px, 5vw, 62px);
  line-height: 1.08;
  font-weight: 700;
}

.path-hero p {
  max-width: 720px;
  color: rgba(255,255,255,.86);
  line-height: 1.8;
}

.route-lane {
  border-radius: 24px;
  padding: 24px;
  background: rgba(255,255,255,.62);
  box-shadow: 0 22px 60px rgba(79,88,102,.12);
  backdrop-filter: blur(18px);
}

.lane-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: baseline;
  margin-bottom: 18px;
}

.lane-head h2 {
  margin: 0;
  font-size: 24px;
}

.lane-head span {
  color: var(--muted);
}

.stage-grid,
.path-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.stage-card,
.path-card,
.plan-list article {
  border-radius: 18px;
  padding: 18px;
  background: rgba(255,255,255,.7);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.stage-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #68778a;
  font-size: 13px;
  font-weight: 700;
}

.stage-kicker::before {
  content: "";
  width: 30px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--mist-blue), var(--rose));
}

h3 {
  margin: 14px 0 10px;
  font-size: 20px;
}

p {
  color: var(--muted);
  line-height: 1.75;
}

.path-card-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.stage-evidence {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.stage-evidence section {
  border-radius: 14px;
  padding: 12px;
  display: grid;
  align-content: start;
  gap: 8px;
  background: rgba(127,143,163,.08);
}

.stage-evidence strong {
  color: #68778a;
  font-size: 13px;
}

.stage-evidence span {
  position: relative;
  padding-left: 14px;
  color: #59616b;
  line-height: 1.55;
}

.stage-evidence span::before {
  content: "";
  position: absolute;
  left: 0;
  top: .72em;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #a5b5b2;
}

.plan-list article span {
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(127,143,163,.12);
  color: #59616b;
  font-size: 13px;
}

.detail-row {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 10px;
  margin-top: 10px;
  color: var(--muted);
  line-height: 1.6;
}

.detail-row strong {
  color: #68778a;
}

.lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(300px, .8fr);
  gap: 18px;
}

.plan-list {
  display: grid;
  gap: 12px;
}

.plan-list strong {
  display: inline-flex;
  margin-bottom: 8px;
}

.risk-list {
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
  color: var(--muted);
}

.risk-list article {
  border-radius: 16px;
  padding: 16px;
  background: rgba(255,255,255,.7);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.risk-list strong {
  display: block;
  color: #4f5862;
  font-size: 16px;
}

.risk-list p {
  margin: 8px 0;
}

.risk-list span {
  display: block;
  border-left: 3px solid #c9b1b0;
  padding-left: 10px;
  color: #68778a;
  line-height: 1.65;
}

@media (max-width: 860px) {
  .path-hero,
  .lower-grid,
  .stage-evidence {
    grid-template-columns: 1fr;
  }

  .lane-head {
    display: block;
  }
}
</style>
