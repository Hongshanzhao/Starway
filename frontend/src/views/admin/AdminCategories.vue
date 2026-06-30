<template>
  <section class="page">
    <div class="admin-hero">
      <div>
        <el-tag effect="plain">Category Analytics</el-tag>
        <h1>岗位分类统计</h1>
        <p>查看岗位库的方向分布，判断哪些类别样本充足、哪些类别需要补充岗位数据。</p>
      </div>
      <div class="hero-number">
        <strong>{{ totalJobs }}</strong>
        <span>岗位样本</span>
      </div>
    </div>

    <div class="chart-grid">
      <section class="panel">
        <h2>分类占比</h2>
        <div ref="pieEl" class="chart"></div>
      </section>
      <section class="panel">
        <h2>数量排行</h2>
        <div ref="barEl" class="chart"></div>
      </section>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h2>分类明细</h2>
        <span>样本越均衡，推荐和匹配结果越稳定</span>
      </div>
      <el-table :data="rows" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="分类" />
        <el-table-column prop="job_count" label="岗位数量" width="140" />
        <el-table-column label="占比" width="220">
          <template #default="{ row }">
            <el-progress :percentage="percent(row.job_count)" :stroke-width="8" />
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { adminApi } from '@/api'

const rows = ref([])
const pieEl = ref(null)
const barEl = ref(null)
const charts = []
const totalJobs = computed(() => rows.value.reduce((sum, item) => sum + Number(item.job_count || 0), 0))

function percent(value) {
  return totalJobs.value ? Math.round((Number(value || 0) / totalJobs.value) * 100) : 0
}

function mount(el, option) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function render() {
  charts.splice(0).forEach((chart) => chart.dispose())
  mount(pieEl.value, {
    color: ['#7F8FA3', '#A5B5B2', '#C9B1B0', '#D9CEC2', '#78A083'],
    tooltip: {},
    series: [{ type: 'pie', radius: ['45%', '72%'], data: rows.value.map((item) => ({ name: item.name, value: item.job_count })) }],
  })
  mount(barEl.value, {
    color: ['#7F8FA3'],
    tooltip: {},
    grid: { left: 90, right: 18, top: 18, bottom: 28 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: rows.value.map((item) => item.name).reverse() },
    series: [{ type: 'bar', data: rows.value.map((item) => item.job_count).reverse(), barWidth: 12 }],
  })
}

onMounted(async () => {
  const data = await adminApi.categories()
  rows.value = data.list || data.categories || []
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
.page { display: grid; gap: 18px; }
.admin-hero,.panel {
  border-radius: 20px;
  padding: 24px;
  background: rgba(255,255,255,.68);
  box-shadow: 0 18px 54px rgba(79,88,102,.1);
  backdrop-filter: blur(24px);
}
.admin-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: center;
}
.admin-hero h1 { margin: 14px 0; font-size: 42px; }
.admin-hero p,.panel-head span { color: var(--muted); line-height: 1.8; }
.hero-number { width: 140px; height: 110px; border-radius: 18px; display: grid; place-items: center; background: rgba(255,255,255,.62); }
.hero-number strong { font-size: 34px; }
.hero-number span { color: var(--muted); }
.chart-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.panel h2 { margin: 0 0 14px; }
.panel-head { display:flex; justify-content:space-between; gap:12px; align-items:center; }
.chart { height: 340px; }
@media (max-width: 900px) { .chart-grid,.admin-hero { grid-template-columns: 1fr; display:grid; } }
</style>
