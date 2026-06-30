<template>
  <section class="page">
    <div class="summary-grid">
      <article><span>报告总数</span><strong>{{ total }}</strong></article>
      <article><span>岗位方向</span><strong>{{ jobCount }}</strong></article>
      <article><span>详细报告占比</span><strong>{{ detailedRate }}%</strong></article>
      <article><span>当前筛选</span><strong>{{ studentId || '全部' }}</strong></article>
    </div>

    <div class="chart-grid">
      <section class="panel">
        <div class="panel-head"><h2>热门报告方向</h2><span>看学生最关注哪些岗位</span></div>
        <div ref="jobEl" class="chart"></div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>内容质量</h2><span>过短报告需要重点复查</span></div>
        <div ref="lengthEl" class="chart"></div>
      </section>
      <section class="panel wide">
        <div class="panel-head"><h2>生成趋势</h2><span>判断报告使用是否活跃</span></div>
        <div ref="dailyEl" class="chart small"></div>
      </section>
    </div>

    <GlassCard>
      <div class="head">
        <h1 class="section-title">报告管理</h1>
        <div class="toolbar">
          <el-input-number v-model="studentId" :min="0" placeholder="学生 ID" />
          <el-button type="primary" @click="load">筛选</el-button>
        </div>
      </div>
      <el-table :data="rows" stripe height="620">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="student_id" label="学生" width="100" />
        <el-table-column prop="job_name" label="岗位" />
        <el-table-column label="内容长度" width="140">
          <template #default="{ row }">{{ (row.content || '').length }} 字</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button text @click="view(row)">查看</el-button>
            <el-button text type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </GlassCard>
    <el-dialog v-model="dialog" title="报告详情" width="820px">
      <pre>{{ current.content }}</pre>
    </el-dialog>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { adminApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'

const rows = ref([])
const analytics = ref({})
const total = ref(0)
const studentId = ref(0)
const dialog = ref(false)
const current = ref({})
const jobEl = ref(null)
const lengthEl = ref(null)
const dailyEl = ref(null)
const charts = []
const jobCount = computed(() => (analytics.value.jobs || []).length)
const detailedRate = computed(() => {
  const rows = analytics.value.length || []
  const totalCount = rows.reduce((sum, item) => sum + Number(item.value || 0), 0)
  const detailed = rows.find((item) => item.name === '详细')?.value || 0
  return totalCount ? Math.round((Number(detailed) / totalCount) * 100) : 0
})

async function load() {
  const params = studentId.value ? { student_id: studentId.value, size: 50 } : { size: 50 }
  const data = await adminApi.reports(params)
  rows.value = data.items || []
  analytics.value = data.analytics || {}
  total.value = data.total || rows.value.length
  await nextTick()
  render()
}

async function view(row) {
  current.value = await adminApi.reportDetail(row.id)
  dialog.value = true
}

async function remove(id) {
  await adminApi.deleteReport(id)
  load()
}

function mount(el, option) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function render() {
  charts.splice(0).forEach((chart) => chart.dispose())
  const jobs = analytics.value.jobs || []
  const length = analytics.value.length || []
  const daily = (analytics.value.daily || []).slice().reverse()
  mount(jobEl.value, {
    color: ['#7F8FA3'],
    tooltip: {},
    grid: { left: 110, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: jobs.map((item) => item.name).reverse() },
    series: [{ type: 'bar', barWidth: 14, data: jobs.map((item) => item.value).reverse() }],
  })
  mount(lengthEl.value, {
    color: ['#C9B1B0', '#A5B5B2', '#7F8FA3'],
    tooltip: {},
    series: [{ type: 'pie', radius: ['45%', '72%'], data: length }],
  })
  mount(dailyEl.value, {
    color: ['#A5B5B2'],
    tooltip: {},
    grid: { left: 40, right: 20, top: 20, bottom: 36 },
    xAxis: { type: 'category', data: daily.map((item) => item.name) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, areaStyle: {}, data: daily.map((item) => item.value) }],
  })
}

onMounted(load)
onBeforeUnmount(() => charts.forEach((chart) => chart.dispose()))
</script>

<style scoped>
.page { display: grid; gap: 18px; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
.summary-grid article,.panel { border-radius:20px; padding:20px; background:rgba(255,255,255,.68); box-shadow:0 18px 54px rgba(79,88,102,.1); backdrop-filter:blur(24px); }
.summary-grid span,.panel-head span { color:var(--muted); }
.summary-grid strong { display:block; margin-top:8px; font-size:34px; }
.chart-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
.panel.wide { grid-column:1 / -1; }
.panel-head,.head,.toolbar { display:flex; justify-content:space-between; gap:16px; align-items:center; }
.panel-head h2 { margin:0; }
.chart { height:320px; }
.chart.small { height:240px; }
pre { white-space: pre-wrap; line-height: 1.8; }
@media (max-width: 920px) { .summary-grid,.chart-grid { grid-template-columns:1fr; } .panel.wide { grid-column:auto; } .head { align-items:flex-start; flex-direction:column; } }
</style>
