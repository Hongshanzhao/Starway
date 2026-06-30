<template>
  <section class="page">
    <div class="ai-hero">
      <div>
        <el-tag effect="plain">AI Operations</el-tag>
        <h1>AI 产出监控</h1>
        <p>这里不再放一个模糊的“工具箱”。管理员可以看到 AI 产出的数量、质量和需要处理的任务，知道下一步该补数据、重建图谱还是复查报告。</p>
      </div>
      <el-button type="primary" :loading="building" @click="buildGraph">刷新图谱底座</el-button>
    </div>

    <div class="summary-grid">
      <article><span>职业报告</span><strong>{{ totals.reports || 0 }}</strong></article>
      <article><span>人岗匹配</span><strong>{{ totals.matches || 0 }}</strong></article>
      <article><span>兴趣测评</span><strong>{{ totals.assessments || 0 }}</strong></article>
      <article><span>报告可用率</span><strong>{{ quality.report_quality_rate || 0 }}%</strong></article>
    </div>

    <div class="chart-grid">
      <section class="panel">
        <div class="panel-head"><h2>AI 产出分布</h2><span>看平台 AI 能力使用在哪些地方</span></div>
        <div ref="outputEl" class="chart"></div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>热门报告方向</h2><span>帮助判断用户真实需求</span></div>
        <div ref="reportEl" class="chart"></div>
      </section>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h2>管理员待办</h2>
        <span>每一项都对应前台体验提升</span>
      </div>
      <div class="task-grid">
        <article v-for="task in tasks" :key="task.name">
          <strong>{{ task.name }}</strong>
          <p>{{ task.impact }}</p>
          <el-button text @click="goTask(task.action)">去处理</el-button>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi } from '@/api'

const router = useRouter()
const data = ref({})
const building = ref(false)
const outputEl = ref(null)
const reportEl = ref(null)
let outputChart
let reportChart

const totals = computed(() => data.value.totals || {})
const quality = computed(() => data.value.quality || {})
const tasks = computed(() => data.value.tasks || [])

async function load() {
  data.value = await adminApi.aiToolsOverview()
  await nextTick()
  render()
}

async function buildGraph() {
  building.value = true
  try {
    await adminApi.buildGraph()
    router.push('/admin/graph')
  } finally {
    building.value = false
  }
}

function goTask(action) {
  const map = {
    build_graph: '/admin/graph',
    review_reports: '/admin/reports',
    review_jobs: '/admin/jobs',
  }
  router.push(map[action] || '/admin/dashboard')
}

function render() {
  if (outputEl.value) {
    if (!outputChart) outputChart = echarts.init(outputEl.value)
    outputChart.setOption({
      color: ['#7F8FA3', '#A5B5B2', '#C9B1B0'],
      tooltip: {},
      series: [{ type: 'pie', radius: ['46%', '72%'], data: data.value.ai_outputs || [] }],
    })
  }
  if (reportEl.value) {
    if (!reportChart) reportChart = echarts.init(reportEl.value)
    const rows = data.value.report_jobs || []
    reportChart.setOption({
      color: ['#7F8FA3'],
      tooltip: {},
      grid: { left: 110, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: rows.map((item) => item.name).reverse() },
      series: [{ type: 'bar', barWidth: 14, data: rows.map((item) => item.value).reverse() }],
    })
  }
}

onMounted(load)
onBeforeUnmount(() => {
  outputChart?.dispose()
  reportChart?.dispose()
})
</script>

<style scoped>
.page { display:grid; gap:18px; }
.ai-hero,.summary-grid article,.panel {
  border-radius:20px;
  padding:24px;
  background:rgba(255,255,255,.68);
  box-shadow:0 18px 54px rgba(79,88,102,.1);
  backdrop-filter:blur(24px);
}
.ai-hero { min-height:190px; display:flex; justify-content:space-between; gap:20px; align-items:center; }
.ai-hero h1 { margin:14px 0; font-size:42px; }
.ai-hero p,.panel-head span,.task-grid p { color:var(--muted); line-height:1.75; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
.summary-grid span { color:var(--muted); }
.summary-grid strong { display:block; margin-top:8px; font-size:34px; }
.chart-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
.panel-head { display:flex; justify-content:space-between; gap:12px; align-items:center; }
.panel-head h2 { margin:0; }
.chart { height:320px; }
.task-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:16px; }
.task-grid article { border-radius:16px; padding:16px; background:rgba(255,255,255,.62); box-shadow:inset 0 0 0 1px rgba(127,143,163,.12); }
.task-grid strong { color:#3c4148; }
@media (max-width: 980px) { .summary-grid,.chart-grid,.task-grid { grid-template-columns:1fr; } .ai-hero { align-items:flex-start; flex-direction:column; } }
</style>
