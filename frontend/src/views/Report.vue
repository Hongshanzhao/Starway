<template>
  <div class="report-container">
    <!-- 页面头部 -->
    <el-page-header 
      content="职业生涯发展报告" 
      @back="$router.push('/')"
      style="margin-bottom: 20px;"
    ></el-page-header>
    
    <!-- 操作栏 -->
    <el-row style="margin: 20px 0;" justify="space-between" align="middle">
      <el-button 
        type="primary" 
        icon="Download" 
        @click="exportReport"
        size="large"
        style="border-radius: 8px;"
        :loading="exporting"
      >
        导出报告
      </el-button>
      
      <el-button 
        type="success" 
        icon="Refresh" 
        @click="refreshReport"
        size="large"
        style="border-radius: 8px;"
        :loading="refreshing"
      >
        智能润色报告
      </el-button>

      <el-button 
        type="warning" 
        icon="Edit" 
        @click="editReport"
        size="large"
        style="border-radius: 8px;"
      >
        手动编辑报告
      </el-button>
    </el-row>

    <!-- 报告内容卡片 -->
    <el-card shadow="hover" style="border-radius: 10px;" v-loading="loading">
      <div class="report-content" v-html="reportContent"></div>
    </el-card>

    <!-- 手动编辑弹窗 -->
    <el-dialog v-model="editVisible" title="手动编辑职业规划报告" width="80%">
      <el-input
        v-model="editContent"
        type="textarea"
        :rows="20"
        style="width: 100%; font-size: 14px;"
        placeholder="可在此处手动调整报告内容，支持HTML格式"
      ></el-input>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const exporting = ref(false)
const refreshing = ref(false)

const reportContent = ref('')
const editVisible = ref(false)
const editContent = ref('')

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

// 加载报告
const loadReport = async (reportId) => {
  if (!reportId) {
    ElMessage.error('报告ID不存在')
    router.push('/')
    return
  }
  loading.value = true
  try {
    const res = await fetch(`/api/report/${reportId}`, {
      headers: getHeaders()
    })
    if (!res.ok) throw new Error('获取报告失败')
    const data = await res.json()
    reportContent.value = data.content || ''
  } catch (error) {
    ElMessage.error('加载报告失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 导出报告
const exportReport = async () => {
  const reportId = route.query.id
  if (!reportId) return

  exporting.value = true
  try {
    const res = await fetch(`/api/report/${reportId}/download`, {
      headers: getHeaders()
    })
    if (!res.ok) throw new Error('导出失败')
    
    const blob = await res.blob()
    const disposition = res.headers.get('Content-Disposition')
    let filename = `report_${reportId}.html`
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    }
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  } finally {
    exporting.value = false
  }
}

// 智能润色报告
const refreshReport = async () => {
  const reportId = route.query.id
  if (!reportId) return

  ElMessage.info('大模型正在智能润色报告内容...')
  refreshing.value = true
  try {
    const infoRes = await fetch(`/api/report/${reportId}`, { headers: getHeaders() })
    if (!infoRes.ok) throw new Error('获取原报告失败')
    const report = await infoRes.json()
    
    const generateRes = await fetch('/api/report/generate', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title: report.title,
        type: report.type,
        format: 'html',
        modules: []
      })
    })
    if (!generateRes.ok) throw new Error('润色失败')
    const data = await generateRes.json()
    const newReportId = data.id
    router.replace({ query: { id: newReportId } })
    await loadReport(newReportId)
    ElMessage.success('报告润色成功！')
  } catch (error) {
    ElMessage.error('润色失败：' + error.message)
  } finally {
    refreshing.value = false
  }
}

// 手动编辑报告
const editReport = () => {
  editContent.value = reportContent.value
  editVisible.value = true
}

const saveEdit = () => {
  if (!editContent.value) {
    ElMessage.error('报告内容不能为空！')
    return
  }
  reportContent.value = editContent.value
  editVisible.value = false
  ElMessage.success('报告修改保存成功！')
}

onMounted(() => {
  const reportId = route.query.id
  if (!reportId) {
    ElMessage.error('缺少报告ID')
    router.push('/')
    return
  }
  loadReport(reportId)
})
</script>

<style scoped>
.report-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}
.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}
.report-content {
  padding: 10px;
}
.report-inner h2, .report-inner h3, .report-inner h4 {
  margin-top: 0;
}
</style>