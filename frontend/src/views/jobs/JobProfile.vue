<template>
  <section class="page-shell page">
    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <div class="profile-hero">
        <el-page-header @back="router.back()">
          <template #content>{{ profile.job_name }} 岗位画像</template>
        </el-page-header>
        <div class="hero-body">
          <div>
            <el-tag effect="plain">{{ profile.category || '职业方向' }}</el-tag>
            <h1>{{ profile.job_name }}</h1>
            <p>{{ aiProfile.summary || roleSummary }}</p>
          </div>
          <div class="hero-metrics">
            <div>
              <strong>{{ skills.length }}</strong>
              <span>核心技能</span>
            </div>
            <div>
              <strong>{{ evidenceList.length || 0 }}</strong>
              <span>作品证据</span>
            </div>
            <div>
              <strong>{{ softRows.length }}</strong>
              <span>软能力</span>
            </div>
          </div>
        </div>
      </div>

      <div class="content-grid">
        <GlassCard class="main-card">
          <div class="card-head">
            <h2>岗位能力拆解</h2>
            <el-button text @click="router.push(`/jobs/${encodeURIComponent(profile.job_name)}/path`)">看成长路径</el-button>
          </div>
          <div class="skill-columns">
            <section v-for="group in skillGroups" :key="group.title" class="skill-group">
              <span>{{ group.title }}</span>
              <p>{{ group.desc || group.reason }}</p>
              <div class="tag-list">
                <el-tag v-for="skill in group.items" :key="skill" :type="group.type">{{ skill }}</el-tag>
                <span v-if="!group.items.length" class="muted">暂无明确数据</span>
              </div>
            </section>
          </div>
        </GlassCard>

        <GlassCard class="side-card">
          <h2>准备优先级</h2>
          <ol class="check-list">
            <li v-for="item in preparationList" :key="item">{{ item }}</li>
          </ol>
        </GlassCard>
      </div>

      <div class="content-grid">
        <GlassCard class="chart-card">
          <h2>软能力要求</h2>
          <RadarChart :items="softRows" title="岗位软能力" />
          <div class="soft-list">
            <article v-for="item in softRows" :key="item.name">
              <strong>{{ item.name }}</strong>
              <el-progress :percentage="Math.round(Number(item.score || 0) * 20)" :stroke-width="8" />
              <p>{{ item.description || softAbilityText(item.name) }}</p>
            </article>
          </div>
        </GlassCard>

        <GlassCard>
          <h2>作品与面试证据</h2>
          <div class="evidence-list">
            <article v-for="item in evidenceList" :key="item.title">
              <span>{{ item.title }}</span>
              <p>{{ item.text }}</p>
            </article>
          </div>
        </GlassCard>
      </div>
      <GlassCard>
        <h2>AI 工作场景与面试问题</h2>
        <div class="ai-grid">
          <article>
            <span>真实工作场景</span>
            <ul>
              <li v-for="item in aiProfile.work_scenarios || []" :key="item">{{ item }}</li>
            </ul>
          </article>
          <article>
            <span>面试追问</span>
            <ul>
              <li v-for="item in aiProfile.interview_questions || []" :key="item">{{ item }}</li>
            </ul>
          </article>
          <article>
            <span>常见误区</span>
            <ul>
              <li v-for="item in aiProfile.risk_tips || []" :key="item">{{ item }}</li>
            </ul>
          </article>
        </div>
      </GlassCard>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { jobsApi } from '@/api'
import { streamRequest } from '@/api/http'
import { listify, softAbilityRows } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import RadarChart from '@/components/RadarChart.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const aiLoading = ref(false)
const profile = ref({})
const aiProfile = ref({})

const skills = computed(() => listify(profile.value.skills))
const softRows = computed(() => softAbilityRows(profile.value.soft_abilities))
const jobName = computed(() => profile.value.job_name || '目标岗位')

const roleSummary = computed(() => {
  const name = jobName.value
  if (hasAny(['测试', 'QA', '质量'])) return `${name}关注需求理解、风险识别、用例设计、缺陷定位和质量复盘。用户真正需要看到的是你能不能把问题测出来、讲清楚、推动修复。`
  if (hasAny(['前端', 'Vue', 'React', 'Web'])) return `${name}需要把需求转成稳定、清晰、可维护的页面体验。除了会写页面，还要能处理接口联调、组件复用、响应式布局和异常状态。`
  if (hasAny(['后端', 'Java', 'Python', '开发'])) return `${name}重点在接口、数据、性能、安全和部署。准备时要证明你能独立设计一条业务链路，并能解释关键技术取舍。`
  if (hasAny(['数据', '分析', '算法'])) return `${name}需要把业务问题变成数据问题，再用清洗、统计、建模或可视化产出可解释结论。`
  if (hasAny(['产品', '需求'])) return `${name}需要理解用户场景、拆解需求优先级、输出清晰方案，并推动研发、测试和运营协作。`
  return `${name}不是一个抽象名称，而是一组真实任务。准备时要围绕技能、项目证据、沟通协作和岗位产出四条线建立可信材料。`
})

const skillGroups = computed(() => {
  if (aiProfile.value.skill_groups?.length) {
    return aiProfile.value.skill_groups.map((group, index) => ({
      title: group.title,
      desc: group.reason,
      items: group.skills || [],
      type: ['', 'success', 'warning'][index] || '',
    }))
  }
  const primary = skills.value.slice(0, 6)
  const advanced = skills.value.slice(6, 12)
  return [
    {
      title: '入门必须会',
      desc: '先补齐能看懂 JD、能完成基础任务的技能。',
      items: primary,
      type: '',
    },
    {
      title: '作品加分项',
      desc: '用这些能力把课程或项目做成可展示成果。',
      items: advanced,
      type: 'success',
    },
    {
      title: '项目证明点',
      desc: '把技能放到真实问题里，形成简历和面试可验证证据。',
      items: primary.slice(0, 3),
      type: 'warning',
    },
  ]
})

const preparationList = computed(() => aiProfile.value.preparation_steps?.length ? aiProfile.value.preparation_steps : [
  `收集 15 条 ${jobName.value} JD，统计重复出现的技能和职责。`,
  `从核心技能中选择 2 到 3 项，做一个能展示岗位产出的项目。`,
  '把项目写成“问题、方案、工具、结果、复盘”的结构，而不是只列技术名词。',
  '准备 5 个面试故事：一次问题定位、一次协作推进、一次失败复盘、一次学习突破、一次结果验证。',
])

const evidenceList = computed(() => aiProfile.value.evidence?.length ? aiProfile.value.evidence : [
  {
    title: '简历证据',
    text: `至少准备 3 条和 ${jobName.value} 直接相关的经历，每条写清动作、工具和结果。例如“设计/实现/分析/测试了什么，解决了什么问题”。`,
  },
  {
    title: '作品证据',
    text: '技术岗位优先准备代码仓库、接口文档、测试记录或部署地址；非技术岗位优先准备调研报告、方案文档、数据复盘或流程模板。',
  },
  {
    title: '面试证据',
    text: `围绕 ${jobName.value} 准备一段 3 分钟项目讲述稿，重点讲你的判断、取舍和结果，而不是从头背流程。`,
  },
])

function hasAny(words) {
  const text = `${jobName.value} ${skills.value.join(' ')}`.toLowerCase()
  return words.some((word) => text.includes(String(word).toLowerCase()))
}

function softAbilityText(name) {
  const map = {
    沟通: '能把问题、风险和进展讲清楚，是协作型岗位的基础能力。',
    协作: '能和产品、研发、测试、运营等角色对齐目标并推进落地。',
    学习: '能快速补齐新工具和新业务背景，适合岗位变化较快的环境。',
    分析: '能拆解问题、找到证据，并用结果支持判断。',
    执行: '能把计划拆成任务并稳定交付，避免只停留在想法层面。',
  }
  return map[name] || '建议用项目复盘、周报和面试案例证明这项能力，而不是只写性格描述。'
}

onMounted(async () => {
  try {
    profile.value = await jobsApi.profile(route.params.jobId)
    loading.value = false
    aiLoading.value = true
    await streamRequest(`/api/jobs/${route.params.jobId}/profile-ai-stream`, null, (event) => {
      if (event.done && event.data) aiProfile.value = event.data
    }, { method: 'GET' }).catch(async () => {
      aiProfile.value = await jobsApi.profileAi(route.params.jobId).catch(() => ({}))
    })
  } finally {
    aiLoading.value = false
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

.profile-hero {
  border-radius: 28px;
  padding: 26px;
  background: linear-gradient(135deg, rgba(255,255,255,.78), rgba(165,181,178,.24));
  box-shadow: 0 22px 58px rgba(79,88,102,.12);
  backdrop-filter: blur(18px);
}

.hero-body {
  margin-top: 24px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 26px;
  align-items: end;
}

.hero-body h1 {
  margin: 14px 0;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.08;
}

.hero-body p {
  max-width: 760px;
  color: var(--muted);
  line-height: 1.8;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, 96px);
  gap: 12px;
}

.hero-metrics div {
  min-height: 86px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.hero-metrics strong {
  font-size: 28px;
  color: #4f5862;
}

.hero-metrics span {
  color: var(--muted);
  font-size: 13px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, .65fr);
  gap: 18px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

h2 {
  margin: 0 0 16px;
  font-size: 21px;
  font-weight: 600;
}

.skill-columns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.skill-group,
.evidence-list article,
.soft-list article {
  border-radius: 16px;
  padding: 16px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.skill-group span,
.evidence-list span {
  display: inline-flex;
  margin-bottom: 8px;
  color: #68778a;
  font-weight: 700;
}

.skill-group p,
.evidence-list p,
.soft-list p {
  margin: 0 0 12px;
  color: var(--muted);
  line-height: 1.7;
}

.check-list {
  margin: 0;
  padding-left: 20px;
  color: var(--muted);
  line-height: 1.9;
}

.soft-list,
.evidence-list,
.ai-grid {
  display: grid;
  gap: 12px;
}

.soft-list {
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}

.ai-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.ai-grid article {
  border-radius: 16px;
  padding: 16px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.ai-grid span {
  display: inline-flex;
  margin-bottom: 8px;
  color: #68778a;
  font-weight: 700;
}

.ai-grid ul {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
  line-height: 1.8;
}

.soft-list strong {
  display: inline-flex;
  margin-bottom: 8px;
}

@media (max-width: 980px) {
  .hero-body,
  .content-grid,
  .skill-columns,
  .ai-grid {
    grid-template-columns: 1fr;
  }

  .hero-metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
