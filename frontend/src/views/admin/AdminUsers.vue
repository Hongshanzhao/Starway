<template>
  <section class="page">
    <div class="summary-grid">
      <article>
        <span>总用户</span>
        <strong>{{ users.length }}</strong>
      </article>
      <article>
        <span>管理员占比</span>
        <strong>{{ adminRate }}%</strong>
      </article>
      <article>
        <span>画像完成覆盖</span>
        <strong>{{ profileRate }}%</strong>
      </article>
      <article>
        <span>启用账号</span>
        <strong>{{ activeCount }}</strong>
      </article>
    </div>

    <div class="chart-grid">
      <section class="panel">
        <div class="panel-head">
          <h2>角色结构</h2>
          <span>判断管理员与普通用户比例</span>
        </div>
        <div ref="roleEl" class="chart"></div>
      </section>
      <section class="panel">
        <div class="panel-head">
          <h2>账号状态</h2>
          <span>快速定位停用或异常账号</span>
        </div>
        <div ref="statusEl" class="chart"></div>
      </section>
      <section class="panel wide">
        <div class="panel-head">
          <h2>用户画像覆盖</h2>
          <span>画像越完整，推荐和报告越准确</span>
        </div>
        <div ref="profileEl" class="chart compact"></div>
      </section>
    </div>

    <GlassCard>
      <div class="head">
        <div>
          <h1 class="section-title">用户管理</h1>
          <p class="muted">先看结构和覆盖率，再处理角色、启用状态和异常账号。</p>
        </div>
        <el-input v-model="keyword" placeholder="搜索用户名/手机号/角色" class="search" />
      </div>
      <el-table :data="filtered" stripe height="620">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-select v-model="row.role" @change="update(row)">
              <el-option label="user" value="user" />
              <el-option label="admin" value="admin" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" :active-value="1" :inactive-value="0" @change="update(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </GlassCard>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { adminApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'

const users = ref([])
const analytics = ref({})
const keyword = ref('')
const roleEl = ref(null)
const statusEl = ref(null)
const profileEl = ref(null)
const charts = []

const filtered = computed(() => users.value.filter((row) => !keyword.value || JSON.stringify(row).includes(keyword.value)))
const adminCount = computed(() => users.value.filter((item) => item.role === 'admin').length)
const activeCount = computed(() => users.value.filter((item) => Number(item.is_active) === 1).length)
const adminRate = computed(() => users.value.length ? Math.round((adminCount.value / users.value.length) * 100) : 0)
const profileRate = computed(() => {
  const row = (analytics.value.profiles || []).find((item) => item.name === '已建画像')
  return users.value.length ? Math.round((Number(row?.value || 0) / users.value.length) * 100) : 0
})

async function load() {
  const data = await adminApi.users()
  users.value = data.users || []
  analytics.value = data.analytics || {}
  await nextTick()
  render()
}

async function update(row) {
  await adminApi.updateUser(row.id, { username: row.username, phone: row.phone, role: row.role, is_active: row.is_active })
  load()
}

async function remove(id) {
  await adminApi.deleteUser(id)
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
  const roles = analytics.value.roles || []
  const status = analytics.value.status || []
  const profiles = analytics.value.profiles || []
  mount(roleEl.value, {
    color: ['#7F8FA3', '#C9B1B0', '#A5B5B2'],
    tooltip: {},
    series: [{ type: 'pie', radius: ['48%', '72%'], data: roles }],
  })
  mount(statusEl.value, {
    color: ['#A5B5B2', '#C9B1B0'],
    tooltip: {},
    series: [{ type: 'pie', radius: ['48%', '72%'], data: status }],
  })
  mount(profileEl.value, {
    color: ['#7F8FA3'],
    tooltip: {},
    grid: { left: 80, right: 24, top: 20, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: profiles.map((item) => item.name).reverse() },
    series: [{ type: 'bar', barWidth: 18, data: profiles.map((item) => item.value).reverse() }],
  })
}

onMounted(load)
onBeforeUnmount(() => charts.forEach((chart) => chart.dispose()))
</script>

<style scoped>
.page { display: grid; gap: 18px; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
.summary-grid article,.panel {
  border-radius:20px;
  padding:20px;
  background:rgba(255,255,255,.68);
  box-shadow:0 18px 54px rgba(79,88,102,.1);
  backdrop-filter:blur(24px);
}
.summary-grid span,.panel-head span { color:var(--muted); }
.summary-grid strong { display:block; margin-top:8px; font-size:34px; }
.chart-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
.panel.wide { grid-column: 1 / -1; }
.panel-head,.head { display:flex; justify-content:space-between; gap:16px; align-items:center; }
.panel-head h2 { margin:0; }
.chart { height:300px; }
.chart.compact { height:240px; }
.head { margin-bottom:16px; }
.head p { margin:0; }
.search { max-width: 300px; }
@media (max-width: 920px) { .summary-grid,.chart-grid { grid-template-columns:1fr; } .panel.wide { grid-column:auto; } .head { align-items:flex-start; flex-direction:column; } }
</style>
