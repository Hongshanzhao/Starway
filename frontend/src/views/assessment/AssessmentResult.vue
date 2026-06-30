<template>
  <section class="page-shell page">
    <div class="result-hero">
      <div>
        <el-tag effect="plain">Result Unlocked</el-tag>
        <h1>你的兴趣能量图已生成</h1>
        <p>把最高维度当成线索，不是限制。真正适合你的方向，往往来自兴趣、能力、机会和行动的交叉点。</p>
      </div>
      <div class="top-dim">{{ topDimension }}</div>
    </div>
    <div class="grid">
      <GlassCard class="chart-card">
        <div class="card-head">
          <h2>维度雷达</h2>
          <span>{{ profileSummary }}</span>
        </div>
        <RadarChart :items="chartItems" title="兴趣维度" />
        <div class="dimension-list">
          <article v-for="item in dimensionCards" :key="item.name">
            <div class="dimension-head">
              <strong>{{ item.name }}</strong>
              <span>{{ item.score }} / 5</span>
            </div>
            <el-progress :percentage="Math.round(Number(item.score || 0) * 20)" :stroke-width="8" />
            <p>{{ item.text }}</p>
          </article>
        </div>
        <div class="evidence-box">
          <h3>下一步验证</h3>
          <p>{{ evidenceAdvice }}</p>
        </div>
      </GlassCard>
      <GlassCard>
        <h2>职业建议</h2>
        <div class="recommendation-blocks">
          <article v-for="item in recommendationBlocks" :key="item.title" class="advice-card">
            <span>{{ item.title }}</span>
            <p>{{ item.text }}</p>
          </article>
        </div>
        <div class="actions">
          <el-button type="primary" @click="router.push('/jobs/search')">去探索岗位</el-button>
          <el-button @click="router.push('/assistant/chat')">问问 AI 助手</el-button>
        </div>
      </GlassCard>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assessmentApi } from '@/api'
import { authState } from '@/utils/auth'
import GlassCard from '@/components/GlassCard.vue'
import RadarChart from '@/components/RadarChart.vue'

const route = useRoute()
const router = useRouter()
const result = ref({})
const chartItems = computed(() => Object.entries(result.value.dimension_scores || {}).map(([name, score]) => ({ name, score })))
const topDimension = computed(() => {
  const items = chartItems.value
  if (!items.length) return '探索中'
  return [...items].sort((a, b) => b.score - a.score)[0].name
})
const topItems = computed(() => [...chartItems.value].sort((a, b) => b.score - a.score))
const dimensionCards = computed(() => topItems.value.slice(0, 4).map((item) => ({
  ...item,
  text: dimensionText(item.name),
})))
const profileSummary = computed(() => {
  const first = topItems.value[0]?.name || '探索'
  const second = topItems.value[1]?.name || '补充'
  return `${first} + ${second} 倾向`
})
const evidenceAdvice = computed(() => {
  const first = topItems.value[0]?.name || '高分维度'
  return `选择一个和 ${first} 相关的小任务，在 7 天内做出可展示结果：一份调研、一段代码、一个原型、一次访谈或一张数据表。兴趣只有被行动验证后，才会变成可靠方向。`
})
const recommendationBlocks = computed(() => {
  const primary = topItems.value[0]?.name || '探索'
  const secondary = topItems.value[1]?.name || '补充'
  const base = result.value.recommendation || '本次测评已经形成兴趣画像，可以把高分维度当成接下来探索岗位和项目的线索。'
  return [
    {
      title: '结果解读',
      text: `${base}\n\n当前最高维度是 ${primary}，第二线索是 ${secondary}。建议不要把它理解成唯一答案，而是作为筛选岗位、课程和项目的优先级。`,
    },
    {
      title: '适合先看的方向',
      text: directionAdvice(primary, secondary),
    },
    {
      title: '30 天行动',
      text: '1. 选择 3 个相关岗位 JD，标出共同技能和任务。\n2. 把已有课程、项目、社团或实习经历改写成岗位语言。\n3. 做一个小作品或一次深度调研，用结果验证兴趣是否真的适合长期投入。',
    },
  ]
})

function directionAdvice(primary, secondary) {
  const map = {
    R: '现实型偏好动手实践和明确流程，可优先看测试、运维、硬件、工程实施、质量管理等方向。',
    I: '研究型偏好分析和探索，可优先看数据分析、算法助理、测试开发、科研助理、用户研究等方向。',
    A: '艺术型偏好表达和创造，可优先看视觉设计、内容策划、交互设计、品牌运营、产品体验等方向。',
    S: '社会型偏好沟通和帮助他人，可优先看教育培训、HR、用户运营、客户成功、咨询助理等方向。',
    E: '企业型偏好推动和影响，可优先看产品经理、项目管理、销售运营、商业分析、创业实践等方向。',
    C: '常规型偏好秩序和细节，可优先看财务、人力资源、行政、数据录入、流程管理、质量审核等方向。',
  }
  return `${map[primary] || '建议先从你高分维度对应的岗位开始看真实 JD。'}\n\n如果 ${secondary} 也较高，可以把两个维度组合起来筛选岗位，例如“分析 + 表达”“实践 + 秩序”“沟通 + 推动”。`
}

function dimensionText(name) {
  const map = {
    R: '现实型代表你更容易被动手、工具、流程和可见结果吸引。验证时优先选择能实际操作的任务。',
    I: '研究型代表你对分析、推理和探索未知更敏感。验证时优先选择数据、问题拆解或调研型任务。',
    A: '艺术型代表你重视表达、审美和创造空间。验证时可以尝试内容、设计、交互或品牌表达任务。',
    S: '社会型代表你在沟通、帮助、陪伴和服务中更容易获得动力。验证时选择需要真实用户反馈的任务。',
    E: '企业型代表你对推动、影响、组织资源和结果达成更感兴趣。验证时选择项目推进、销售运营或商业分析任务。',
    C: '常规型代表你偏好秩序、细节、规则和稳定交付。验证时选择流程整理、质量审核、财务/数据记录类任务。',
  }
  return map[name] || '这个维度可以作为探索线索，建议用真实岗位任务验证，而不是只看名称判断适不适合。'
}

onMounted(async () => {
  const cached = sessionStorage.getItem(`assessment_result_${route.params.resultId}`)
  if (cached) {
    result.value = JSON.parse(cached)
    return
  }
  const history = await assessmentApi.history(authState.user?.id)
  result.value = history.find((item) => String(item.id) === String(route.params.resultId)) || history[0] || {}
})
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.result-hero {
  min-height: 280px;
  border-radius: 30px;
  padding: 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 28px;
  color: white;
  background: linear-gradient(135deg, rgba(165,181,178,.9), rgba(127,143,163,.84), rgba(201,177,176,.74));
  box-shadow: 0 28px 70px rgba(79,88,102,.18);
}

.result-hero h1 {
  margin: 16px 0;
  font-size: clamp(36px, 5vw, 64px);
  line-height: 1.08;
}

.result-hero p {
  max-width: 620px;
  margin: 0;
  color: rgba(255,255,255,.86);
  line-height: 1.8;
}

.top-dim {
  width: 150px;
  height: 150px;
  border-radius: 46px;
  display: grid;
  place-items: center;
  font-size: 42px;
  font-weight: 700;
  background: rgba(255,255,255,.22);
  backdrop-filter: blur(14px);
  animation: pulse 3s ease-in-out infinite;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

h2 {
  margin: 0 0 16px;
  font-weight: 500;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.card-head span {
  color: var(--muted);
}

.dimension-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.dimension-list article,
.evidence-box {
  border-radius: 16px;
  padding: 14px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.dimension-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.dimension-head strong {
  color: #4f5862;
}

.dimension-head span {
  color: var(--muted);
  font-size: 13px;
}

.dimension-list p,
.evidence-box p {
  margin: 10px 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.evidence-box {
  margin-top: 14px;
}

.evidence-box h3 {
  margin: 0;
  font-size: 17px;
}

.recommendation-blocks {
  display: grid;
  gap: 14px;
}

.advice-card {
  padding: 16px;
  border-radius: 16px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.advice-card span {
  display: inline-flex;
  margin-bottom: 8px;
  color: var(--amber);
  font-weight: 700;
}

.advice-card p {
  margin: 0;
  white-space: pre-wrap;
  color: var(--muted);
  line-height: 1.9;
}

.actions {
  margin-top: 22px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@keyframes pulse {
  50% { transform: translateY(-8px) rotate(2deg); }
}

@media (max-width: 820px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .dimension-list {
    grid-template-columns: 1fr;
  }
}
</style>
