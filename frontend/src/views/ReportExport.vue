<template>
  <div class="report-export-page">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item" @click="$router.push('/')">首页</li>
            <li class="menu-item" @click="$router.push('/career-planning-intro')">职业规划</li>
            <li class="menu-item active" @click="$router.push('/report-export')">报告导出</li>
          </ul>
        </div>

        <div class="nav-right">
          <div class="nav-search-wrap">
            <input 
              type="text" 
              class="nav-search-input" 
              placeholder="搜索职业方向、专业、院校、岗位类型"
              @keyup.enter="handleSearch"
            >
            <button class="nav-search-btn" @click="handleSearch">搜索</button>
          </div>

          <button class="btn-toggle-theme" @click="toggleTheme">🌙</button>
          
          <button class="btn-login" @click="$router.push('/login')" v-if="!isLogin">登录</button>
          <button class="btn-register" @click="$router.push('/register')" v-if="!isLogin">注册</button>
          
          <div class="user-profile" v-if="isLogin">
            <img 
              :src="userAvatar || 'https://picsum.photos/seed/avatar/40/40'" 
              alt="用户头像" 
              class="avatar"
              @click="toggleUserMenu"
            >
            <div class="user-menu" v-show="isUserMenuOpen">
              <div class="menu-item" @click="$router.push('/profile')">个人中心</div>
              <div class="menu-item logout" @click="handleLogout">退出登录</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 子页面标题栏 -->
    <div class="test-subheader">
      <div class="subheader-wrap">
        <div class="page-title">
          <span class="title-icon">📄</span>
          <h1>报告导出中心</h1>
        </div>
        <div class="page-nav">
          <button class="report-btn" @click="showHistory = !showHistory">
            {{ showHistory ? '隐藏历史记录' : '📜 查看全部报告' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 页面主体内容 -->
    <div class="report-export">
      <!-- 报告列表（从三个接口加载） -->
      <div class="report-list-section" v-if="!showHistory">
        <h3 class="section-title">我的报告列表</h3>
        <div class="filter-row">
          <select v-model="filterType" class="filter-select">
            <option value="">全部类型</option>
            <option value="interest_test">兴趣测试报告</option>
            <option value="job_match">人岗匹配报告</option>
            <option value="career_plan">职业规划报告</option>
          </select>
          <input v-model="filterName" placeholder="搜索报告名称" class="filter-input" />
        </div>

        <div class="card-list">
          <div class="report-card" v-for="item in filteredReports" :key="item.id">
            <div class="card-tag" :class="item.type">{{ getTypeName(item.type) }}</div>
            <h4 class="card-title">{{ item.title }}</h4>
            <p class="card-time">生成时间：{{ item.created_at }}</p>
            <div class="card-actions">
              <button @click="loadReport(item)" class="btn btn-edit">编辑查看</button>
<button @click="quickExport(item)" class="btn btn-export">一键导出</button>
<button @click="deleteReportItem(item)" class="btn btn-delete">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 报告编辑与导出区 -->
      <div class="edit-section" v-if="currentReport">
        <div class="edit-header">
          <h3>✏️ 报告编辑与导出</h3>
          <div class="tool-buttons">
            <button class="tool-btn check" @click="checkContent">✅ 内容检查</button>
            <button class="tool-btn polish" @click="polishReport">✨ 智能润色</button>
            <button class="tool-btn reset" @click="resetContent">🔄 恢复原始</button>
          </div>
        </div>

        <div class="editor-box">
          <textarea v-model="editContent" class="report-editor" placeholder="报告内容"></textarea>
        </div>

        <div class="export-bar">
          <div class="left">
            <span>导出格式：</span>
            <select v-model="exportFormat">
              <option value="pdf">PDF</option>
              <option value="word">Word</option>
              <option value="md">Markdown</option>
            </select>
            <input v-model="currentReport.title" class="name-input" placeholder="报告名称" />
          </div>
          <div class="right">
            <button class="btn-save" @click="saveEdit">💾 保存修改</button>
            <button class="btn-export-final" @click="exportFinalReport">📤 导出报告</button>
          </div>
        </div>
      </div>

      <!-- 全部报告历史 -->
      <div class="history-section" v-if="showHistory">
        <h3 class="section-title">全部报告记录</h3>
        <table class="history-table">
          <thead>
            <tr>
              <th>报告名称</th>
              <th>类型</th>
              <th>生成时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in allReports" :key="item.id">
              <td>{{ item.title }}</td>
              <td>{{ getTypeName(item.type) }}</td>
              <td>{{ item.created_at }}</td>
              <td>
                <button class="mini-btn" @click="loadReport(item)">编辑</button>
<button class="mini-btn export" @click="quickExport(item)">导出</button>
<button class="mini-btn delete" @click="deleteReportItem(item)">删除</button>
              </td>
             </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 底部 -->
    <footer class="page-footer">
      <div class="footer-wrap">
        © 2026 大学生职业规划系统 | 职业规划报告导出中心
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import html2pdf from 'html2pdf.js'

const router = useRouter()

// 登录校验
const token = localStorage.getItem('token')
const studentId = localStorage.getItem('studentId')
const userId = localStorage.getItem('userId')

if (!token) {
  ElMessage.warning('请先登录')
  router.push('/login')
}

// 创建带token的axios实例
const authAxios = axios.create({
  baseURL: '/api',
  headers: {
    Authorization: 'Bearer ' + token
  }
})

// =============== 导航栏通用逻辑 ===============
const isLogin = ref(!!token)
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const darkMode = ref(localStorage.getItem('darkMode') === 'true')

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const handleLogout = () => {
  localStorage.clear()
  isLogin.value = false
  isUserMenuOpen.value = false
  router.push('/login')
  ElMessage.success('退出成功')
}

const applyTheme = () => {
  document.body.classList.toggle('dark', darkMode.value)
}
const toggleTheme = () => {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  applyTheme()
}

const goToFeature = (type) => {
  const map = {
    '测评': '/interest-test',
    '分析': '/ability-analysis',
    '规划': '/development-path',
    '导出': '/report-export'
  }
  router.push(map[type] || '/')
}

const handleSearch = () => {
  const ipt = document.querySelector('.nav-search-input')
  const k = ipt?.value?.trim()
  if (k) {
    router.push(`/search?keyword=${encodeURIComponent(k)}`)
    ipt.value = ''
    ElMessage.success('搜索中')
  } else ElMessage.warning('请输入关键词')
}

// =============== 从后端加载真实报告数据（使用三个新接口）===============
const allReports = ref([])

// 1. 加载职业规划报告（使用 /api/user/plans）
const loadCareerPlans = async () => {
  try {
    const { data } = await authAxios.get('/user/plans')
    if (!Array.isArray(data)) return []
    
    return data.map(item => ({
      id: `career_${item.id}`,
      title: item.title || `${item.targetJob} 职业规划报告`,
      type: 'career_plan',
      content: generateCareerPlanContent(item),
      created_at: item.createTime || new Date().toLocaleString(),
      originalId: item.id,
      originalType: 'career'
    }))
  } catch (e) {
    console.error('加载职业规划报告失败', e)
    return []
  }
}

// 生成职业规划报告内容
const generateCareerPlanContent = (item) => {
  return `
【职业生涯规划报告】

一、基本信息
目标岗位：${item.targetJob || '未指定'}
规划周期：${item.cycle || '1-3年'}
生成时间：${item.createTime || new Date().toLocaleString()}

二、发展规划
${item.content || '请通过职业规划功能生成详细报告'}

三、实施建议
• 定期复盘，每季度评估进展
• 持续学习，紧跟行业动态
• 积累项目经验，提升实战能力
`
}

// 2. 加载人岗匹配报告（使用 /api/user/match-reports）
const loadMatchReports = async () => {
  try {
    const { data } = await authAxios.get('/user/match-reports')
    if (!Array.isArray(data)) return []
    
    return data.map(item => ({
      id: `match_${item.id}`,
      title: item.title || `${item.targetJob} 匹配报告`,
      type: 'job_match',
      content: generateMatchReportContent(item),
      created_at: item.createTime || new Date().toLocaleString(),
      originalId: item.id,
      originalType: 'match',
      matchScore: item.score
    }))
  } catch (e) {
    console.error('加载人岗匹配报告失败', e)
    return []
  }
}

// 生成人岗匹配报告内容
const generateMatchReportContent = (item) => {
  return `
【人岗匹配分析报告】

一、基本信息
目标岗位：${item.targetJob || '未指定'}
综合匹配度：${item.score || 0}%
匹配等级：${item.result || '待评估'}
生成时间：${item.createTime || new Date().toLocaleString()}

二、匹配分析
${item.suggestion || '暂无详细分析'}

三、改进建议
• 针对薄弱环节制定学习计划
• 补充相关证书和项目经验
• 提升软能力和职业素养
`
}

// 3. 加载兴趣测评报告（使用 /api/user/interest-reports）
const loadInterestReports = async () => {
  try {
    const { data } = await authAxios.get('/user/interest-reports')
    if (!Array.isArray(data)) return []
    
    return data.map(item => ({
      id: `interest_${item.id}`,
      title: item.title || '霍兰德职业兴趣测评报告',
      type: 'interest_test',
      content: generateInterestReportContent(item),
      created_at: item.createTime || new Date().toLocaleString(),
      originalId: item.id,
      originalType: 'interest'
    }))
  } catch (e) {
    console.error('加载兴趣测评报告失败', e)
    return []
  }
}

// 生成兴趣测评报告内容
const generateInterestReportContent = (item) => {
  return `
【霍兰德职业兴趣测评报告】

一、测评结果
${item.result || '根据您的测评结果，建议关注以下职业方向'}

二、推荐岗位
${item.suitableJobs || '产品经理、人力资源、心理咨询师、市场营销、教育培训'}

三、发展建议
• 结合兴趣选择适合的职业方向
• 参加相关实践活动积累经验
• 持续探索和调整职业规划
`
}

// 统一加载所有报告（使用三个新接口）
const loadAllReports = async () => {
  try {
    const [careerPlans, matchReports, interestReports] = await Promise.all([
      loadCareerPlans(),
      loadMatchReports(),
      loadInterestReports()
    ])
    
    allReports.value = [...careerPlans, ...matchReports, ...interestReports]
    
    // 按时间倒序排序
    allReports.value.sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at)
    })
    
    if (allReports.value.length === 0) {
      ElMessage.info('暂无报告数据，请先去完成测评或规划')
    }
  } catch (e) {
    ElMessage.error('报告数据加载失败')
    console.error(e)
    allReports.value = []
  }
}

// =============== 状态 ===============
const showHistory = ref(false)
const currentReport = ref(null)
const editContent = ref('')
const originalContent = ref('')

const filterType = ref('')
const filterName = ref('')
const exportFormat = ref('pdf')

// =============== 计算属性 ===============
const filteredReports = computed(() => {
  let list = [...allReports.value]
  if (filterType.value) {
    list = list.filter(i => i.type === filterType.value)
  }
  if (filterName.value) {
    list = list.filter(i => i.title.includes(filterName.value))
  }
  return list
})

// =============== 方法 ===============
const getTypeName = (t) => {
  const map = {
    interest_test: '兴趣测试报告',
    job_match: '人岗匹配报告',
    career_plan: '职业规划报告'
  }
  return map[t] || '报告'
}

const loadReport = (item) => {
  currentReport.value = { ...item }
  editContent.value = item.content
  originalContent.value = item.content
}

const checkContent = () => {
  if (!editContent.value) {
    ElMessage.warning('无报告内容')
    return
  }
  const len = editContent.value.length
  const ok = /匹配|得分|建议|分析/.test(editContent.value)
  if(ok){
    ElMessage.success(`✅ 结构完整，${len}字`)
  }else{
    ElMessage.warning('⚠️ 结构不完整')
  }
}

const polishReport = () => {
  if (!editContent.value) return
  let t = editContent.value
    .replace(/、/g, '、 ')
    .replace(/\n+/g, '\n')
    .replace(/一、|二、|三、/g, '\n$&')
  editContent.value = t
  ElMessage.success('已优化排版')
}

const resetContent = () => {
  editContent.value = originalContent.value
  ElMessage.success('已恢复原始内容')
}

const saveEdit = () => {
  if (!currentReport.value) return
  const i = allReports.value.findIndex(x => x.id === currentReport.value.id)
  if (i > -1) {
    allReports.value[i].title = currentReport.value.title
    allReports.value[i].content = editContent.value
    ElMessage.success('保存成功')
  }
}

const quickExport = (item) => {
  loadReport(item)
  setTimeout(() => exportFinalReport(), 300)
}

// ====================== 删除报告 ======================
const deleteReportItem = async (item) => {
  try {
    let url = ''
    if (item.originalType === 'career') {
      url = `/user/report/career/${item.originalId}`
    } else if (item.originalType === 'match') {
      url = `/user/report/match/${item.originalId}`
    } else if (item.originalType === 'interest') {
      url = `/user/report/interest/${item.originalId}`
    }

    if (!url) return

    await authAxios.delete(url)
    ElMessage.success('删除成功')
    loadAllReports()
    currentReport.value = null
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// =============== 导出报告 ================
const exportFinalReport = async () => {
  if (!currentReport.value) return
  saveEdit()

  const title = currentReport.value.title
  const content = editContent.value
  const format = exportFormat.value

  try {
    if (format === 'pdf') {
      const html = `
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Microsoft Yahei; line-height:1.7; padding:30px; }
            h1 { color:#1890ff; border-left:4px solid #1890ff; padding-left:10px; }
            h2 { color:#2f54eb; margin-top:24px; }
            p { font-size:15px; color:#333; }
            table { border-collapse:collapse; width:100%; margin:16px 0; }
            th,td { border:1px solid #eee; padding:10px; }
            th { background:#f5f7fa; }
          </style>
        </head>
        <body>
          <h1>${escapeHtml(title)}</h1>
          ${content.replace(/\n/g, '<br>').replace(/\|/g, '｜')}
        </body>
        </html>
      `
      const opt = {
        margin: 10,
        filename: `${title}.pdf`,
        html2canvas: { scale: 2 },
        jsPDF: { format: 'a4' }
      }
      html2pdf().set(opt).from(html).save()
      ElMessage.success('PDF 导出成功')

    } else if (format === 'word') {
      const html = `
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Microsoft Yahei; line-height:1.7; padding:20px; }
            h1 { color:#2f54eb; }
            h2 { color:#1890ff; }
          </style>
        </head>
        <body>
          <h1>${escapeHtml(title)}</h1>
          ${content.replace(/\n/g, '<br>')}
        </body>
        </html>
      `
      const blob = new Blob([html], { type: 'application/msword' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${title}.doc`
      link.click()
      ElMessage.success('Word 导出成功')

    } else {
      const blob = new Blob([content], { type: 'text/markdown' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${title}.md`
      link.click()
      ElMessage.success('Markdown 导出成功')
    }

  } catch (err) {
    console.error(err)
    ElMessage.error('导出失败，请检查内容或重试')
  }
}

// HTML转义
const escapeHtml = (text) => {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

onMounted(() => {
  applyTheme()
  loadAllReports()
})
</script>
<style scoped>
/* 整体页面布局（和测评完全一致） */
.report-export-page {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  background: #f8f9fa;
  margin: 0;
  padding: 60px 0 0 0;
  color: #333;
}

/* 顶部导航 */
.top-nav {
  height: 60px;
  background: #fff;
  box-shadow: 0 1px 3 rgba(0, 0, 0, 0.1);
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
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
  color: #000;
}
.logo-icon {
  font-size: 24px;
  margin-right: 8px;
}
.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}
.menu-item {
  margin: 0 15px;
  font-size: 14px;
  cursor: pointer;
  padding: 0 5px;
  position: relative;
  height: 60px;
  line-height: 60px;
  color: #000;
}
.menu-item.active {
  color: #2f54eb;
}
.menu-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: #2f54eb;
}
.dropdown {
  position: relative;
}
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  width: 200px;
  background: #fff;
  box-shadow: 0 2px 8 rgba(0,0,0,0.1);
  border-radius: 4px;
  list-style: none;
  padding: 8px 0;
  margin: 0;
  display: none;
  z-index: 9999;
}
.dropdown:hover .dropdown-menu {
  display: block;
}
.dropdown-item {
  padding: 10px 15px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  height: auto;
  line-height: normal;
  color: #000;
}
.dropdown-item:hover, .dropdown-item.active {
  background: #f5f7fa;
  color: #2f54eb;
}
.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.color-dot.red { background: #ff7a45; }
.color-dot.orange { background: #faad14; }
.color-dot.green { background: #52c41a; }
.color-dot.blue { background: #1890ff; }

.nav-right {
  display: flex;
  gap: 15px;
  align-items: center;
}
.nav-search-wrap {
  display: flex;
  width: 200px;
  height: 24px;
}
.nav-search-input {
  flex: 1;
  height: 100%;
  padding: 0 10px;
  border: 1px solid #e8e8e8;
  border-radius: 4px 0 0 4px;
  outline: none;
  font-size: 12px;
}
.nav-search-btn {
  width: 53px;
  height: 100%;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  font-size: 12px;
}
.btn-toggle-theme {
  padding: 6px 10px;
  border: none;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  color: #000;
}
.btn-login {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #000;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.btn-register {
  padding: 6px 15px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
}

/* ========== 这里是修改的头像下拉菜单样式，和首页完全一致 ========== */
.user-profile {
  position: relative;
  display: flex;
  align-items: center;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid #f0f0f0;
}
.user-menu {
  position: absolute;
  top: 50px;
  right: 0;
  width: 120px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  border-radius: 4px;
  z-index: 9999;
}
.user-menu .menu-item {
  padding: 8px 15px;
  font-size: 14px;
  cursor: pointer;
  height: auto;
  line-height: normal;
  margin: 0;
  color: #000;
}
.user-menu .menu-item:hover {
  background: #f5f7fa;
}
.user-menu .logout {
  color: #ff4d4f;
  border-top: 1px solid #e8e8e8;
}

/* 子标题栏 */
.test-subheader {
  height: 70px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
}
.subheader-wrap {
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
.report-btn {
  padding: 6px 15px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 报告导出内容区 */
.report-export {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}

.section-title {
  font-size: 20px;
  margin-bottom: 18px;
}
.filter-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.filter-select, .filter-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

/* 卡片 */
.card-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}
.report-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  position: relative;
  box-shadow: 0 2px 8 rgba(0,0,0,0.06);
}
.card-tag {
  position: absolute;
  top: 14px;
  right: 16px;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;
  color: #fff;
}
.card-tag.interest_test { background: #4299e1; }
.card-tag.job_match { background: #00b42a; }
.card-tag.career_plan { background: #fa8c16; }
.card-title {
  font-size: 17px;
  margin: 0 0 6px 0;
}
.card-time {
  font-size: 13px;
  color: #999;
  margin: 0 0 14px 0;
}
.card-actions {
  display: flex;
  gap: 10px;
}
.btn {
  padding: 7px 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}
.btn-edit { background: #f5f7fa; color: #333; }
.btn-export { background: #2f54eb; color: #fff; }
.btn-delete {
  background: #ff4d4f;
  color: #fff;
}
/* 编辑区 */
.edit-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12 rgba(0,0,0,0.06);
  margin-bottom: 40px;
}
.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.tool-buttons {
  display: flex;
  gap: 10px;
}
.tool-btn {
  padding: 7px 12px;
  border-radius: 6px;
  border: none;
  font-size: 14px;
  cursor: pointer;
}
.tool-btn.check { background: #f6ffed; color: #00b42a; }
.tool-btn.polish { background: #fff7e6; color: #fa8c16; }
.tool-btn.reset { background: #f5f7fa; color: #666; }

.editor-box {
  margin-bottom: 20px;
}
.report-editor {
  width: 100%;
  min-height: 380px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  font-size: 15px;
  line-height: 1.6;
  box-sizing: border-box;
  resize: vertical;
  white-space: pre-line;
}

.mini-btn.delete {
  background: #fff1f0;
  color: #ff4d4f;
}
.export-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}
.left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.left select, .name-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
}
.name-input { width: 220px; }
.right {
  display: flex;
  gap: 12px;
}
.btn-save {
  padding: 9px 16px;
  background: #f5f7fa;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.btn-export-final {
  padding: 9px 16px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* 历史 */
.history-section {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 10 rgba(0,0,0,0.05);
}
.history-table {
  width: 100%;
  border-collapse: collapse;
}
.history-table th, .history-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}
.history-table th {
  background: #f8f9fa;
}
.mini-btn {
  padding: 4px 10px;
  border-radius: 4px;
  border: none;
  font-size: 12px;
  margin-right: 6px;
  cursor: pointer;
}
.mini-btn.export {
  background: #e6f7ff;
  color: #1890ff;
}

/* 底部 */
.page-footer {
  background: #fff;
  padding: 20px 0;
  border-top: 1px solid #e8e8e8;
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 40px;
}
.footer-wrap {
  width: 1200px;
  margin: 0 auto;
}

/* 响应式 */
@media (max-width: 1200px) {
  .nav-wrap, .subheader-wrap, .report-export {
    width: 90%;
  }
  .card-list {
    grid-template-columns: 1fr;
  }
}
</style>