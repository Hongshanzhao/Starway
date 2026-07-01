<template>
  <section class="page-shell page">
    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <div class="report-hero">
        <div>
          <el-tag effect="plain">Career Report</el-tag>
          <h1>{{ report.job_name }} 职业报告</h1>
          <p>{{ reportLead }}</p>
        </div>
        <div class="score-pill">
          <strong>{{ Math.round(insights.score || 0) }}%</strong>
          <span>综合匹配</span>
        </div>
      </div>

      <div class="dashboard-grid">
        <GlassCard class="metric-card">
          <div class="card-title-row">
            <h2>匹配指标</h2>
            <span>5 项能力面</span>
          </div>
          <div class="metric-summary">
            <div>
              <strong>{{ Math.round(insights.score || 0) }}%</strong>
              <span>综合匹配</span>
            </div>
            <p>{{ metricSummary }}</p>
          </div>
          <div class="metric-bars">
            <article v-for="item in metricItems" :key="item.name">
              <div>
                <strong>{{ item.name }}</strong>
                <span>{{ Math.round(Number(item.value || 0)) }}%</span>
              </div>
              <el-progress :percentage="Math.round(Number(item.value || 0))" :stroke-width="9" />
            </article>
          </div>
        </GlassCard>
        <GlassCard class="skill-card">
          <div class="card-title-row">
            <h2>技能缺口</h2>
            <span>{{ gapSummary }}</span>
          </div>
          <div class="gap-overview">
            <article>
              <strong>{{ (insights.matched_skills || []).length }}</strong>
              <span>已匹配</span>
            </article>
            <article>
              <strong>{{ (insights.missing_skills || []).length }}</strong>
              <span>待补齐</span>
            </article>
            <article>
              <strong>{{ (insights.required_skills || []).length }}</strong>
              <span>岗位高频</span>
            </article>
          </div>
          <div class="skill-box">
            <section>
              <span>已匹配</span>
              <div class="tag-list">
                <el-tag v-for="item in insights.matched_skills || []" :key="item" type="success">{{ item }}</el-tag>
                <p v-if="!insights.matched_skills?.length" class="muted">暂无明显匹配技能</p>
              </div>
            </section>
            <section>
              <span>优先补齐</span>
              <div class="tag-list">
                <el-tag v-for="item in insights.missing_skills || []" :key="item" type="warning">{{ item }}</el-tag>
                <p v-if="!insights.missing_skills?.length" class="muted">暂无明显缺口</p>
              </div>
            </section>
            <section>
              <span>岗位高频</span>
              <div class="tag-list compact">
                <el-tag v-for="item in (insights.required_skills || []).slice(0, 6)" :key="item" type="info">{{ item }}</el-tag>
                <p v-if="!insights.required_skills?.length" class="muted">暂无岗位高频技能</p>
              </div>
            </section>
          </div>
        </GlassCard>
        <GlassCard>
          <h2>行动准备度</h2>
          <div class="readiness-list">
            <article v-for="item in insights.readiness || []" :key="item.name">
              <div>
                <strong>{{ item.name }}</strong>
                <span>{{ item.value }}%</span>
              </div>
              <el-progress :percentage="Math.round(Number(item.value || 0))" :stroke-width="9" />
              <p>{{ item.text }}</p>
            </article>
          </div>
        </GlassCard>
        <GlassCard>
          <h2>90 天路线</h2>
          <div class="timeline">
            <article v-for="item in insights.timeline || []" :key="item.stage">
              <strong>{{ item.stage }}</strong>
              <p>{{ item.title }}</p>
              <span>{{ item.output }}</span>
            </article>
          </div>
        </GlassCard>
      </div>

      <div class="grid">
        <GlassCard class="report-editor">
          <div class="editor-head">
            <h2>报告正文</h2>
            <el-switch v-model="editMode" active-text="编辑" inactive-text="预览" />
          </div>
          <div v-if="!editMode" class="report-preview">{{ displayContent }}</div>
          <el-input v-else v-model="content" type="textarea" :rows="24" />
        </GlassCard>
        <GlassCard class="tools">
          <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
          <el-button :loading="polishing" @click="polishStream">流式智能润色</el-button>
          <el-button @click="restore">恢复原始版本</el-button>
          <el-button @click="exportVisualReport">导出可视化报告</el-button>
          <el-button @click="exportMarkdown">导出纯文本</el-button>
          <div class="stream-tip" v-if="polishing">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>AI 正在重写建议，内容会实时出现</span>
          </div>
        </GlassCard>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { reportApi } from '@/api'
import { streamRequest } from '@/api/http'
import { downloadBlob, plainTextFromMarkdown } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const route = useRoute()
const loading = ref(true)
const saving = ref(false)
const polishing = ref(false)
const report = ref({})
const insights = ref({})
const content = ref('')
const original = ref('')
const editMode = ref(false)

const displayContent = computed(() => plainTextFromMarkdown(content.value))
const metricItems = computed(() => {
  const items = insights.value.metrics || []
  if (items.length) return items
  return [
    { name: '技能匹配', value: 0 },
    { name: '方向匹配', value: 0 },
    { name: '学历基础', value: 0 },
    { name: '经历基础', value: 0 },
    { name: '软能力', value: 0 },
  ]
})
const metricSummary = computed(() => {
  const sorted = [...metricItems.value].sort((a, b) => Number(b.value || 0) - Number(a.value || 0))
  const top = sorted[0]
  const low = sorted[sorted.length - 1]
  if (!top || !low) return '暂无指标数据，生成报告后会自动补齐。'
  return `当前优势在${top.name}，下一步优先补${low.name}。`
})
const gapSummary = computed(() => {
  const missing = insights.value.missing_skills?.length || 0
  if (missing > 0) return `优先补齐 ${missing} 项`
  return '缺口较少，重点沉淀证据'
})
const reportLead = computed(() => {
  const missing = insights.value.missing_skills?.slice(0, 3).join('、')
  if (missing) return `当前最需要优先补齐：${missing}。报告已结合匹配数据生成行动路线。`
  return '当前画像与目标岗位已有一定重合，建议重点把项目和经历转化为可验证证据。'
})

async function save() {
  saving.value = true
  try {
    await reportApi.update(route.params.reportId, { content: content.value })
    original.value = content.value
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

async function polishStream() {
  const sourceText = content.value || original.value || displayContent.value
  if (!sourceText.trim()) {
    ElMessage.warning('当前报告内容为空，无法润色')
    return
  }
  polishing.value = true
  content.value = ''
  try {
    await streamRequest('/api/report/polish-stream', { content: sourceText, job_name: report.value.job_name }, (event) => {
      if (event.chunk) content.value += event.chunk
      if (event.done) content.value = plainTextFromMarkdown(content.value)
    })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    polishing.value = false
  }
}

function restore() {
  content.value = original.value
}

async function exportMarkdown() {
  const blob = await reportApi.exportMarkdown({ markdown: displayContent.value })
  downloadBlob(blob, `starway-report-${route.params.reportId}.txt`)
}

function exportVisualReport() {
  const metrics = insights.value.metrics || []
  const metricHtml = metrics.map((item) => `
    <div class="metric"><b>${escapeHtml(item.value ?? 0)}%</b><span>${escapeHtml(item.name)}</span><i style="width:${Math.max(0, Math.min(100, Number(item.value || 0)))}%"></i></div>
  `).join('')
  const readiness = (insights.value.readiness || []).map((item) => `
    <div class="ready"><div><b>${escapeHtml(item.name)}</b><strong>${escapeHtml(item.value)}%</strong></div><i style="width:${Math.max(0, Math.min(100, Number(item.value || 0)))}%"></i><p>${escapeHtml(item.text)}</p></div>
  `).join('')
  const matched = (insights.value.matched_skills || []).map((item) => `<span class="tag good">${escapeHtml(item)}</span>`).join('') || '<em>暂无明显匹配技能</em>'
  const missing = (insights.value.missing_skills || []).map((item) => `<span class="tag warn">${escapeHtml(item)}</span>`).join('') || '<em>暂无明显缺口</em>'
  const timeline = (insights.value.timeline || []).map((item) => `<li><b>${escapeHtml(item.stage)}</b><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.output)}</span></li>`).join('')
  const score = Math.round(insights.value.score || 0)
  const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>${escapeHtml(report.value.job_name)} 职业报告</title>
<style>
body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;color:#3c4148;background:#eef2ef;line-height:1.8}
.wrap{max-width:1120px;margin:28px auto;padding:0 24px}
.hero,.card{border-radius:18px;background:rgba(255,255,255,.86);box-shadow:0 18px 50px rgba(79,88,102,.12);padding:28px;margin-bottom:18px}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 150px;gap:24px;align-items:center;background:linear-gradient(135deg,#7f8fa3,#a5b5b2,#c9b1b0);color:white}
.score{width:132px;height:132px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(#fff ${score}%,rgba(255,255,255,.25) 0);color:#3c4148}.score span{width:98px;height:98px;border-radius:50%;display:grid;place-items:center;background:white;font-size:30px;font-weight:800}
h1{margin:0 0 10px;font-size:34px}h2{margin:0 0 16px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.metric,.ready{position:relative;overflow:hidden;border-radius:14px;background:#f7f9f8;padding:18px}.metric b{font-size:28px}.metric span{display:block;color:#747b82}.metric i,.ready i{display:block;height:8px;margin-top:12px;border-radius:99px;background:#7f8fa3}.ready div{display:flex;justify-content:space-between}.ready p{margin:8px 0 0;color:#747b82}.tag{display:inline-flex;margin:4px;padding:6px 10px;border-radius:99px}.good{background:#e5f1ea;color:#4f7c63}.warn{background:#f5ece1;color:#a96f32}li{margin:10px 0;padding:12px 14px;border-radius:12px;background:#f8faf9}li b,li strong,li span{display:block}.content{white-space:pre-wrap}.content p{margin:0}
@media print{body{background:white}.wrap{margin:0;max-width:none}.hero,.card{box-shadow:none;border:1px solid #dde3df}}
@media(max-width:760px){.hero,.two,.grid{grid-template-columns:1fr}}
</style></head><body><main class="wrap">
<section class="hero"><div><h1>${escapeHtml(report.value.job_name)} 职业报告</h1><p>${escapeHtml(reportLead.value)}</p></div><div class="score"><span>${score}%</span></div></section>
<section class="card"><h2>匹配指标</h2><div class="grid">${metricHtml}</div></section>
<section class="two"><div class="card"><h2>技能雷达</h2><p>已匹配：${matched}</p><p>优先补齐：${missing}</p></div><div class="card"><h2>行动准备度</h2>${readiness}</div></section>
<section class="card"><h2>90 天推进路线</h2><ol>${timeline}</ol></section>
<section class="card content"><h2>报告正文</h2><p>${escapeHtml(displayContent.value)}</p></section>
</main></body></html>`
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  downloadBlob(blob, `starway-visual-report-${route.params.reportId}.html`)
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]))
}

onMounted(async () => {
  try {
    report.value = await reportApi.detail(route.params.reportId)
    content.value = plainTextFromMarkdown(report.value.content || '')
    original.value = content.value
    insights.value = await reportApi.insights(route.params.reportId).catch(() => ({}))
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.report-hero {
  min-height: 220px;
  border-radius: 24px;
  padding: 30px;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: center;
  color: white;
  background: linear-gradient(135deg, rgba(127,143,163,.92), rgba(165,181,178,.84), rgba(201,177,176,.72));
  box-shadow: 0 24px 68px rgba(79,88,102,.16);
}

.report-hero h1 {
  margin: 14px 0;
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1.08;
}

.report-hero p {
  max-width: 640px;
  color: rgba(255,255,255,.86);
  line-height: 1.8;
}

.score-pill {
  width: 148px;
  height: 148px;
  border-radius: 32px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.22);
  backdrop-filter: blur(16px);
}

.score-pill strong {
  font-size: 38px;
}

.score-pill span {
  color: rgba(255,255,255,.82);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 18px;
}

.tools {
  display: grid;
  align-content: start;
  gap: 12px;
}

.tools :deep(.el-button) {
  margin: 0;
}

.report-editor {
  min-height: 640px;
}

.editor-head {
  margin-bottom: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

h2 {
  margin: 0 0 16px;
  font-weight: 600;
}

.report-preview {
  min-height: 560px;
  padding: 24px 28px;
  border-radius: 16px;
  color: #4f5862;
  background: rgba(255,255,255,.72);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.14);
  line-height: 1.95;
  white-space: pre-wrap;
}

.card-title-row {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.card-title-row h2 {
  margin: 0;
}

.card-title-row span {
  color: var(--muted);
  font-size: 13px;
  white-space: nowrap;
}

.metric-summary {
  min-height: 116px;
  margin-bottom: 14px;
  border-radius: 16px;
  padding: 18px;
  display: grid;
  align-content: center;
  gap: 10px;
  color: white;
  background: linear-gradient(135deg, rgba(127,143,163,.95), rgba(165,181,178,.86));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.22);
}

.metric-summary strong {
  display: block;
  font-size: 38px;
  line-height: 1;
}

.metric-summary span {
  display: block;
  margin-top: 6px;
  color: rgba(255,255,255,.78);
}

.metric-summary p {
  margin: 0;
  color: rgba(255,255,255,.86);
  line-height: 1.55;
}

.gap-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.gap-overview article {
  min-height: 74px;
  border-radius: 16px;
  padding: 12px;
  display: grid;
  align-content: center;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.gap-overview strong {
  color: #59616b;
  font-size: 24px;
  line-height: 1;
}

.gap-overview span {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
}

.skill-box,
.timeline,
.readiness-list,
.metric-bars {
  display: grid;
  gap: 12px;
}

.skill-box section,
.timeline article,
.readiness-list article,
.metric-bars article,
.stream-tip {
  border-radius: 16px;
  padding: 14px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-box span,
.timeline strong,
.readiness-list strong,
.metric-bars strong {
  display: inline-flex;
  margin-bottom: 8px;
  color: #68778a;
  font-weight: 700;
}

.metric-bars article div,
.readiness-list article div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.timeline p {
  margin: 0 0 8px;
  color: #4f5862;
}

.timeline span,
.readiness-list p,
.stream-tip span {
  color: var(--muted);
  line-height: 1.6;
}

.readiness-list p {
  margin: 8px 0 0;
}

.stream-tip {
  display: flex;
  gap: 8px;
  align-items: center;
}

@media (max-width: 1020px) {
  .dashboard-grid,
  .grid {
    grid-template-columns: 1fr;
  }

  .report-hero {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
