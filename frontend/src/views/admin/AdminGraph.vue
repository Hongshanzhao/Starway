<template>
  <section class="page">
    <div class="tool-hero">
      <div>
        <el-tag effect="plain">Knowledge Graph</el-tag>
        <h1>岗位关系图谱</h1>
        <p>这不是单纯“点一下构建”。它用来检查岗位之间的晋升和换岗关系是否覆盖充分，直接影响前台的成长路径、相似岗位和换岗建议。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="run">重新计算关系</el-button>
    </div>

    <div class="summary-grid">
      <article><span>岗位覆盖率</span><strong>{{ overview.coverage || 0 }}%</strong></article>
      <article><span>图谱节点</span><strong>{{ graph.nodes?.length || 0 }}</strong></article>
      <article><span>关系数量</span><strong>{{ graph.links?.length || 0 }}</strong></article>
      <article><span>孤立岗位</span><strong>{{ overview.isolated_jobs || 0 }}</strong></article>
    </div>

    <div class="result-grid">
      <section class="result-panel graph-panel">
        <div class="panel-head">
          <h2>关系网络</h2>
          <span>{{ graph.nodes?.length || 0 }} 节点 · {{ graph.links?.length || 0 }} 关系</span>
        </div>
        <div ref="graphEl" class="graph"></div>
      </section>
      <section class="result-panel">
        <h2>关系类型</h2>
        <div ref="typeEl" class="type-chart"></div>
        <div class="status-card" :class="{ success: result.success }">
          <strong>{{ result.success ? '本次构建完成' : '当前图谱状态' }}</strong>
          <p>{{ result.message || graphAdvice }}</p>
        </div>
        <div class="explain-box">
          <h3>管理员看什么</h3>
          <p>覆盖率低，说明很多岗位没有可解释的路线，前台路径会显得空。孤立岗位多时，优先去岗位管理补技能、描述和行业字段。</p>
          <h3>构建后有什么用</h3>
          <p>用户查看成长路径时，系统会基于这些关系给出晋升方向和可迁移方向；匹配报告也能引用更可信的路径数据。</p>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { adminApi } from '@/api'

const loading = ref(false)
const result = ref({})
const overview = ref({})
const graphEl = ref(null)
const typeEl = ref(null)
let graphChart
let typeChart

const graph = computed(() => result.value.graph || overview.value.graph || { nodes: [], links: [] })
const graphAdvice = computed(() => {
  if (!overview.value.total_jobs) return '当前还没有图谱数据，建议先执行一次关系计算。'
  if (Number(overview.value.coverage || 0) < 60) return '覆盖率偏低，建议补充岗位技能、岗位描述和行业字段后重新计算。'
  return '图谱覆盖情况可用，可以继续观察孤立岗位和关系类型是否均衡。'
})

async function loadOverview() {
  overview.value = await adminApi.graphOverview().catch(() => ({}))
  await nextTick()
  render()
}

async function run() {
  loading.value = true
  try {
    result.value = await adminApi.buildGraph()
    overview.value = await adminApi.graphOverview().catch(() => overview.value)
    await nextTick()
    render()
  } finally {
    loading.value = false
  }
}

function render() {
  if (graphEl.value) {
    if (!graphChart) graphChart = echarts.init(graphEl.value)
    graphChart.setOption({
      tooltip: { formatter: (p) => p.data?.description || p.name },
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        data: graph.value.nodes || [],
        links: graph.value.links || [],
        symbolSize: 18,
        force: { repulsion: 120, edgeLength: 80 },
        categories: [{ name: '岗位' }],
        lineStyle: { color: '#7F8FA3', opacity: .42 },
        itemStyle: { color: '#7F8FA3' },
        label: { show: true, fontSize: 10, color: '#59616b' },
      }],
    })
  }
  if (typeEl.value) {
    if (!typeChart) typeChart = echarts.init(typeEl.value)
    typeChart.setOption({
      color: ['#7F8FA3', '#C9B1B0', '#A5B5B2'],
      tooltip: {},
      series: [{ type: 'pie', radius: ['46%', '72%'], data: overview.value.relation_types || [] }],
    })
  }
}

onMounted(loadOverview)
onBeforeUnmount(() => {
  graphChart?.dispose()
  typeChart?.dispose()
})
</script>

<style scoped>
.page { display:grid; gap:18px; }
.tool-hero,.summary-grid article,.result-panel {
  border-radius:20px;
  background:rgba(255,255,255,.68);
  box-shadow:0 18px 54px rgba(79,88,102,.1);
  backdrop-filter:blur(24px);
}
.tool-hero { min-height:190px; padding:28px; display:flex; justify-content:space-between; gap:20px; align-items:center; }
.tool-hero h1 { margin:14px 0; font-size:42px; }
.tool-hero p,.status-card p,.explain-box p { color:var(--muted); line-height:1.75; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
.summary-grid article { padding:20px; }
.summary-grid span,.panel-head span { color:var(--muted); }
.summary-grid strong { display:block; margin-top:8px; font-size:34px; }
.result-grid { display:grid; grid-template-columns:minmax(0,1.3fr) 380px; gap:18px; }
.result-panel { padding:20px; }
.panel-head { display:flex; justify-content:space-between; gap:12px; align-items:center; }
.panel-head h2,.result-panel h2 { margin:0 0 16px; }
.graph { height:560px; }
.type-chart { height:240px; }
.status-card,.explain-box { border-radius:16px; padding:16px; background:rgba(255,255,255,.64); box-shadow:inset 0 0 0 1px rgba(127,143,163,.12); margin-top:14px; }
.status-card.success strong { color:#4f7c63; }
.explain-box h3 { margin:0 0 8px; font-size:17px; }
.explain-box p { margin:0 0 14px; }
@media (max-width: 980px) { .summary-grid,.result-grid { grid-template-columns:1fr; } .tool-hero { align-items:flex-start; flex-direction:column; } }
</style>
