<template>
  <div class="report-generate">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-wrap">
        <div class="page-title">
          <span class="title-icon">📑</span>
          <h1>规划报告生成中心</h1>
        </div>
        <div class="page-nav">
          <button class="back-btn" @click="$router.push('/')">← 返回首页</button>
          <button class="history-btn" @click="showHistory = !showHistory">历史报告</button>
        </div>
      </div>
    </header>

    <!-- 历史报告弹窗 -->
    <div class="history-modal" v-show="showHistory">
      <div class="modal-mask" @click="showHistory = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>历史生成报告</h3>
          <button class="close-btn" @click="showHistory = false">×</button>
        </div>
        <div class="modal-body">
          <div class="history-empty" v-if="historyReports.length === 0">
            暂无历史报告，快去生成你的第一份报告吧！
          </div>
          <div class="history-list" v-else>
            <div class="history-item" v-for="item in historyReports" :key="item.id">
              <div class="history-title">{{ item.title }}</div>
              <div class="history-time">{{ formatDate(item.created_at) }}</div>
              <div class="history-actions">
                <button class="preview-btn" @click="previewHistoryReport(item)">预览</button>
                <button class="export-btn" @click="downloadReport(item.id)">导出</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 报告配置区 -->
    <section class="config-section">
      <div class="config-wrap">
        <div class="config-card">
          <div class="config-title">
            <span class="title-icon">⚙️</span>
            报告生成配置
          </div>
          <div class="config-content">
            <!-- 报告类型选择（动态从后端获取） -->
            <div class="config-item">
              <label class="config-label">报告类型：</label>
              <select class="config-select" v-model="selectedTypeId" @change="onTypeChange">
                <option v-for="type in reportTypes" :key="type.id" :value="type.id">
                  {{ type.name }}
                </option>
              </select>
            </div>

            <!-- 报告标题自定义 -->
            <div class="config-item">
              <label class="config-label">报告标题：</label>
              <input 
                type="text" 
                class="config-input" 
                v-model="reportConfig.title" 
                placeholder="请输入报告标题（默认：XX的职业规划报告）"
              >
            </div>

            <!-- 包含模块选择（动态从模板获取） -->
            <div class="config-item">
              <label class="config-label">包含模块：</label>
              <div class="module-group">
                <label class="module-item" v-for="module in reportModules" :key="module.key">
                  <input 
                    type="checkbox" 
                    v-model="module.checked"
                  >
                  <span class="module-text">{{ module.name }}</span>
                </label>
              </div>
            </div>

            <!-- 报告格式选择 -->
            <div class="config-item">
              <label class="config-label">导出格式：</label>
              <div class="format-group">
                <label class="format-item">
                  <input type="radio" v-model="reportConfig.format" value="pdf"> PDF（推荐）
                </label>
                <label class="format-item">
                  <input type="radio" v-model="reportConfig.format" value="word"> Word
                </label>
                <label class="format-item">
                  <input type="radio" v-model="reportConfig.format" value="txt"> 纯文本
                </label>
              </div>
            </div>

            <!-- 生成按钮 -->
            <div class="config-btn-group">
              <button class="generate-btn" @click="generateReport" :disabled="isGenerating">
                <span v-if="!isGenerating">生成报告</span>
                <span v-if="isGenerating">生成中... {{ generateProgress }}%</span>
              </button>
              <button class="reset-btn" @click="resetConfig">重置配置</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 报告预览区 -->
    <section class="preview-section" v-show="reportPreview">
      <div class="preview-wrap">
        <div class="preview-header">
          <h2>{{ reportConfig.title }}</h2>
          <div class="preview-actions">
            <button class="print-btn" @click="printReport">打印报告</button>
            <button class="export-btn" @click="exportCurrentReport">导出报告</button>
          </div>
        </div>

        <!-- 报告内容（直接显示后端生成的 HTML） -->
        <div class="preview-content" v-html="generatedContent" ref="previewRef"></div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="page-footer">
      <div class="footer-wrap">
        © 2026 大学生职业规划系统 | 专业报告 · 科学规划
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ---------- 状态 ----------
const showHistory = ref(false)
const isGenerating = ref(false)
const generateProgress = ref(0)
const reportPreview = ref(false)
const generatedContent = ref('') // 后端返回的报告内容（HTML）

// 报告类型列表（从后端获取）
const reportTypes = ref([])
const selectedTypeId = ref(null)

// 报告配置
const reportConfig = ref({
  title: '',
  format: 'pdf'
})

// 当前选中的报告类型对应的模块列表
const reportModules = ref([])

// 历史报告列表
const historyReports = ref([])

// ---------- 工具函数 ----------
const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${(d.getMonth()+1).toString().padStart(2,'0')}-${d.getDate().toString().padStart(2,'0')} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

// ---------- 数据获取 ----------
// 获取报告类型列表
const fetchReportTypes = async () => {
  try {
    const res = await fetch('/api/report/types')
    if (!res.ok) throw new Error('获取报告类型失败')
    const data = await res.json()
    reportTypes.value = data
    if (data.length > 0) {
      selectedTypeId.value = data[0].id
      await fetchReportTemplate(data[0].id)
    }
  } catch (error) {
    console.error(error)
    alert('加载报告类型失败')
  }
}

// 根据类型ID获取模板（模块列表）
const fetchReportTemplate = async (typeId) => {
  try {
    const res = await fetch(`/api/report/templates/${typeId}`)
    if (!res.ok) throw new Error('获取模板失败')
    const template = await res.json()
    reportModules.value = (template.modules || []).map(m => ({
      key: m.key,
      name: m.name,
      checked: m.default
    }))
    // 更新默认标题
    if (!reportConfig.value.title) {
      const type = reportTypes.value.find(t => t.id === typeId)
      reportConfig.value.title = `我的${type?.name || '职业规划'}报告`
    }
  } catch (error) {
    console.error(error)
    reportModules.value = []
  }
}

// 获取历史报告列表
const fetchHistoryReports = async () => {
  try {
    const res = await fetch('/api/report/history', { headers: getHeaders() })
    if (res.ok) {
      const data = await res.json()
      historyReports.value = data
    }
  } catch (error) {
    console.error('获取历史报告失败', error)
  }
}

// ---------- 事件处理 ----------
const onTypeChange = async () => {
  if (selectedTypeId.value) {
    await fetchReportTemplate(selectedTypeId.value)
  }
}

// 重置配置
const resetConfig = () => {
  selectedTypeId.value = reportTypes.value[0]?.id || null
  if (selectedTypeId.value) {
    fetchReportTemplate(selectedTypeId.value)
  }
  reportConfig.value.format = 'pdf'
  reportPreview.value = false
  generatedContent.value = ''
}

// 生成报告
const generateReport = async () => {
  if (!selectedTypeId.value) {
    alert('请选择报告类型')
    return
  }

  isGenerating.value = true
  generateProgress.value = 0

  // 收集选中的模块key
  const selectedModules = reportModules.value
    .filter(m => m.checked)
    .map(m => m.key)

  try {
    // 调用后端生成报告
    const res = await fetch('/api/report/generate', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title: reportConfig.value.title,
        type: selectedTypeId.value,
        format: reportConfig.value.format,
        modules: selectedModules
      })
    })
    if (!res.ok) throw new Error('生成报告失败')
    const data = await res.json()

    // 保存后端返回的报告内容（假设为 HTML）
    generatedContent.value = data.content

    // 模拟进度（可去掉，但为了体验保留）
    generateProgress.value = 100
    setTimeout(() => {
      isGenerating.value = false
      reportPreview.value = true

      // 刷新历史记录
      fetchHistoryReports()

      // 滚动到预览区
      document.querySelector('.preview-section')?.scrollIntoView({ behavior: 'smooth' })
    }, 500)
  } catch (error) {
    console.error(error)
    alert('生成报告失败：' + error.message)
    isGenerating.value = false
  }
}

// 下载报告（用于历史记录导出）
const downloadReport = async (reportId) => {
  try {
    const res = await fetch(`/api/report/${reportId}/download`, {
      headers: getHeaders()
    })
    if (!res.ok) throw new Error('下载失败')
    const blob = await res.blob()
    const disposition = res.headers.get('Content-Disposition')
    let filename = `report.${reportConfig.value.format}`
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    }
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error(error)
    alert('下载失败：' + error.message)
  }
}

// 导出当前报告（重新生成并下载）
const exportCurrentReport = async () => {
  if (!selectedTypeId.value) return
  isGenerating.value = true
  const selectedModules = reportModules.value.filter(m => m.checked).map(m => m.key)
  try {
    const res = await fetch('/api/report/generate', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title: reportConfig.value.title,
        type: selectedTypeId.value,
        format: reportConfig.value.format,
        modules: selectedModules
      })
    })
    const data = await res.json()
    await downloadReport(data.id)
  } catch (error) {
    alert('导出失败')
  } finally {
    isGenerating.value = false
  }
}

// 预览历史报告
const previewHistoryReport = (report) => {
  showHistory.value = false
  // 直接跳转到报告详情页（假设有 report-preview 路由，或者用弹窗显示）
  // 这里简单处理：跳转到预览页，并传递报告 ID
  router.push({
    path: '/report-preview',
    query: { id: report.id }
  })
}

// 打印报告
const printReport = () => {
  const previewContent = document.querySelector('.preview-content')
  if (previewContent) {
    const printWindow = window.open('', '_blank')
    printWindow.document.write(`
      <html>
        <head>
          <title>${reportConfig.value.title}</title>
          <style>
            body { font-family: "Microsoft Yahei", sans-serif; padding: 20px; }
            /* 保留原有打印样式，可自定义 */
          </style>
        </head>
        <body>
          ${previewContent.innerHTML}
        </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.print()
  }
}

// 初始化
onMounted(async () => {
  // 检查登录
  if (!localStorage.getItem('token')) {
    alert('请先登录')
    router.push('/login')
    return
  }

  // 获取报告类型和历史报告
  await Promise.all([
    fetchReportTypes(),
    fetchHistoryReports()
  ])
})
</script>

<style scoped>
/* 全局容器 */
.report-generate {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  background: #f8f9fa;
  margin: 0;
  padding: 0;
}

/* 页面头部 */
.page-header {
  height: 70px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  width: 100%;
}
.header-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}
.page-title {
  display: flex;
  align-items: center;
  color: #2f54eb;
}
.title-icon {
  font-size: 24px;
  margin-right: 8px;
}
.page-title h1 {
  font-size: 20px;
  margin: 0;
}
.page-nav {
  display: flex;
  gap: 10px;
}
.back-btn, .history-btn {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}

/* 历史报告弹窗 */
.history-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
}
.modal-mask {
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
}
.modal-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  margin: 0;
  color: #2f54eb;
}
.close-btn {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}
.modal-body {
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
}
.history-empty {
  text-align: center;
  padding: 40px 0;
  color: #999;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.history-item {
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history-title {
  font-weight: bold;
  flex: 1;
}
.history-time {
  font-size: 12px;
  color: #999;
  margin-right: 15px;
}
.history-actions {
  display: flex;
  gap: 10px;
}
.preview-btn {
  padding: 4px 10px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.export-btn {
  padding: 4px 10px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

/* 报告配置区 */
.config-section {
  padding: 40px 0;
}
.config-wrap {
  width: 1200px;
  margin: 0 auto;
}
.config-card {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.config-title {
  font-size: 20px;
  font-weight: bold;
  color: #2f54eb;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
.config-content {
  display: flex;
  flex-direction: column;
  gap: 25px;
}
.config-item {
  display: flex;
  align-items: flex-start;
}
.config-label {
  width: 120px;
  text-align: right;
  margin-right: 20px;
  font-weight: bold;
  padding-top: 5px;
}
.config-select, .config-input {
  flex: 1;
  height: 36px;
  padding: 0 10px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  outline: none;
  max-width: 400px;
}
.module-group {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}
.module-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 15px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
.module-item input {
  margin-right: 8px;
}
.module-item:has(input:checked) {
  border-color: #2f54eb;
  background: rgba(47, 84, 235, 0.1);
}
.module-item:has(input:disabled) {
  opacity: 0.5;
  cursor: not-allowed;
}
.module-tip {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}
.format-group {
  flex: 1;
  display: flex;
  gap: 20px;
}
.format-item {
  display: flex;
  align-items: center;
  cursor: pointer;
}
.format-item input {
  margin-right: 8px;
}
.config-btn-group {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}
.generate-btn {
  padding: 10px 30px;
  border: none;
  background: #2f54eb;
  color: #fff;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}
.generate-btn:disabled {
  background: #e8e8e8;
  cursor: not-allowed;
}
.reset-btn {
  padding: 10px 30px;
  border: 1px solid #e8e8e8;
  color: #666;
  background: #fff;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

/* 报告预览区 */
.preview-section {
  padding: 20px 0 40px;
}
.preview-wrap {
  width: 1200px;
  margin: 0 auto;
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e8e8e8;
}
.preview-header h2 {
  margin: 0;
  color: #2f54eb;
}
.preview-actions {
  display: flex;
  gap: 10px;
}
.print-btn {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.preview-content {
  font-size: 14px;
  line-height: 1.8;
}
.report-header {
  text-align: center;
  margin-bottom: 40px;
}
.report-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
}
.report-subtitle {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}
.report-line {
  height: 1px;
  background: #333;
  width: 80%;
  margin: 0 auto;
}
.report-module {
  margin-bottom: 40px;
}
.module-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
  border-left: 4px solid #2f54eb;
  padding-left: 10px;
}
.info-table {
  width: 100%;
  border-collapse: collapse;
}
.info-table td {
  border: 1px solid #e8e8e8;
  padding: 10px;
}
.table-label {
  font-weight: bold;
  width: 20%;
  background: #f8f9fa;
}
.plan-stage {
  margin-bottom: 20px;
}
.stage-title {
  font-weight: bold;
  margin-bottom: 8px;
}
.plan-empty, .ability-empty {
  color: #999;
  padding: 20px 0;
  text-align: center;
}
.ability-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.ability-item {
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}
.ability-dimension {
  font-weight: bold;
  margin-bottom: 8px;
}
.ability-score {
  margin-bottom: 8px;
}
.score-bar {
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
}
.score-fill {
  height: 100%;
  background: #2f54eb;
}
.ability-suggestion {
  font-size: 14px;
  color: #666;
}
.suggest-content, .summary-content {
  line-height: 1.8;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}
.report-footer {
  margin-top: 60px;
  text-align: center;
  font-size: 12px;
  color: #999;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}

/* 页脚 */
.page-footer {
  background: #fff;
  padding: 20px 0;
  border-top: 1px solid #e8e8e8;
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 20px;
}
.footer-wrap {
  width: 1200px;
  margin: 0 auto;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .header-wrap, .config-wrap, .preview-wrap, .footer-wrap {
    width: 90%;
  }
  .modal-content {
    width: 90%;
  }
}
@media (max-width: 768px) {
  .config-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .config-label {
    width: 100%;
    text-align: left;
    margin-bottom: 8px;
  }
  .module-group, .format-group {
    flex-direction: column;
    gap: 10px;
  }
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  .info-table td {
    display: block;
    width: 100%;
  }
}
</style>