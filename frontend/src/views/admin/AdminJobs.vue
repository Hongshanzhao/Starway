<template>
  <section class="page">
    <div class="summary-grid">
      <article><span>岗位总数</span><strong>{{ total }}</strong></article>
      <article><span>覆盖行业</span><strong>{{ industryCount }}</strong></article>
      <article><span>覆盖城市</span><strong>{{ cityCount }}</strong></article>
      <article><span>画像字段完整度</span><strong>{{ qualityRate }}%</strong></article>
    </div>

    <div class="chart-grid">
      <section class="panel">
        <div class="panel-head"><h2>行业分布</h2><span>判断岗位库是否偏科</span></div>
        <div ref="industryEl" class="chart"></div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>城市热度</h2><span>辅助判断地域覆盖</span></div>
        <div ref="cityEl" class="chart"></div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>薪资区间</h2><span>帮助管理员发现异常薪资</span></div>
        <div ref="salaryEl" class="chart small"></div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>字段质量</h2><span>描述和技能越完整，AI 越稳</span></div>
        <div class="quality-list">
          <article v-for="item in qualityItems" :key="item.name">
            <strong>{{ item.name }}</strong>
            <el-progress :percentage="item.value" :stroke-width="9" />
          </article>
        </div>
      </section>
    </div>

    <GlassCard>
      <div class="head">
        <h1 class="section-title">岗位管理</h1>
        <div class="actions">
          <el-input
            v-model="keyword"
            clearable
            placeholder="搜索岗位/公司/行业/城市"
            class="search"
            @keyup.enter="search"
            @clear="search"
          />
          <el-button :loading="loading" @click="search">搜索</el-button>
          <el-button type="primary" @click="dialog = true">新增岗位</el-button>
        </div>
      </div>
      <el-table v-loading="loading" :data="rows" stripe height="620">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="job_name" label="岗位" min-width="180" />
        <el-table-column prop="company" label="公司" min-width="150" />
        <el-table-column prop="industry" label="行业" width="130" />
        <el-table-column prop="location" label="地点" width="120" />
        <el-table-column label="质量" width="160">
          <template #default="{ row }">
            <el-progress :percentage="rowQuality(row)" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230">
          <template #default="{ row }">
            <el-button text @click="edit(row)">编辑</el-button>
            <el-button text @click="showProfile(row)">画像</el-button>
            <el-button text type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <span>当前第 {{ page }} 页，每页 {{ size }} 条</span>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          background
          layout="prev, pager, next, sizes, jumper"
          :page-sizes="[20, 50, 100]"
          :total="total"
          @current-change="load"
          @size-change="handleSizeChange"
        />
      </div>
    </GlassCard>

    <el-dialog v-model="dialog" title="岗位信息" width="640px">
      <el-form :model="form" label-position="top">
        <el-form-item label="岗位名称"><el-input v-model="form.job_name" /></el-form-item>
        <el-form-item label="公司"><el-input v-model="form.company" /></el-form-item>
        <el-form-item label="行业"><el-input v-model="form.industry" /></el-form-item>
        <el-form-item label="地点"><el-input v-model="form.location" /></el-form-item>
        <el-form-item label="技能"><el-input v-model="form.skills" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.job_description" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="profileDialog" title="岗位画像" width="720px">
      <div class="tag-list"><el-tag v-for="item in profile.skills || []" :key="item">{{ item }}</el-tag></div>
      <RadarChart :items="softRows" title="软能力" />
    </el-dialog>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { adminApi, jobsApi } from '@/api'
import { softAbilityRows } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'
import RadarChart from '@/components/RadarChart.vue'

const rows = ref([])
const analytics = ref({})
const keyword = ref('')
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const dialog = ref(false)
const profileDialog = ref(false)
const profile = ref({})
const form = reactive({})
const industryEl = ref(null)
const cityEl = ref(null)
const salaryEl = ref(null)
const charts = []
let searchTimer = null

const industryCount = computed(() => analytics.value.summary?.industry_count || new Set(rows.value.map((row) => row.industry || row.job_category).filter(Boolean)).size)
const cityCount = computed(() => analytics.value.summary?.city_count || new Set(rows.value.map((row) => row.location || row.city).filter(Boolean)).size)
const softRows = computed(() => softAbilityRows(profile.value.soft_abilities))
const qualityItems = computed(() => {
  const q = analytics.value.quality || {}
  const total = Number(q.total || rows.value.length || 0)
  const percent = (value) => total ? Math.round((Number(value || 0) / total) * 100) : 0
  return [
    { name: '技能字段', value: percent(q.has_skills) },
    { name: '岗位描述', value: percent(q.has_description) },
    { name: '任职要求', value: percent(q.has_requirements) },
  ]
})
const qualityRate = computed(() => {
  const items = qualityItems.value
  return items.length ? Math.round(items.reduce((sum, item) => sum + item.value, 0) / items.length) : 0
})

async function load() {
  loading.value = true
  try {
    const data = await adminApi.jobs({
      page: page.value,
      size: size.value,
      keyword: keyword.value || undefined,
    })
    rows.value = data.list || []
    total.value = Number(data.total || rows.value.length || 0)
    analytics.value = data.analytics || {}
    await nextTick()
    render()
  } finally {
    loading.value = false
  }
}

function rowQuality(row) {
  if (row.quality_score !== undefined && row.quality_score !== null) {
    return Math.max(0, Math.min(100, Number(row.quality_score) || 0))
  }
  let score = 0
  if (row.skills) score += 34
  if ((row.job_description || '').length > 30) score += 33
  if ((row.requirements || '').length > 20) score += 33
  return score
}

function edit(row) {
  Object.assign(form, row)
  dialog.value = true
}

async function save() {
  if (form.id) await adminApi.updateJob(form.id, form)
  else await adminApi.addJob(form)
  dialog.value = false
  Object.keys(form).forEach((key) => delete form[key])
  load()
}

async function remove(id) {
  await adminApi.deleteJob(id)
  load()
}

function search() {
  page.value = 1
  load()
}

function handleSizeChange() {
  page.value = 1
  load()
}

async function showProfile(row) {
  profile.value = await jobsApi.profile(row.id)
  profileDialog.value = true
}

function mount(el, option) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function render() {
  charts.splice(0).forEach((chart) => chart.dispose())
  const industries = analytics.value.industries || []
  const cities = analytics.value.cities || []
  const salary = analytics.value.salary || []
  mount(industryEl.value, {
    color: ['#7F8FA3', '#A5B5B2', '#C9B1B0', '#D9CEC2', '#78A083'],
    tooltip: {},
    series: [{ type: 'pie', radius: ['46%', '72%'], data: industries }],
  })
  mount(cityEl.value, {
    color: ['#7F8FA3'],
    tooltip: {},
    grid: { left: 92, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: cities.map((item) => item.name).reverse() },
    series: [{ type: 'bar', barWidth: 14, data: cities.map((item) => item.value).reverse() }],
  })
  mount(salaryEl.value, {
    color: ['#C9B1B0'],
    tooltip: {},
    xAxis: { type: 'category', data: salary.map((item) => item.name) },
    yAxis: { type: 'value' },
    grid: { left: 40, right: 20, top: 22, bottom: 38 },
    series: [{ type: 'bar', barWidth: 20, data: salary.map((item) => item.value) }],
  })
}

onMounted(load)
watch(keyword, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(search, 380)
})
onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  charts.forEach((chart) => chart.dispose())
})
</script>

<style scoped>
.page { display: grid; gap: 18px; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
.summary-grid article,.panel { border-radius:20px; padding:20px; background:rgba(255,255,255,.68); box-shadow:0 18px 54px rgba(79,88,102,.1); backdrop-filter:blur(24px); }
.summary-grid span,.panel-head span { color:var(--muted); }
.summary-grid strong { display:block; margin-top:8px; font-size:34px; }
.chart-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
.panel-head,.head,.actions { display:flex; justify-content:space-between; gap:16px; align-items:center; }
.panel-head h2 { margin:0; }
.chart { height:320px; }
.chart.small { height:240px; }
.quality-list { display:grid; gap:18px; padding-top:16px; }
.quality-list strong { display:block; margin-bottom:8px; color:#59616b; }
.search { width: 280px; }
.pager { display:flex; justify-content:space-between; align-items:center; gap:16px; padding-top:18px; color:var(--muted); }
@media (max-width: 920px) { .summary-grid,.chart-grid { grid-template-columns:1fr; } .head,.actions { align-items:stretch; flex-direction:column; } .search { width:100%; } }
</style>
