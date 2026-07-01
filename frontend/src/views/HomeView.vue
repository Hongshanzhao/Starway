<template>
  <div class="home">
    <section class="hero">
      <div class="cinematic-bg" aria-hidden="true">
        <span v-for="n in 22" :key="`spark-${n}`" class="spark"></span>
        <span v-for="n in 9" :key="`veil-${n}`" class="wind-veil"></span>
      </div>

      <div class="page-shell hero-grid">
        <div class="hero-copy">
          <div class="brand-signature">
            <img class="brand-art" :src="wordmark" alt="Starway" />
          </div>
          <el-tag effect="plain" class="hero-tag">Career Intelligence in Motion</el-tag>
          <h1 class="page-title">
            <span>让风经过山脊</span>
            <span>让未来显出航线</span>
          </h1>
          <p>
            Starway 把你的画像、兴趣、岗位与 AI 判断织成一张会呼吸的星图。
            不是替你决定去哪里，而是让方向、证据和下一步都变得清晰。
          </p>
          <div class="hero-actions">
            <el-button type="primary" size="large" :icon="Sparkles" @click="router.push('/profile/create')">
              开启星图
            </el-button>
            <el-button size="large" :icon="Search" @click="router.push('/jobs/search')">
              追踪岗位风向
            </el-button>
          </div>
        </div>

        <div class="orbit-panel glass-panel">
          <div class="orbit-core">
            <span class="orbit-ring ring-a"></span>
            <span class="orbit-ring ring-b"></span>
            <span class="orbit-ring ring-c"></span>
            <span class="orbit-dot dot-a"></span>
            <span class="orbit-dot dot-b"></span>
            <span class="orbit-dot dot-c"></span>
            <strong>AI</strong>
          </div>
          <div class="signal-list">
            <article v-for="item in signals" :key="item.label">
              <span>{{ item.value }}</span>
              <p>{{ item.label }}</p>
            </article>
          </div>
        </div>
      </div>

      <div class="page-shell compass-strip">
        <article v-for="item in quick" :key="item.to" class="compass-card glass-panel" @click="router.push(item.to)">
          <component :is="item.icon" :size="24" />
          <div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="page-shell manifesto">
      <div class="section-head">
        <span>Starway Method</span>
        <h2>把模糊的愿望，落成可验证的生长路径</h2>
      </div>
      <div class="method-grid">
        <GlassCard v-for="item in methods" :key="item.title" class="method-card">
          <small>{{ item.step }}</small>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </GlassCard>
      </div>
    </section>

    <section class="page-shell hot-section">
      <div class="section-head row">
        <div>
          <span>Live Positions</span>
          <h2>此刻值得眺望的岗位</h2>
        </div>
        <el-button text @click="router.push('/jobs/search')">进入岗位星图</el-button>
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
import wordmark from '@/assets/starway-wordmark-transparent.png'

const router = useRouter()
const loading = ref(true)
const jobs = ref([])

const signals = [
  { value: '画像', label: '看见真实的你' },
  { value: '岗位', label: '读取市场风向' },
  { value: '路径', label: '留下可验证证据' },
]

const quick = [
  { title: '兴趣罗盘', desc: '先听见自己的偏好，再决定奔赴哪片海。', to: '/assessment', icon: Compass },
  { title: '岗位星图', desc: '从真实岗位里看见能力、迁移与远方。', to: '/jobs/search', icon: Search },
  { title: '人岗回声', desc: '让画像与岗位相遇，听清优势与缺口。', to: '/match/recommend', icon: Target },
  { title: 'AI 旅伴', desc: '把困惑交给模型，把行动带回生活。', to: '/assistant/chat', icon: Bot },
]

const methods = [
  { step: '01', title: '画像成像', desc: '把教育、技能、经历、兴趣汇成一张可以被分析的个人星图。' },
  { step: '02', title: '岗位折光', desc: '用真实岗位数据拆出技能、任务、产出物与迁移可能。' },
  { step: '03', title: '行动落地', desc: '把 AI 的判断变成 30/60/90 天路线、作品证据和复盘指标。' },
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
.home {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  isolation: isolate;
  background: #071416;
  color: white;
}

.home::before,
.home::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.home::before {
  z-index: -2;
  background: url('/1.jpg') center / cover no-repeat;
  filter: saturate(1.05) contrast(1.04);
  transform: scale(1.035);
  animation: bgBreath 18s ease-in-out infinite alternate;
}

.home::after {
  z-index: -1;
  background:
    linear-gradient(90deg, rgba(4,16,20,.76) 0%, rgba(13,33,30,.52) 34%, rgba(18,47,38,.1) 62%, rgba(4,12,14,.38) 100%),
    linear-gradient(180deg, rgba(5,14,18,.08) 0%, rgba(7,22,22,.18) 46%, rgba(7,18,18,.82) 100%);
}

.hero {
  position: relative;
  min-height: min(920px, calc(100vh - 78px));
  padding: 64px 0 0;
  display: grid;
  align-content: center;
  overflow: hidden;
  isolation: isolate;
  color: white;
  perspective: 1400px;
}

.cinematic-bg {
  position: absolute;
  inset: 0;
}

.cinematic-bg {
  z-index: 0;
  overflow: hidden;
  transform-style: preserve-3d;
}

.spark,
.wind-veil {
  position: absolute;
  z-index: 2;
  pointer-events: none;
}

.spark {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(220,234,223,.9);
  box-shadow: 0 0 18px rgba(220,234,223,.9);
  animation: sparkFloat 10s ease-in-out infinite;
}

.spark:nth-of-type(1) { left: 18%; top: 24%; animation-delay: -.2s; }
.spark:nth-of-type(2) { left: 32%; top: 36%; animation-delay: -1.1s; }
.spark:nth-of-type(3) { left: 46%; top: 18%; animation-delay: -2s; }
.spark:nth-of-type(4) { left: 60%; top: 22%; animation-delay: -2.9s; }
.spark:nth-of-type(5) { left: 78%; top: 28%; animation-delay: -3.8s; }
.spark:nth-of-type(6) { left: 86%; top: 46%; animation-delay: -4.7s; }
.spark:nth-of-type(7) { left: 70%; top: 64%; animation-delay: -5.6s; }
.spark:nth-of-type(8) { left: 54%; top: 72%; animation-delay: -6.5s; }
.spark:nth-of-type(9) { left: 38%; top: 66%; animation-delay: -7.4s; }
.spark:nth-of-type(10) { left: 24%; top: 58%; animation-delay: -8.3s; }
.spark:nth-of-type(11) { left: 12%; top: 44%; animation-delay: -9.2s; }
.spark:nth-of-type(12) { left: 91%; top: 18%; animation-delay: -10.1s; }
.spark:nth-of-type(13) { left: 64%; top: 8%; animation-delay: -11s; }
.spark:nth-of-type(14) { left: 48%; top: 52%; animation-delay: -11.9s; }
.spark:nth-of-type(15) { left: 74%; top: 78%; animation-delay: -12.8s; }
.spark:nth-of-type(16) { left: 88%; top: 72%; animation-delay: -13.7s; }
.spark:nth-of-type(17) { left: 42%; top: 84%; animation-delay: -14.6s; }
.spark:nth-of-type(18) { left: 30%; top: 16%; animation-delay: -15.5s; }
.spark:nth-of-type(19) { left: 56%; top: 42%; animation-delay: -16.4s; }
.spark:nth-of-type(20) { left: 83%; top: 10%; animation-delay: -17.3s; }
.spark:nth-of-type(21) { left: 68%; top: 38%; animation-delay: -18.2s; }
.spark:nth-of-type(22) { left: 15%; top: 76%; animation-delay: -19.1s; }

.wind-veil {
  width: 54vw;
  height: 120px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.34), rgba(220,234,223,.2), transparent);
  filter: blur(4px);
  opacity: .5;
  transform: rotate(-16deg);
  animation: veilRun 16s ease-in-out infinite;
}

.wind-veil:nth-of-type(23) { left: -12%; top: 18%; animation-delay: -1s; }
.wind-veil:nth-of-type(24) { left: 18%; top: 34%; animation-delay: -4s; animation-duration: 19s; }
.wind-veil:nth-of-type(25) { left: 48%; top: 12%; animation-delay: -7s; animation-duration: 21s; }
.wind-veil:nth-of-type(26) { left: 8%; top: 68%; animation-delay: -10s; animation-duration: 18s; }
.wind-veil:nth-of-type(27) { left: 54%; top: 58%; animation-delay: -13s; animation-duration: 23s; }
.wind-veil:nth-of-type(28) { left: 30%; top: 82%; animation-delay: -16s; animation-duration: 20s; }
.wind-veil:nth-of-type(29) { left: 70%; top: 38%; animation-delay: -19s; animation-duration: 24s; }
.wind-veil:nth-of-type(30) { left: -18%; top: 48%; animation-delay: -22s; animation-duration: 22s; }
.wind-veil:nth-of-type(31) { left: 62%; top: 84%; animation-delay: -25s; animation-duration: 26s; }

.hero-grid {
  position: relative;
  z-index: 3;
  padding: 30px 0 150px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, .72fr);
  gap: 40px;
  align-items: center;
}

.hero-copy {
  max-width: 720px;
  border-radius: 30px;
  padding: clamp(24px, 4vw, 42px);
  background:
    linear-gradient(135deg, rgba(255,255,255,.26), rgba(255,255,255,.08)),
    rgba(11,30,30,.16);
  border: 1px solid rgba(255,255,255,.34);
  box-shadow:
    0 34px 100px rgba(0,0,0,.22),
    inset 0 1px 0 rgba(255,255,255,.42);
  backdrop-filter: blur(22px) saturate(1.24);
  -webkit-backdrop-filter: blur(22px) saturate(1.24);
  transform: rotateY(-7deg) rotateX(2deg) translateZ(70px);
  transform-style: preserve-3d;
  animation: panelFloat 8s ease-in-out infinite alternate;
}

.brand-signature {
  width: min(310px, 64vw);
  margin: -24px 0 16px -18px;
  border-radius: 24px;
  padding: 0 4px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(255,255,255,.08), rgba(255,255,255,.02)),
    rgba(206,238,218,.03);
  box-shadow: none;
}

.brand-art {
  width: 100%;
  display: block;
  filter: saturate(1.35) brightness(1.42) contrast(1.08) drop-shadow(0 18px 42px rgba(151,231,185,.28));
  opacity: .95;
}

.hero-tag {
  color: rgba(236,250,241,.88);
  border-color: rgba(255,255,255,.38);
  background: rgba(255,255,255,.12);
}

.page-title {
  max-width: 720px;
  margin-top: 18px;
  color: #f8fff9;
  font-size: clamp(42px, 5.45vw, 72px);
  line-height: 1.04;
  font-weight: 520;
  text-shadow: 0 18px 54px rgba(0,0,0,.28);
}

.page-title span {
  display: block;
}

.hero-copy p {
  margin: 28px 0 0;
  max-width: 610px;
  color: rgba(239,250,244,.82);
  font-size: 18px;
  line-height: 1.95;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 34px;
}

.orbit-panel {
  min-height: 470px;
  padding: 28px;
  display: grid;
  align-content: space-between;
  color: #ecfaf1;
  background:
    linear-gradient(145deg, rgba(255,255,255,.2), rgba(255,255,255,.06)),
    rgba(5,22,25,.18);
  border-color: rgba(255,255,255,.28);
  border-radius: 28px;
  transform: rotateY(9deg) rotateX(4deg) translateZ(120px);
  box-shadow: 0 38px 90px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.36);
  animation: panelFloat 9s ease-in-out infinite alternate-reverse;
}

.orbit-core {
  min-height: 300px;
  position: relative;
  display: grid;
  place-items: center;
  transform-style: preserve-3d;
}

.orbit-core strong {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #24463b;
  font-size: 34px;
  background: radial-gradient(circle at 35% 28%, #f8fff9, #bde8cc 58%, #7f8fa3);
  box-shadow: 0 0 50px rgba(189,232,204,.62), inset 0 1px 0 white;
}

.orbit-ring {
  position: absolute;
  border: 1px solid rgba(220,234,223,.42);
  border-radius: 50%;
  transform-style: preserve-3d;
}

.ring-a { width: 260px; height: 108px; transform: rotateX(68deg) rotateZ(-14deg); animation: orbitSpin 16s linear infinite; }
.ring-b { width: 300px; height: 142px; transform: rotateX(62deg) rotateZ(38deg); animation: orbitSpin 22s linear infinite reverse; }
.ring-c { width: 220px; height: 220px; transform: rotateY(64deg) rotateZ(16deg); animation: orbitSpin 18s linear infinite; }

.orbit-dot {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #dceadf;
  box-shadow: 0 0 20px #dceadf;
}

.dot-a { left: 18%; top: 44%; animation: dotPulse 2.8s ease-in-out infinite; }
.dot-b { right: 18%; top: 30%; animation: dotPulse 3.2s ease-in-out infinite -.8s; }
.dot-c { right: 32%; bottom: 20%; animation: dotPulse 3.6s ease-in-out infinite -1.6s; }

.signal-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.signal-list article {
  border-radius: 18px;
  padding: 14px 12px;
  background: rgba(255,255,255,.12);
  border: 1px solid rgba(255,255,255,.18);
}

.signal-list span {
  display: block;
  color: #f9fff9;
  font-weight: 700;
}

.signal-list p {
  margin: 6px 0 0;
  color: rgba(239,250,244,.68);
  font-size: 12px;
}

.compass-strip {
  position: relative;
  z-index: 4;
  margin-top: -98px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.compass-card {
  min-height: 132px;
  padding: 18px;
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 14px;
  align-items: start;
  cursor: pointer;
  color: #ecfaf1;
  background:
    linear-gradient(145deg, rgba(255,255,255,.24), rgba(255,255,255,.08)),
    rgba(7,28,29,.18);
  border-color: rgba(255,255,255,.26);
  box-shadow: 0 20px 58px rgba(0,0,0,.16), inset 0 1px 0 rgba(255,255,255,.3);
  transition: transform .28s ease, box-shadow .28s ease;
}

.compass-card:hover {
  transform: translateY(-8px) rotateX(4deg);
  box-shadow: 0 30px 70px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.42);
}

.compass-card h3 {
  margin: 0 0 8px;
  color: #f9fff9;
  font-size: 18px;
}

.compass-card p {
  margin: 0;
  color: rgba(239,250,244,.72);
  line-height: 1.65;
}

.manifesto {
  padding: 74px 0 20px;
}

.section-head {
  margin-bottom: 24px;
}

.section-head span {
  color: rgba(220,234,223,.78);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}

.section-head h2 {
  max-width: 920px;
  margin: 10px 0 0;
  color: #f8fff9;
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.18;
  font-weight: 520;
  text-shadow: 0 18px 54px rgba(0,0,0,.28);
}

.section-head.row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: end;
}

.method-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.method-card {
  min-height: 230px;
  color: #f8fff9;
  background:
    linear-gradient(145deg, rgba(255,255,255,.22), rgba(255,255,255,.08)),
    rgba(7,28,29,.2);
  border-color: rgba(255,255,255,.26);
}

.method-card small {
  display: inline-flex;
  width: 46px;
  height: 46px;
  border-radius: 16px;
  align-items: center;
  justify-content: center;
  color: white;
  background: linear-gradient(135deg, var(--leaf), var(--mist-blue));
}

.method-card h3 {
  margin: 24px 0 10px;
  font-size: 22px;
}

.method-card p {
  margin: 0;
  color: rgba(239,250,244,.72);
  line-height: 1.8;
}

.hot-section {
  padding: 54px 0 34px;
}

.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

@keyframes bgBreath {
  to { transform: scale(1.075) translate3d(-1.4%, -1%, 0); }
}

@keyframes sparkFloat {
  0%, 100% { transform: translate3d(0, 0, 60px) scale(.7); opacity: .22; }
  50% { transform: translate3d(44px, -40px, 180px) scale(1.25); opacity: .9; }
}

@keyframes veilRun {
  0%, 100% { transform: translate3d(-5%, 0, 80px) rotate(-16deg); opacity: .16; }
  50% { transform: translate3d(12%, -26px, 160px) rotate(-16deg); opacity: .5; }
}

@keyframes panelFloat {
  to { transform: rotateY(-3deg) rotateX(4deg) translate3d(0, -16px, 100px); }
}

@keyframes orbitSpin {
  to { rotate: 360deg; }
}

@keyframes dotPulse {
  50% { transform: scale(1.8); opacity: .45; }
}

@media (max-width: 1060px) {
  .hero-grid {
    grid-template-columns: 1fr;
    padding-bottom: 132px;
  }

  .hero-copy,
  .orbit-panel {
    transform: none;
  }

  .orbit-panel {
    min-height: 360px;
  }

  .compass-strip,
  .method-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .hero {
    min-height: auto;
    padding-top: 34px;
  }

  .hero-grid {
    padding-bottom: 120px;
  }

  .hero-copy {
    padding: 22px;
  }

  .brand-art {
    width: min(260px, 78vw);
  }

  .page-title {
    font-size: clamp(36px, 13vw, 58px);
  }

  .orbit-panel {
    display: none;
  }

  .compass-strip,
  .method-grid,
  .section-head.row {
    grid-template-columns: 1fr;
    display: grid;
  }

  .compass-card {
    min-height: 116px;
  }
}
</style>
