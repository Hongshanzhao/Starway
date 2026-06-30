<template>
  <section class="page-shell center-page">
    <div class="assessment-hero">
      <div class="copy">
        <el-tag effect="plain">Holland RIASEC</el-tag>
        <h1>兴趣测评</h1>
        <p>三十道题勾勒六种职业倾向：你愿意靠近什么样的任务，习惯怎样工作，又在哪些场景里更容易发光。</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="router.push('/assessment/start')">开始测评</el-button>
          <el-button size="large" @click="router.push('/user/interests')">查看历史</el-button>
        </div>
      </div>
      <div class="constellation" aria-hidden="true">
        <span v-for="item in dimensions" :key="item.code" :style="{ '--x': item.x, '--y': item.y, '--delay': item.delay }">
          {{ item.code }}
        </span>
      </div>
    </div>

    <div class="dimension-grid">
      <article v-for="item in dimensions" :key="item.code" class="dimension-card">
        <div class="code">{{ item.code }}</div>
        <div>
          <h2>{{ item.name }}</h2>
          <p>{{ item.desc }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const dimensions = [
  { code: 'R', name: '现实型', desc: '偏爱具体、动手、可操作的任务，适合工程、制造、运维与技术实践。', x: '16%', y: '28%', delay: '0s' },
  { code: 'I', name: '研究型', desc: '喜欢分析、推理和探索问题，适合数据、算法、科研、咨询与策略分析。', x: '48%', y: '14%', delay: '.18s' },
  { code: 'A', name: '艺术型', desc: '重视表达、审美和创造，适合设计、内容、品牌、创意策划与体验工作。', x: '78%', y: '30%', delay: '.36s' },
  { code: 'S', name: '社会型', desc: '愿意帮助、沟通和协作，适合教育、心理、人力、运营与用户服务。', x: '72%', y: '72%', delay: '.54s' },
  { code: 'E', name: '企业型', desc: '享受影响、组织和推进目标，适合产品、销售、管理、创业与商业拓展。', x: '38%', y: '82%', delay: '.72s' },
  { code: 'C', name: '常规型', desc: '偏好秩序、流程和精确执行，适合财务、审计、风控、行政与项目管理。', x: '14%', y: '68%', delay: '.9s' },
]
</script>

<style scoped>
.center-page {
  padding: 26px 0 56px;
}

.assessment-hero {
  min-height: 420px;
  border-radius: 32px;
  padding: 44px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr);
  gap: 28px;
  overflow: hidden;
  position: relative;
  background:
    radial-gradient(circle at 82% 18%, rgba(217, 206, 194, .58), transparent 28%),
    linear-gradient(135deg, #7f8fa3, #a5b5b2 56%, #c9b1b0);
  box-shadow: 0 30px 76px rgba(79, 88, 102, .2);
}

.copy {
  color: white;
  position: relative;
  z-index: 1;
  align-self: center;
}

.copy h1 {
  margin: 18px 0;
  font-size: clamp(46px, 7vw, 86px);
  line-height: 1;
  font-weight: 650;
}

.copy p {
  margin: 0;
  max-width: 720px;
  font-size: 18px;
  line-height: 1.95;
  color: rgba(255, 255, 255, .9);
}

.hero-actions {
  margin-top: 28px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.constellation {
  position: relative;
  min-height: 330px;
}

.constellation::before,
.constellation::after {
  content: "";
  position: absolute;
  inset: 17% 12%;
  border: 1px solid rgba(255,255,255,.36);
  border-radius: 50%;
  transform: rotate(-16deg);
}

.constellation::after {
  inset: 29% 22%;
  transform: rotate(22deg);
}

.constellation span {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: 72px;
  height: 72px;
  margin: -36px 0 0 -36px;
  border-radius: 24px;
  display: grid;
  place-items: center;
  color: #586270;
  font-size: 28px;
  font-weight: 700;
  background: rgba(255,255,255,.7);
  box-shadow: 0 18px 42px rgba(60,65,72,.16);
  backdrop-filter: blur(14px);
  animation: drift 4.8s ease-in-out infinite;
  animation-delay: var(--delay);
}

.dimension-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.dimension-card {
  min-height: 188px;
  padding: 22px;
  border-radius: 24px;
  display: grid;
  grid-template-columns: 58px 1fr;
  gap: 16px;
  background: rgba(255,255,255,.62);
  border: 1px solid rgba(255,255,255,.68);
  box-shadow: 0 20px 54px rgba(79,88,102,.11);
  backdrop-filter: blur(18px);
  transition: transform .35s ease, box-shadow .35s ease;
}

.dimension-card:hover {
  transform: translateY(-7px);
  box-shadow: 0 30px 70px rgba(79,88,102,.17);
}

.code {
  width: 58px;
  height: 58px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--mist-blue), var(--rose));
}

h2 {
  margin: 2px 0 8px;
  font-size: 21px;
  font-weight: 600;
}

p {
  color: var(--muted);
  line-height: 1.75;
}

@keyframes drift {
  50% { transform: translateY(-14px) rotate(3deg); }
}

@media (max-width: 920px) {
  .assessment-hero {
    grid-template-columns: 1fr;
  }

  .constellation {
    min-height: 260px;
  }

  .dimension-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .assessment-hero {
    padding: 30px;
  }

  .constellation {
    display: none;
  }

  .dimension-grid {
    grid-template-columns: 1fr;
  }
}
</style>
