<template>
  <div class="home">
    <section class="hero">
      <div class="sky-depth" aria-hidden="true">
        <span class="glow glow-a"></span>
        <span class="glow glow-b"></span>
        <span class="glass-ribbon ribbon-a"></span>
        <span class="glass-ribbon ribbon-b"></span>
        <span v-for="n in 24" :key="`bird-${n}`" class="bird"></span>
        <span v-for="n in 12" :key="`leaf-${n}`" class="leaf"></span>
      </div>
      <div class="page-shell hero-inner">
        <div class="hero-copy">
          <el-tag effect="plain">Starway Career Intelligence</el-tag>
          <h1 class="page-title">在职业的星河里，找到自己的航线</h1>
          <p>Starway 读取真实岗位、学生画像与兴趣测评，让 AI 把模糊的憧憬整理成可抵达的路径：看见方向，也看见下一步该留下些什么证据。</p>
          <div class="hero-actions">
            <el-button type="primary" size="large" :icon="Sparkles" @click="router.push('/profile/create')">
              开始规划
            </el-button>
            <el-button size="large" :icon="Search" @click="router.push('/jobs/search')">
              探索岗位
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="page-shell quick-grid">
      <GlassCard v-for="item in quick" :key="item.to" interactive class="quick" @click="router.push(item.to)">
        <component :is="item.icon" :size="28" />
        <h3>{{ item.title }}</h3>
        <p>{{ item.desc }}</p>
      </GlassCard>
    </section>

    <section class="page-shell hot-section">
      <div class="section-head">
        <h2 class="section-title">热门岗位</h2>
        <el-button text @click="router.push('/jobs/search')">查看全部</el-button>
      </div>
      <LoadingSkeleton v-if="loading" />
      <div v-else class="job-grid">
        <JobCard v-for="job in jobs" :key="job.id" :job="job" @open="openJob" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bot, Compass, Search, Sparkles, Target } from 'lucide-vue-next'
import { jobsApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'
import JobCard from '@/components/JobCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const router = useRouter()
const loading = ref(true)
const jobs = ref([])
const quick = [
  { title: '兴趣测评', desc: '用霍兰德六维看见你天然靠近的工作方式。', to: '/assessment', icon: Compass },
  { title: '岗位星图', desc: '从真实岗位数据里寻找方向、能力要求与迁移路径。', to: '/jobs/search', icon: Search },
  { title: '人岗匹配', desc: '让画像与岗位相遇，拆出优势、差距和下一步。', to: '/match/recommend', icon: Target },
  { title: 'AI 助手', desc: '把犹豫、简历和计划交给模型，得到具体回答。', to: '/assistant/chat', icon: Bot },
]

function openJob(job) {
  router.push(`/jobs/${job.id}`)
}

onMounted(async () => {
  try {
    const data = await jobsApi.search({ page: 1, size: 5, order: 'desc' })
    jobs.value = data.items || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.hero {
  position: relative;
  min-height: min(760px, calc(100vh - 70px));
  display: grid;
  align-items: center;
  overflow: hidden;
  isolation: isolate;
}

.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    linear-gradient(105deg, rgba(244,241,236,.82) 0%, rgba(220,234,223,.5) 48%, rgba(201,177,176,.22) 100%),
    radial-gradient(circle at 76% 38%, rgba(120,160,131,.28), transparent 34%);
}

.sky-depth {
  position: absolute;
  inset: -8% -6%;
  pointer-events: none;
  perspective: 1100px;
  z-index: 1;
  transform-style: preserve-3d;
}

.glow,
.glass-ribbon,
.bird,
.leaf {
  position: absolute;
}

.glow {
  width: 46vw;
  aspect-ratio: 1;
  border-radius: 50%;
  filter: blur(22px);
  opacity: .58;
  mix-blend-mode: screen;
  animation: slowBreath 12s ease-in-out infinite alternate;
}

.glow-a {
  right: 0;
  top: 5%;
  background: radial-gradient(circle, rgba(120,160,131,.42), rgba(220,234,223,.18) 54%, transparent 72%);
}

.glow-b {
  left: 34%;
  bottom: -20%;
  background: radial-gradient(circle, rgba(201,177,176,.34), rgba(217,206,194,.14) 55%, transparent 74%);
  animation-delay: -4s;
}

.glass-ribbon {
  width: 64vw;
  height: 150px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.36), rgba(220,234,223,.28), transparent);
  filter: blur(1px);
  opacity: .7;
  transform: rotate(-14deg) translateZ(120px);
  animation: ribbonDrift 16s ease-in-out infinite alternate;
}

.ribbon-a { left: 28%; top: 16%; }
.ribbon-b { left: 46%; top: 56%; transform: rotate(-18deg) translateZ(40px); animation-duration: 22s; opacity: .46; }

.bird {
  width: 30px;
  height: 12px;
  transform-style: preserve-3d;
  animation: flockMove 13s ease-in-out infinite;
}

.bird::before,
.bird::after {
  content: "";
  position: absolute;
  width: 18px;
  height: 8px;
  border-radius: 999px 999px 2px 999px;
  background: linear-gradient(135deg, rgba(79,124,99,.58), rgba(220,234,223,.72));
  box-shadow: 0 10px 22px rgba(79,124,99,.1);
}

.bird::before {
  left: 0;
  transform: rotate(-18deg);
}

.bird::after {
  right: 0;
  transform: rotate(18deg) scaleX(-1);
}

.leaf {
  width: 18px;
  height: 42px;
  border-radius: 999px 4px 999px 4px;
  background: linear-gradient(180deg, rgba(120,160,131,.34), rgba(244,241,236,.68));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.56), 0 18px 34px rgba(79,124,99,.08);
  animation: leafSway 14s ease-in-out infinite;
}

.bird:nth-of-type(5) { left: 52%; top: 18%; animation-delay: -.2s; transform: translateZ(160px) scale(1.08); }
.bird:nth-of-type(6) { left: 59%; top: 23%; animation-delay: -.9s; transform: translateZ(110px) scale(.92); }
.bird:nth-of-type(7) { left: 67%; top: 17%; animation-delay: -1.6s; transform: translateZ(200px) scale(1.18); }
.bird:nth-of-type(8) { left: 76%; top: 28%; animation-delay: -2.4s; transform: translateZ(90px) scale(.86); }
.bird:nth-of-type(9) { left: 84%; top: 20%; animation-delay: -3.2s; transform: translateZ(150px); }
.bird:nth-of-type(10) { left: 71%; top: 43%; animation-delay: -4s; transform: translateZ(70px) scale(.8); }
.bird:nth-of-type(11) { left: 88%; top: 50%; animation-delay: -4.8s; transform: translateZ(210px) scale(1.2); }
.bird:nth-of-type(12) { left: 57%; top: 57%; animation-delay: -5.6s; transform: translateZ(120px) scale(.9); }
.bird:nth-of-type(13) { left: 92%; top: 68%; animation-delay: -6.4s; transform: translateZ(80px) scale(.72); }
.bird:nth-of-type(14) { left: 46%; top: 35%; animation-delay: -7.2s; transform: translateZ(180px); }
.bird:nth-of-type(15) { left: 80%; top: 12%; animation-delay: -8s; transform: translateZ(130px) scale(.78); }
.bird:nth-of-type(16) { left: 63%; top: 70%; animation-delay: -8.8s; transform: translateZ(170px) scale(.94); }
.bird:nth-of-type(17) { left: 70%; top: 78%; animation-delay: -9.6s; transform: translateZ(55px) scale(.7); }
.bird:nth-of-type(18) { left: 42%; top: 22%; animation-delay: -10.4s; transform: translateZ(135px) scale(.82); }
.bird:nth-of-type(19) { left: 95%; top: 18%; animation-delay: -11.2s; transform: translateZ(95px) scale(.76); }
.bird:nth-of-type(20) { left: 50%; top: 82%; animation-delay: -12s; transform: translateZ(190px) scale(.88); }
.bird:nth-of-type(21) { left: 86%; top: 62%; animation-delay: -12.8s; transform: translateZ(145px) scale(.8); }
.bird:nth-of-type(22) { left: 36%; top: 48%; animation-delay: -13.6s; transform: translateZ(65px) scale(.64); }
.bird:nth-of-type(23) { left: 78%; top: 84%; animation-delay: -14.4s; transform: translateZ(115px) scale(.72); }
.bird:nth-of-type(24) { left: 91%; top: 8%; animation-delay: -15.2s; transform: translateZ(175px) scale(.9); }
.bird:nth-of-type(25) { left: 61%; top: 9%; animation-delay: -16s; transform: translateZ(45px) scale(.62); }
.bird:nth-of-type(26) { left: 69%; top: 34%; animation-delay: -16.8s; transform: translateZ(230px) scale(1.08); }
.bird:nth-of-type(27) { left: 53%; top: 66%; animation-delay: -17.6s; transform: translateZ(105px) scale(.76); }
.bird:nth-of-type(28) { left: 83%; top: 76%; animation-delay: -18.4s; transform: translateZ(155px) scale(.86); }

.leaf:nth-of-type(29) { left: 48%; top: 76%; animation-delay: -.4s; }
.leaf:nth-of-type(30) { left: 74%; top: 74%; animation-delay: -1.5s; transform: translateZ(120px) rotate(18deg); }
.leaf:nth-of-type(31) { left: 89%; top: 36%; animation-delay: -2.6s; transform: translateZ(70px) rotate(-12deg); }
.leaf:nth-of-type(32) { left: 54%; top: 10%; animation-delay: -3.7s; transform: translateZ(160px) rotate(26deg); }
.leaf:nth-of-type(33) { left: 96%; top: 80%; animation-delay: -4.8s; transform: translateZ(30px) rotate(-16deg); }
.leaf:nth-of-type(34) { left: 39%; top: 60%; animation-delay: -5.9s; transform: translateZ(90px) rotate(10deg); }
.leaf:nth-of-type(35) { left: 67%; top: 6%; animation-delay: -7s; transform: translateZ(130px) rotate(-22deg); }
.leaf:nth-of-type(36) { left: 82%; top: 88%; animation-delay: -8.1s; transform: translateZ(60px) rotate(14deg); }
.leaf:nth-of-type(37) { left: 58%; top: 48%; animation-delay: -9.2s; transform: translateZ(200px) rotate(30deg); }
.leaf:nth-of-type(38) { left: 93%; top: 56%; animation-delay: -10.3s; transform: translateZ(100px) rotate(-8deg); }
.leaf:nth-of-type(39) { left: 44%; top: 86%; animation-delay: -11.4s; transform: translateZ(70px) rotate(20deg); }
.leaf:nth-of-type(40) { left: 73%; top: 52%; animation-delay: -12.5s; transform: translateZ(150px) rotate(-26deg); }

.hero-inner {
  position: relative;
  z-index: 2;
  padding: 58px 0 104px;
}

.hero-copy {
  max-width: 620px;
  position: relative;
  padding: 28px 0;
}

.hero-copy::before {
  content: "";
  position: absolute;
  inset: -28px -42px;
  z-index: -1;
  border-radius: 34px;
  background:
    linear-gradient(135deg, rgba(255,255,255,.5), rgba(255,255,255,.12)),
    radial-gradient(circle at 30% 45%, rgba(244,241,236,.78), rgba(220,234,223,.2) 62%, transparent 76%);
  backdrop-filter: blur(12px) saturate(1.1);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.58);
}

.hero-copy p {
  margin: 24px 0 0;
  max-width: 560px;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.9;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 32px;
}

.quick-grid {
  margin-top: -92px;
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.quick {
  cursor: pointer;
  min-height: 176px;
}

.quick h3 {
  margin: 18px 0 8px;
  font-size: 20px;
  font-weight: 500;
}

.quick p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.hot-section {
  padding: 56px 0 26px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

@keyframes slowBreath {
  to { transform: translate3d(4%, -3%, 0) scale(1.08); opacity: .76; }
}

@keyframes ribbonDrift {
  to { margin-left: -42px; margin-top: 28px; opacity: .92; }
}

@keyframes flockMove {
  0%, 100% { margin-left: 0; margin-top: 0; opacity: .46; }
  50% { margin-left: 34px; margin-top: -22px; opacity: .82; }
}

@keyframes leafSway {
  0%, 100% { margin-left: 0; margin-top: 0; opacity: .36; }
  50% { margin-left: -24px; margin-top: -34px; opacity: .68; }
}

@media (max-width: 960px) {
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 580px) {
  .hero {
    min-height: 660px;
  }

  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
