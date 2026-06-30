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
            <div class="mini-tags">
              <span v-for="tag in item.outputs" :key="tag">{{ tag }}</span>
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
            <span>每个阶段都要留下可展示证据</span>
          </div>
          <div class="plan-list">
            <article v-for="item in actionPlan" :key="item.title">
              <strong>{{ item.title }}</strong>
              <p>{{ item.text }}</p>
              <span>{{ item.output }}</span>
            </article>
          </div>
        </section>

        <section class="route-lane">
          <div class="lane-head">
            <h2>风险检查</h2>
            <span>避免只学习、不产出、不复盘</span>
          </div>
          <ul class="risk-list">
            <li v-for="item in riskList" :key="item">{{ item }}</li>
          </ul>
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
const data = ref({})
const currentJob = computed(() => data.value.job_name || route.params.jobName || '目标岗位')

const verticalStages = computed(() => {
  if (data.value.vertical_stages?.length) return data.value.vertical_stages
  const raw = data.value.vertical_path || []
  const stages = raw.map((item, index) => ({
    title: `${item.from_job || currentJob.value} → ${item.to_job || `进阶阶段 ${index + 1}`}`,
    description: item.description || item.why_next || `${currentJob.value} 的进阶重点是把基础执行转化为稳定交付，并逐步承担更复杂的问题拆解。`,
      outputs: [
      '岗位能力清单',
      ...(item.transferable_skills || []).slice(0, 2),
      ...(item.learning_plan || []).slice(0, 1),
    ].filter(Boolean),
  }))
  return [
    {
      title: `${currentJob.value} 入门准备`,
      description: '先看真实 JD，确认高频技能、工作任务和交付物。这个阶段的目标是能理解岗位语言，并完成一个小练习证明基础能力。',
      outputs: ['JD 拆解表', '技能优先级', '学习笔记'],
    },
    ...stages,
    {
      title: `${currentJob.value} 独立胜任`,
      description: '把学习成果沉淀为一个完整项目或案例，能讲清需求、方案、执行、结果和复盘。到这个阶段才适合更集中地投递。',
      outputs: ['作品集', '简历条目', '面试讲稿'],
    },
  ]
})

const lateralCards = computed(() => data.value.lateral_cards?.length ? data.value.lateral_cards : (data.value.lateral_paths || []))

const actionPlan = computed(() => data.value.action_plan?.length ? data.value.action_plan : [
  {
    title: '0-30 天：拆岗位',
    text: `收集 20 条 ${currentJob.value} JD，标出共同技能、职责、工具和产出物。选择 2 个最高频缺口开始补齐。`,
    output: '产出：岗位能力清单 + 个人差距清单',
  },
  {
    title: '31-60 天：做作品',
    text: `围绕 ${currentJob.value} 做一个小项目或案例，不求大而全，但要完整展示从问题到结果的过程。`,
    output: '产出：作品链接/文档 + 150 字简历描述',
  },
  {
    title: '61-90 天：投递复盘',
    text: '开始小批量投递，每周复盘回复率、面试问题和技能卡点。根据反馈微调简历关键词和项目讲述。',
    output: '产出：投递记录表 + 面试题复盘',
  },
])

const riskList = computed(() => data.value.risk_list?.length ? data.value.risk_list : [
  '只收藏课程但没有作品：每学一个技能都要配一个可展示输出。',
  '简历只写“熟悉/了解”：改成“用什么方法，在什么场景，解决什么问题”。',
  '横向迁移跨度过大：优先选择技能、行业或工作方式至少有一项相邻的方向。',
  '投递后不复盘：每周至少记录一次反馈，判断是关键词、项目深度还是表达问题。',
])

function listText(value, fallback) {
  return Array.isArray(value) && value.length ? value.slice(0, 5).join('、') : fallback
}

onMounted(async () => {
  try {
    const profile = await userApi.profile().catch(() => null)
    const studentId = currentStudentId(profile)
    data.value = await jobsApi.path(route.params.jobName, studentId ? { student_id: studentId } : undefined).catch(() => ({}))
    loading.value = false
    aiLoading.value = true
    const query = studentId ? `?student_id=${encodeURIComponent(studentId)}` : ''
    await streamRequest(`/api/jobs/${encodeURIComponent(route.params.jobName)}/full-path-ai-stream${query}`, null, (event) => {
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

.mini-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.mini-tags span,
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
  padding-left: 20px;
  color: var(--muted);
  line-height: 1.9;
}

@media (max-width: 860px) {
  .path-hero,
  .lower-grid {
    grid-template-columns: 1fr;
  }

  .lane-head {
    display: block;
  }
}
</style>
