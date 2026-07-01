<template>
  <section class="page-shell profile-page">
    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <div class="profile-hero">
        <div class="hero-copy">
          <el-tag effect="plain">Student Portrait</el-tag>
          <h1>{{ profile.name || '学生画像' }}</h1>
          <p>{{ portraitSummary }}</p>
          <div class="actions">
            <el-button @click="router.push('/profile/create')">重新填写</el-button>
            <el-button type="primary" @click="router.push('/match/recommend')">去匹配岗位</el-button>
          </div>
        </div>
        <div class="hero-metrics">
          <div class="metric-card">
            <strong>{{ profile.completeness || 0 }}%</strong>
            <span>画像完整度</span>
          </div>
          <div class="metric-card accent">
            <strong>{{ profile.competitiveness || 0 }}</strong>
            <span>综合竞争力</span>
          </div>
        </div>
      </div>

      <div class="insight-strip">
        <div v-for="item in insights" :key="item.label" class="insight glass-panel">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.desc }}</p>
        </div>
      </div>

      <div class="story-grid">
        <GlassCard class="radar-card">
          <h2>软能力雷达</h2>
          <RadarChart :items="softRows" title="软能力" />
        </GlassCard>
        <div class="skill-cloud glass-card">
          <h2>技能星云</h2>
          <div class="bubbles">
            <span v-for="(item, index) in profile.skills || []" :key="item" :style="{ '--i': index }">{{ item }}</span>
            <em v-if="!profile.skills?.length">还没有技能标签，先去补一份画像吧。</em>
          </div>
        </div>
      </div>

      <div class="next-steps glass-panel">
        <div>
          <span>Next Best Actions</span>
          <h2>现在最值得做的三件事</h2>
        </div>
        <button v-for="item in nextSteps" :key="item.title" type="button" @click="router.push(item.to)">
          <strong>{{ item.title }}</strong>
          <small>{{ item.desc }}</small>
        </button>
      </div>

      <div class="journey">
        <article v-for="item in journeyItems" :key="item.title" class="journey-card">
          <span>{{ item.index }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.text }}</p>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { profileApi } from '@/api'
import { formatEducation, formatExperience, softAbilityRows } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import RadarChart from '@/components/RadarChart.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const profile = ref({})
const softRows = computed(() => softAbilityRows(profile.value.soft_abilities))
const skills = computed(() => profile.value.skills || [])
const evidenceCount = computed(() => {
  const parts = [profile.value.education_text, profile.value.work_text, profile.value.project_text, profile.value.summary]
  return parts.filter((item) => String(item || '').trim()).length + skills.value.length
})
const portraitSummary = computed(() => {
  const major = profile.value.major || profile.value.education_json?.major || '专业信息待完善'
  const grade = profile.value.grade || profile.value.education_json?.grade || '阶段待完善'
  const topSkills = skills.value.slice(0, 3).join('、') || '技能待补充'
  return `${major} · ${grade} · 当前可展示能力：${topSkills}`
})
const insights = computed(() => [
  {
    label: '可投递方向',
    value: inferDirection(),
    desc: '基于专业、技能和项目线索推断，可在人岗匹配中继续细化。',
  },
  {
    label: '作品证据',
    value: `${Math.min(evidenceCount.value, 12)} 项`,
    desc: '技能、项目、实习和总结会共同影响匹配与报告质量。',
  },
  {
    label: '画像状态',
    value: `${profile.value.completeness || 0}%`,
    desc: completenessHint(),
  },
])
const nextSteps = computed(() => [
  { title: '匹配真实岗位', desc: '用当前画像找出最接近的岗位和差距', to: '/match/recommend' },
  { title: '生成规划报告', desc: '把方向、阶段计划和作品清单整理成报告', to: `/report/generate?student_id=${route.params.studentId}` },
  { title: '问 AI 助手', desc: '继续追问简历表达、项目选择或面试准备', to: '/assistant/chat' },
])
const journeyItems = computed(() => [
  {
    index: '01',
    title: '教育线索',
    text: profile.value.education_text || formatEducation(profile.value.education_json, '待补充教育经历'),
  },
  {
    index: '02',
    title: '实践证据',
    text: profile.value.work_text || formatExperience(profile.value.work_json, '待补充实习/工作经历'),
  },
  {
    index: '03',
    title: '项目作品',
    text: profile.value.project_text || formatExperience(profile.value.project_json, '待补充项目经历'),
  },
  {
    index: '04',
    title: '技能与亮点',
    text: profile.value.skills_certs_text || (skills.value || []).join('、') || '待补充技能、工具和作品亮点',
  },
])

function inferDirection() {
  const text = `${profile.value.major || ''} ${skills.value.join(' ')} ${profile.value.project_text || ''}`
  if (/数据|SQL|Python|Pandas|ECharts|分析/i.test(text)) return '数据分析 / BI'
  if (/Vue|React|前端|JavaScript/i.test(text)) return '前端开发'
  if (/Java|Flask|后端|Docker/i.test(text)) return '后端开发'
  if (/产品|用户|PRD|原型/i.test(text)) return '产品助理'
  return '探索型画像'
}

function completenessHint() {
  const score = Number(profile.value.completeness || 0)
  if (score >= 75) return '已经可以进入匹配与报告生成。'
  if (score >= 45) return '建议补充项目结果和实习细节。'
  return '建议先上传简历或补充项目经历。'
}

onMounted(async () => {
  try {
    profile.value = await profileApi.detail(route.params.studentId)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.profile-page {
  padding: 26px 0 60px;
  display: grid;
  gap: 20px;
}

.profile-hero {
  min-height: 330px;
  border-radius: 34px;
  padding: 38px;
  display: flex;
  justify-content: space-between;
  gap: 28px;
  align-items: center;
  color: white;
  background:
    radial-gradient(circle at 88% 18%, rgba(212,163,115,.42), transparent 24%),
    linear-gradient(135deg, rgba(127,143,163,.9), rgba(165,181,178,.82), rgba(201,177,176,.78));
  box-shadow: 0 30px 78px rgba(79,88,102,.2);
}

.hero-copy h1 {
  margin: 16px 0 10px;
  font-size: clamp(42px, 7vw, 82px);
  line-height: 1;
  font-weight: 700;
}

.hero-copy p {
  color: rgba(255,255,255,.84);
  font-size: 18px;
}

.actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-metrics {
  display: grid;
  gap: 14px;
}

.metric-card {
  width: 170px;
  height: 142px;
  border-radius: 30px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.2);
  backdrop-filter: blur(16px);
  animation: lift 4s ease-in-out infinite;
}

.metric-card.accent {
  animation-delay: .7s;
}

.metric-card strong {
  font-size: 44px;
}

.metric-card span {
  margin-top: -24px;
  color: rgba(255,255,255,.82);
}

.insight-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.insight {
  padding: 18px;
  transition: transform .28s ease, background .28s ease;
}

.insight:hover {
  transform: translateY(-5px);
  background: rgba(255,255,255,.82);
}

.insight span,
.next-steps span {
  color: var(--muted);
  font-size: 13px;
}

.insight strong {
  display: block;
  margin: 8px 0;
  font-size: 26px;
}

.insight p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.story-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, .85fr);
  gap: 20px;
}

.radar-card h2,
.skill-cloud h2 {
  margin: 0 0 16px;
  font-size: 22px;
}

.skill-cloud {
  padding: 24px;
  overflow: hidden;
}

.bubbles {
  min-height: 320px;
  position: relative;
}

.bubbles span {
  display: inline-flex;
  margin: 8px;
  padding: 12px 16px;
  border-radius: 999px;
  color: white;
  background: linear-gradient(135deg, var(--mist-blue), var(--sage));
  box-shadow: 0 12px 28px rgba(79,88,102,.14);
  animation: bob 3.6s ease-in-out infinite;
  animation-delay: calc(var(--i) * .16s);
}

.bubbles em {
  color: var(--muted);
}

.next-steps {
  padding: 20px;
  display: grid;
  grid-template-columns: 1.1fr repeat(3, minmax(0, 1fr));
  gap: 14px;
  align-items: stretch;
}

.next-steps h2 {
  margin: 8px 0 0;
}

.next-steps button {
  min-height: 110px;
  border: 0;
  border-radius: 16px;
  padding: 16px;
  text-align: left;
  color: var(--ink);
  background: rgba(255,255,255,.62);
  cursor: pointer;
  transition: transform .24s ease, opacity .24s ease, box-shadow .24s ease;
}

.next-steps button:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 38px rgba(79,88,102,.12);
}

.next-steps button:active {
  opacity: .72;
  transform: translateY(-2px);
}

.next-steps strong {
  display: block;
  margin-bottom: 8px;
}

.next-steps small {
  color: var(--muted);
  line-height: 1.6;
}

.journey {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.journey-card {
  min-height: 210px;
  border-radius: 26px;
  padding: 24px;
  background: rgba(255,255,255,.58);
  box-shadow: 0 20px 54px rgba(79,88,102,.12);
  transition: transform .3s ease;
}

.journey-card:hover {
  transform: translateY(-8px);
}

.journey-card span {
  color: var(--amber);
  font-weight: 800;
}

.journey-card h3 {
  margin: 14px 0 10px;
  font-size: 21px;
}

.journey-card p {
  color: var(--muted);
  line-height: 1.8;
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 7;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes lift {
  50% { transform: translateY(-10px) rotate(1deg); }
}

@keyframes bob {
  50% { transform: translateY(-8px); }
}

@media (max-width: 860px) {
  .profile-hero,
  .story-grid,
  .insight-strip,
  .next-steps,
  .journey {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-metrics {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
