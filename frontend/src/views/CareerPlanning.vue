<template>
  <div class="career-planning-page">
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item" @click="$router.push('/')">首页</li>
            <li class="menu-item active" @click="$router.push('/career-planning-intro')">职业规划</li>
            <li class="menu-item" @click="$router.push('/report-export')">报告导出</li>
          </ul>
        </div>
        <div class="nav-right">
          <div class="nav-search-wrap">
            <input type="text" class="nav-search-input" placeholder="搜索岗位详情..." @keyup.enter="handleSearch" />
            <button class="btn-toggle-theme" @click="toggleTheme">🌙</button>
            <button class="btn-login" @click="$router.push('/login')" v-if="!isLogin">登录</button>
            <button class="btn-register" @click="$router.push('/register')" v-if="!isLogin">注册</button>
            <div class="user-profile" v-if="isLogin">
              <img :src="userAvatar || 'https://picsum.photos/seed/avatar/40/40'" alt="头像" class="avatar" @click="toggleUserMenu" />
              <div class="user-menu" v-show="isUserMenuOpen">
                <div class="menu-item" @click="$router.push('/profile')">个人中心</div>
                <div class="menu-item logout" @click="handleLogout">退出登录</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="main-content">
      <div v-if="reportVisible" class="report-container">
        <el-card class="report-card" shadow="hover">
          <div class="report-header-bar">
            <div><b>目标岗位：</b> {{ targetJob || '前端开发工程师' }}</div>
            <div><b>生成时间：</b> {{ reportTime }}</div>
            <div class="right-btns">
              <el-button type="primary" @click="generateReport"> 🔄 重新生成 </el-button>
              <el-button type="warning" @click="exportReport"> 📥 导出PDF </el-button>
            </div>
          </div>

          <div class="report-content-section">
            <div class="section-title">
              <i class="icon">📊</i> 职业生涯发展报告
            </div>
            <div v-html="aiReportHtml"></div>
          </div>
        </el-card>
      </div>

      <div v-else class="loading-box">
        <el-loading-spinner />
        <p>AI 正在为你生成专业职业规划报告...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElLoading, ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import html2pdf from 'html2pdf.js'

const router = useRouter()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)

const reportVisible = ref(false)
const reportTime = ref('')
const targetJob = ref('')
const aiReportContent = ref('')
const currentReportId = ref(null)

// 核心：AI Markdown → 截图同款HTML（完全保留动态数据）
const aiReportHtml = computed(() => {
  let txt = aiReportContent.value || ''

  // 1. 按章节拆分（一、二、三、四、五、）
  const parts = txt.split(/(?=一、|二、|三、|四、五、)/)
  let html = ''

  parts.forEach(part => {
    if (!part.trim()) return

    // 2. 每个章节包成卡片
    html += '<div class="card-block">'

    let p = part
      // 3. 章节标题 → 截图同款蓝色左侧边框
      .replace(/^(一、|二、|三、|四、五、)(.+)$/gm, '<h2 class="chapter-title">$1$2</h2>')

      // 4. 表格渲染 → 1:1还原截图样式
      .replace(/(\|.*?\|\n)+/g, (tableStr) => {
        const lines = tableStr.trim().split('\n').filter(l => l.trim())
        if (lines.length < 2) return tableStr

        // 过滤掉Markdown分隔线（---）
        const realLines = lines.filter(l => !l.startsWith('| ---') && !l.includes('----'))
        if (realLines.length < 2) return tableStr

        // 解析表头和行
        const headers = realLines[0].split('|').map(i => i.trim()).filter(Boolean)
        const rows = realLines.slice(1).map(r => r.split('|').map(i => i.trim()).filter(Boolean))

        // 生成截图同款表格HTML
        let table = '<table class="standard-table"><thead><tr>'
        headers.forEach(h => table += `<th>${h}</th>`)
        table += '</tr></thead><tbody>'
        rows.forEach(r => {
          table += '<tr>'
          r.forEach(c => table += `<td>${c}</td>`)
          table += '</tr>'
        })
        table += '</tbody></table>'
        return table
      })

      // 5. 加粗 **xxx**
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

      // 6. 普通段落
      .replace(/^(.+)$/gm, (line) => {
        if (line.match(/<h|<table|^\s*$/)) return line
        return `<p class="text-paragraph">${line}</p>`
      })

    html += p
    html += '</div>'
  })

  return html
})

const getStudentId = () => {
  const id = localStorage.getItem('studentId') || localStorage.getItem('student_id')
  return id ? parseInt(id) : null
}

const fetchReportData = async () => {
  const loading = ElLoading.service({ text: 'AI 正在生成专属报告...' })
  let closed = false
  const closeLoading = () => {
    if (!closed) {
      loading.close()
      closed = true
    }
  }

  try {
    const studentId = getStudentId()
    if (!studentId) {
      ElMessage.error('未获取到学生信息，请重新登录')
      closeLoading()
      return
    }

    const response = await fetch('/api/report/generate-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, job_name: '' })
    })

    if (!response.ok) throw new Error('生成失败')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullContent = ''
    let firstChunkReceived = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i]
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.chunk) {
            if (!firstChunkReceived) {
              firstChunkReceived = true
              // 收到第一个 chunk，立即关闭全屏 loading 并显示报告区域
              closeLoading()
              reportVisible.value = true
            }
            fullContent += data.chunk
            aiReportContent.value = fullContent
          } else if (data.done) {
            currentReportId.value = data.report_id
            reportTime.value = new Date().toLocaleString()
            ElMessage.success('报告生成并已自动保存！')
          }
        }
      }
      buffer = lines[lines.length - 1]
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('报告生成失败')
    closeLoading()
  }
}

const generateReport = () => {
  aiReportContent.value = ''
  reportVisible.value = false
  fetchReportData()
}

const exportReport = () => {
  if (!aiReportContent.value) {
    ElMessage.warning('暂无报告可导出')
    return
  }
  html2pdf().set({
    margin: 10,
    filename: `${targetJob.value}_职业规划报告.pdf`,
    html2canvas: { scale: 2 },
    jsPDF: { format: 'a4' }
  }).from(document.querySelector('.report-content-section')).save()
}

const toggleUserMenu = () => (isUserMenuOpen.value = !isUserMenuOpen.value)
const handleLogout = () => { localStorage.clear(); router.push('/'); ElMessage.success('退出成功') }
const handleSearch = () => ElMessage.warning('搜索功能开发中')
const toggleTheme = () => {}

onMounted(() => {
  fetchReportData()
})
</script>

<style scoped>
/* 页面全局样式 */
.career-planning-page {
  width: 100%;
  min-height: 100vh;
  background: #f5f7fa;
}

/* 顶部导航 */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  z-index: 9999;
}
.nav-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}
.nav-left {
  display: flex;
  align-items: center;
}
.logo {
  display: flex;
  align-items: center;
  margin-right: 40px;
  font-size: 18px;
  font-weight: bold;
}
.logo-icon {
  margin-right: 8px;
  font-size: 22px;
}
.nav-menu {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
}
.menu-item {
  margin: 0 16px;
  font-size: 14px;
  cursor: pointer;
  line-height: 60px;
  position: relative;
}
.menu-item.active {
  color: #409eff;
  font-weight: bold;
}
.menu-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: #409eff;
}

/* 右侧导航 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.nav-search-wrap {
  display: flex;
  width: 200px;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
}
.nav-search-input {
  flex: 1;
  padding: 0 10px;
  border: none;
  outline: none;
  font-size: 12px;
}
.btn-toggle-theme {
  padding: 4px 8px;
  border: none;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
}
.btn-login {
  padding: 6px 14px;
  border: 1px solid #409eff;
  color: #409eff;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.btn-register {
  padding: 6px 14px;
  border: none;
  color: #fff;
  background: #409eff;
  border-radius: 4px;
  cursor: pointer;
}
.user-profile {
  position: relative;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
}
.user-menu {
  position: absolute;
  top: 45px;
  right: 0;
  width: 130px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  border-radius: 8px;
  padding: 8px 0;
}
.user-menu .menu-item {
  padding: 10px 16px;
  font-size: 14px;
  cursor: pointer;
}
.user-menu .logout {
  color: #f56c6c;
  border-top: 1px solid #eee;
}

/* 主内容区 */
.main-content {
  padding-top: 70px;
  width: 1200px;
  margin: 0 auto;
  padding-bottom: 40px;
}
.report-container {
  width: 100%;
}
.report-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.report-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}
.right-btns {
  display: flex;
  gap: 10px;
}

/* 报告内容区 */
.report-content-section {
  padding: 30px;
  line-height: 1.8;
  background: #fff;
}
.section-title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #222;
  display: flex;
  align-items: center;
  gap: 8px;
}
.icon {
  color: #1890ff;
  font-size: 24px;
}

/* 🔥 卡片样式（和截图一致，简洁干净） */
.card-block {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
}

/* ✅ 表格样式（1:1还原截图） */
.report-content-section :deep(.standard-table) {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 16px 0 !important;
  background: #fff !important;
  border: 1px solid #e8e8e8 !important;
}
.report-content-section :deep(.standard-table thead th) {
  background: #f5f7fa !important;
  padding: 12px 16px !important;
  text-align: left !important;
  font-weight: bold !important;
  color: #333 !important;
  border: 1px solid #e8e8e8 !important;
}
.report-content-section :deep(.standard-table tbody td) {
  padding: 12px 16px !important;
  border: 1px solid #e8e8e8 !important;
  color: #444 !important;
  line-height: 1.6 !important;
}
.report-content-section :deep(.standard-table tbody tr:hover) {
  background: #fafbfc !important;
}

/* 章节标题（截图同款蓝色左侧边框） */
.chapter-title {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin: 0 0 16px;
  padding-left: 10px;
  border-left: 4px solid #1890ff;
}

/* 段落样式 */
.text-paragraph {
  font-size: 15px;
  color: #444;
  margin: 10px 0;
  text-align: justify;
  line-height: 1.8;
}

/* 加载样式 */
.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 12px;
  color: #666;
}
</style>