<template>
  <section class="admin-page">
    <div class="hero-map">
      <div class="stats-copy">
        <el-tag effect="plain">General statistics</el-tag>
        <h1>{{ totals.jobs || 0 }}</h1>
        <p>岗位样本覆盖 {{ data.categories?.length || 0 }} 个方向，累计生成 {{ totals.reports || 0 }} 份规划报告和 {{ totals.matches || 0 }} 次匹配记录。</p>
      </div>
      <div ref="graphEl" class="graph-chart"></div>
      <aside class="side-stats">
        <article><strong>{{ totals.users || 0 }}</strong><span>用户</span></article>
        <article><strong>{{ totals.students || 0 }}</strong><span>画像</span></article>
        <article><strong>{{ totals.assessments || 0 }}</strong><span>测评</span></article>
      </aside>
    </div>

    <div class="metric-grid">
      <article v-for="item in metricCards" :key="item.label" class="metric-card">
        <component :is="item.icon" :size="22" />
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>

    <div class="chart-grid">
      <section class="panel">
        <h2>岗位分类分布</h2>
        <div ref="categoryEl" class="chart"></div>
      </section>
      <section class="panel">
        <h2>热门报告方向</h2>
        <div ref="reportEl" class="chart"></div>
      </section>
      <section class="panel wide">
        <h2>近期匹配得分</h2>
        <div ref="matchEl" class="chart"></div>
      </section>
    </div>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { BriefcaseBusiness, FileText, Network, UsersRound } from 'lucide-vue-next'
import { adminApi } from '@/api'

const data = ref({})
const categoryEl = ref(null)
const reportEl = ref(null)
const matchEl = ref(null)
const graphEl = ref(null)
const charts = []
const totals = computed(() => data.value.totals || {})
const metricCards = computed(() => [
  { label: '用户数', value: totals.value.users || 0, icon: UsersRound },
  { label: '岗位数', value: totals.value.jobs || 0, icon: BriefcaseBusiness },
  { label: '报告数', value: totals.value.reports || 0, icon: FileText },
  { label: '图谱边', value: data.value.graph?.links?.length || 0, icon: Network },
])

function mountChart(el, option) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function render() {
  charts.splice(0).forEach((chart) => chart.dispose())
  const categories = data.value.categories || []
  const reportJobs = data.value.report_jobs || []
  const matchScores = data.value.match_scores || []
  const graph = data.value.graph || { nodes: [], links: [] }

  mountChart(categoryEl.value, {
    color: ['#7F8FA3', '#A5B5B2', '#C9B1B0', '#D9CEC2', '#78A083'],
    tooltip: {},
    series: [{ type: 'pie', radius: ['44%', '72%'], data: categories }],
  })
  mountChart(reportEl.value, {
    color: ['#7F8FA3'],
    tooltip: {},
    grid: { left: 90, right: 20, top: 18, bottom: 28 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: reportJobs.map((item) => item.name).reverse() },
    series: [{ type: 'bar', data: reportJobs.map((item) => item.value).reverse(), barWidth: 12 }],
  })
  mountChart(matchEl.value, {
    color: ['#C9B1B0'],
    tooltip: {},
    grid: { left: 40, right: 24, top: 24, bottom: 36 },
    xAxis: { type: 'category', data: matchScores.map((item) => item.job_name || '岗位') },
    yAxis: { type: 'value', max: 100 },
    series: [{ type: 'line', smooth: true, areaStyle: {}, data: matchScores.map((item) => Number(item.match_score || 0)) }],
  })
  mountChart(graphEl.value, {
    tooltip: {},
    series: [{
      type: 'graph',
      layout: 'force',
      roam: false,
      data: graph.nodes || [],
      links: graph.links || [],
      symbolSize: 18,
      force: { repulsion: 80, edgeLength: 70 },
      lineStyle: { color: '#7F8FA3', opacity: .38 },
      itemStyle: { color: '#7F8FA3' },
      label: { show: false },
    }],
  })
}

onMounted(async () => {
  data.value = await adminApi.dashboard()
  await nextTick()
  render()
  window.addEventListener('resize', render)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', render)
  charts.forEach((chart) => chart.dispose())
})
</script>

<style scoped>
.admin-page {
  display: grid;
  gap: 18px;
}

.hero-map,
.panel,
.metric-card {
  border-radius: 20px;
  background: rgba(255,255,255,.68);
  box-shadow: 0 18px 54px rgba(79,88,102,.1);
  backdrop-filter: blur(24px);
}

.hero-map {
  min-height: 430px;
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 160px;
  gap: 18px;
  padding: 28px;
}

.hero-map::before {
  content: "";
  position: absolute;
  inset: 36px 180px 36px 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(127,143,163,.22), rgba(255,255,255,.05) 64%, transparent 68%);
  pointer-events: none;
}

.stats-copy {
  position: relative;
  z-index: 1;
}

.stats-copy h1 {
  margin: 18px 0 10px;
  font-size: 58px;
}

.stats-copy p {
  color: var(--muted);
  line-height: 1.8;
}

.graph-chart {
  position: relative;
  z-index: 1;
  min-height: 360px;
}

.side-stats {
  display: grid;
  align-content: center;
  gap: 14px;
}

.side-stats article,
.metric-card {
  padding: 18px;
  background: rgba(255,255,255,.7);
}

.side-stats strong,
.metric-card strong {
  display: block;
  font-size: 28px;
  color: #3c4148;
}

.side-stats span,
.metric-card span {
  color: var(--muted);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  display: grid;
  gap: 8px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.panel {
  padding: 20px;
}

.panel.wide {
  grid-column: 1 / -1;
}

.panel h2 {
  margin: 0 0 14px;
}

.chart {
  height: 320px;
}

@media (max-width: 1040px) {
  .hero-map,
  .chart-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
