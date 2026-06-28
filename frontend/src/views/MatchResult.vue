<template>
  <div class="job-match-container" :class="{ dark: darkMode }">
    <!-- 顶部导航栏（保持不变） -->
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
            <input 
              type="text" 
              class="nav-search-input" 
              placeholder="搜索职业方向、专业、院校、岗位类型"
              @keyup.enter="handleSearch"
              v-model="searchKeyword"
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

    <div class="main-content">
      <div class="guide-card">
        <div class="guide-content">
          <h3>精准匹配，规划职业方向</h3>
          <p>基于你的个人能力和职业偏好，智能分析你与目标岗位的匹配度，为职业规划提供数据支撑</p>
        </div>
      </div>

      <el-card class="card-item result-card" shadow="hover">
        <div class="result-header">
          <div class="job-title">
            <span>🎯 目标岗位：{{ jobName }}</span>
          </div>
          <div class="job-tags" v-if="debugInfo">
            <el-tooltip :content="`基础技能匹配: ${debugInfo.base_skill_sim}%`" placement="top">
              <el-tag size="small" type="info">技能匹配度 {{ matchResult.skillFit }}%</el-tag>
            </el-tooltip>
          </div>
        </div>

        <!-- 总分卡片（改进版） -->
        <div class="total-score-section">
          <div class="score-card">
            <h3>匹配度总评分</h3>
            <div class="score-value">
              <span class="big-number">{{ matchResult.totalScore }}</span>
              <span class="unit">分</span>
            </div>
            <div class="score-ring">
              <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="#e0e0e0" stroke-width="8"/>
                <circle cx="60" cy="60" r="52" fill="none" 
                  :stroke="getScoreLevelColor()" 
                  stroke-width="8"
                  :stroke-dasharray="2 * Math.PI * 52"
                  :stroke-dashoffset="2 * Math.PI * 52 * (1 - matchResult.totalScore / 100)"
                  stroke-linecap="round"
                  transform="rotate(-90 60 60)"
                  style="transition: stroke-dashoffset 0.8s ease"/>
                <text x="60" y="65" text-anchor="middle" font-size="20" font-weight="bold" :fill="getScoreLevelColor()">
                  {{ matchResult.totalScore }}
                </text>
              </svg>
            </div>
            <div class="score-level">
              <el-tag :style="{ backgroundColor: getScoreLevelColor(), color: '#ffffff', border: 'none', padding: '6px 16px', borderRadius: '20px', fontSize: '14px' }">
                {{ getScoreLevelText() }}
              </el-tag>
            </div>
          </div>

          <div class="match-suggestion">
            <div class="suggestion-header">
              <span>📋 AI 综合评估</span>
            </div>
            <p>{{ getMatchSuggestion() }}</p>
          </div>
        </div>

        <!-- 各维度匹配详情（改进版） -->
        <div class="dimension-section">
          <h4 class="section-title">📊 各维度匹配详情</h4>
          <el-table :data="matchResult.dimensionScores" border style="width: 100%;" stripe>
            <el-table-column prop="dimension" label="匹配维度" align="center" width="120">
              <template #default="scope">
                <span class="dimension-name">
                  {{ scope.row.dimension }}
                  <el-tooltip :content="getDimensionDesc(scope.row.dimension)" placement="top">
                    <span class="help-icon">ⓘ</span>
                  </el-tooltip>
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="匹配分数" align="center">
              <template #default="scope">
                <div class="star-rating">
                  <template v-for="i in 5" :key="i">
                    <span class="star" :class="{ active: i <= (scope.row.score / 20) }">★</span>
                  </template>
                  <span class="score-number">{{ scope.row.score }}分</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="权重" align="center" width="100">
              <template #default="scope">
                <div class="weight-badge">
                  {{ (scope.row.weight * 100).toFixed(0) }}%
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="contribution" label="加权得分" align="center" width="120">
              <template #default="scope">
                <span class="contribution-score">{{ scope.row.contribution }}分</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="匹配状态" align="center" width="100">
              <template #default="scope">
                <el-tag :style="getStatusStyle(scope.row.score)" class="status-tag">
                  {{ scope.row.score >= 80 ? '优秀' : (scope.row.score >= 60 ? '良好' : '待提升') }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 雷达图（更直观的可视化） -->
        <div class="chart-section">
          <h4 class="section-title">📈 匹配度可视化对比</h4>
          <div id="match-chart" style="width: 100%; height: 400px;"></div>
        </div>

        <!-- 差距分析与提升建议（改进版） -->
        <div class="gap-analysis-section">
          <h4 class="section-title">💡 差距分析与提升建议</h4>
          <el-collapse style="width: 100%;" accordion>
            <el-collapse-item name="1">
              <template #title>
                <div class="collapse-title">
                  <span class="collapse-icon">📜</span>
                  <span>基础要求差距</span>
                  <el-tag v-if="matchResult.dimensionScores[0]" size="small" :type="matchResult.dimensionScores[0].score >= 70 ? 'success' : 'warning'" style="margin-left: 12px">
                    {{ matchResult.dimensionScores[0]?.score || 0 }}分
                  </el-tag>
                </div>
              </template>
              <div class="gap-content">
                <div class="gap-text">{{ matchResult.gapAnalysis.base || '暂无建议' }}</div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="2">
              <template #title>
                <div class="collapse-title">
                  <span class="collapse-icon">💻</span>
                  <span>职业技能差距</span>
                  <el-tag v-if="matchResult.dimensionScores[1]" size="small" :type="matchResult.dimensionScores[1].score >= 70 ? 'success' : 'warning'" style="margin-left: 12px">
                    {{ matchResult.dimensionScores[1]?.score || 0 }}分
                  </el-tag>
                </div>
              </template>
              <div class="gap-content">
                <div class="gap-text">{{ matchResult.gapAnalysis.skills || '暂无建议' }}</div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="3">
              <template #title>
                <div class="collapse-title">
                  <span class="collapse-icon">🤝</span>
                  <span>职业素养差距</span>
                  <el-tag v-if="matchResult.dimensionScores[2]" size="small" :type="matchResult.dimensionScores[2].score >= 70 ? 'success' : 'warning'" style="margin-left: 12px">
                    {{ matchResult.dimensionScores[2]?.score || 0 }}分
                  </el-tag>
                </div>
              </template>
              <div class="gap-content">
                <div class="gap-text">{{ matchResult.gapAnalysis.quality || '暂无建议' }}</div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="4">
              <template #title>
                <div class="collapse-title">
                  <span class="collapse-icon">🚀</span>
                  <span>发展潜力差距</span>
                  <el-tag v-if="matchResult.dimensionScores[3]" size="small" :type="matchResult.dimensionScores[3].score >= 70 ? 'success' : 'warning'" style="margin-left: 12px">
                    {{ matchResult.dimensionScores[3]?.score || 0 }}分
                  </el-tag>
                </div>
              </template>
              <div class="gap-content">
                <div class="gap-text">{{ matchResult.gapAnalysis.potential || '暂无建议' }}</div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 推荐资源卡片 -->
        <div class="resource-section" v-if="matchResult.gapAnalysis.recommended_resources">
          <h4 class="section-title">📚 推荐学习资源</h4>
          <div class="resource-card">
            <p>{{ matchResult.gapAnalysis.recommended_resources }}</p>
          </div>
        </div>

        <div class="operation-btn-group">
          <el-button type="primary" @click="generateAndSaveReport" size="large">
            📄 生成生涯规划报告
          </el-button>
          <el-button @click="changeJob" size="large">
            🔄 更换岗位重新匹配
          </el-button>
          <el-button @click="exportResult" size="large">
            📎 导出匹配结果
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElLoading, ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import jsPDF from 'jspdf'

const router = useRouter()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const darkMode = ref(localStorage.getItem('darkMode') === 'true')
const searchKeyword = ref('')

const jobName = ref('软件工程师')
const debugInfo = ref(null)
const matchResult = ref({
  totalScore: 0,
  skillFit: 0,
  dimensionScores: [],
  gapAnalysis: { base: '', skills: '', quality: '', potential: '', recommended_resources: '' }
})

// 维度描述
const getDimensionDesc = (dimension) => {
  const desc = {
    '基础要求': '教育背景与岗位要求的匹配程度',
    '职业技能': '专业技能与岗位要求的匹配程度（权重最高）',
    '职业素养': '软能力（沟通、协作、抗压等）的匹配程度',
    '发展潜力': '实习经验、项目经验等展现的发展潜力'
  }
  return desc[dimension] || ''
}

// 获取状态样式
const getStatusStyle = (score) => {
  if (score >= 80) {
    return { backgroundColor: '#1989fa', color: '#ffffff', border: 'none' }
  } else if (score >= 60) {
    return { backgroundColor: '#409EFF', color: '#ffffff', border: 'none' }
  } else {
    return { backgroundColor: '#f56c6c', color: '#ffffff', border: 'none' }
  }
}

// 加载匹配数据
const loadProfileAndMatch = async () => {
  const loading = ElLoading.service({ text: 'AI 正在分析匹配度...', background: 'rgba(0,0,0,0.7)' })
  let loadingClosed = false
  const closeLoading = () => {
    if (!loadingClosed) {
      loading.close()
      loadingClosed = true
    }
  }

  try {
    const studentId = localStorage.getItem('studentId') || localStorage.getItem('userId')
    if (!studentId) throw new Error('请先登录')

    const job = localStorage.getItem('selectedJob')
    const selected = job ? JSON.parse(job) : { job_name: '软件工程师' }
    jobName.value = selected.job_name

    const response = await fetch('/api/match/match-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: Number(studentId), job_name: jobName.value })
    })
    if (!response.ok) throw new Error('请求失败')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i]
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'base') {
            const d = data.data
            const weights = d.weights || {
              "基础要求": 0.12,
              "职业技能": 0.50,
              "职业素养": 0.18,
              "发展潜力": 0.20
            }
            
            matchResult.value.totalScore = d.overall_score
            matchResult.value.skillFit = d.skill_fit
            debugInfo.value = d.debug_info
            
            matchResult.value.dimensionScores = [
              { dimension: '基础要求', score: d.education_score || 0, weight: weights["基础要求"], contribution: ((d.education_score || 0) * weights["基础要求"]).toFixed(1) },
              { dimension: '职业技能', score: d.skill_fit || 0, weight: weights["职业技能"], contribution: ((d.skill_fit || 0) * weights["职业技能"]).toFixed(1) },
              { dimension: '职业素养', score: 100 - (d.soft_gap || 0), weight: weights["职业素养"], contribution: ((100 - (d.soft_gap || 0)) * weights["职业素养"]).toFixed(1) },
              { dimension: '发展潜力', score: d.experience_score || 0, weight: weights["发展潜力"], contribution: ((d.experience_score || 0) * weights["发展潜力"]).toFixed(1) }
            ]
            
            closeLoading()
            nextTick(() => initMatchChart())
          } else if (data.type === 'gap') {
            matchResult.value.gapAnalysis[data.field] = data.text
          } else if (data.type === 'done') {
            ElMessage.success('匹配分析完成！')
            closeLoading()
          }
        }
      }
      buffer = lines[lines.length - 1]
    }
  } catch (err) {
    console.error(err)
    ElMessage.error(err.message || '获取匹配失败')
    closeLoading()
  } finally {
    closeLoading()
  }
}

// 生成报告
const generateAndSaveReport = async () => {
  try {
    const loading = ElLoading.service({ text: '正在生成报告...' })
    localStorage.setItem('lastMatchResult', JSON.stringify(matchResult.value))
    localStorage.setItem('lastMatchJob', jobName.value)
    setTimeout(() => {
      router.push('/career-planning')
      ElMessage.success('生涯规划报告生成成功！')
      loading.close()
    }, 800)
  } catch (e) {
    ElMessage.error('报告生成失败')
  }
}

// 用户菜单
const toggleUserMenu = () => { isUserMenuOpen.value = !isUserMenuOpen.value }
const handleLogout = () => {
  localStorage.clear()
  isLogin.value = false
  router.push('/')
  ElMessage.success('退出登录成功')
}

// 主题切换
const applyTheme = () => {
  if (darkMode.value) document.body.classList.add('dark')
  else document.body.classList.remove('dark')
}
const toggleTheme = () => {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  applyTheme()
  ElMessage.success(`已切换为${darkMode.value ? '暗黑' : '明亮'}模式`)
}

// 导航搜索
const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  router.push(`/search?keyword=${encodeURIComponent(keyword)}`)
  searchKeyword.value = ''
}

// 评分等级
const getScoreLevelColor = () => {
  if (matchResult.value.totalScore >= 85) return '#1989fa'
  if (matchResult.value.totalScore >= 70) return '#409EFF'
  if (matchResult.value.totalScore >= 60) return '#f59e0b'
  return '#f56c6c'
}
const getScoreLevelText = () => {
  if (matchResult.value.totalScore >= 85) return '高度匹配'
  if (matchResult.value.totalScore >= 70) return '较匹配'
  if (matchResult.value.totalScore >= 60) return '基本匹配'
  return '匹配度较低'
}
const getMatchSuggestion = () => {
  if (matchResult.value.totalScore > 0 && !matchResult.value.gapAnalysis?.base) {
    return '🤖 AI 正在生成详细建议...'
  }
  const base = matchResult.value.gapAnalysis?.base || ''
  if (matchResult.value.totalScore >= 80) {
    return `🎉 恭喜！你的综合匹配度较高。${base}`
  } else if (matchResult.value.totalScore >= 60) {
    return `💪 你的基础条件不错，还有提升空间。${base}`
  } else {
    return `📌 当前匹配度有待提升，以下是具体建议：${base}`
  }
}

// 导出 PDF
const exportResult = () => {
  try {
    const doc = new jsPDF()
    let yPos = 20
    doc.setFontSize(18)
    doc.text(`${jobName.value} 人岗匹配报告`, 14, yPos)
    yPos += 15
    doc.setFontSize(14)
    doc.text(`匹配总分：${matchResult.value.totalScore} 分`, 14, yPos)
    yPos += 10
    doc.text(`匹配等级：${getScoreLevelText()}`, 14, yPos)
    yPos += 15

    doc.setFontSize(14)
    doc.text('各维度匹配详情：', 14, yPos)
    yPos += 10
    doc.setFontSize(12)
    matchResult.value.dimensionScores.forEach(item => {
      if (yPos > 270) { doc.addPage(); yPos = 20 }
      const line = `${item.dimension}：${item.score} 分 | 权重 ${(item.weight * 100).toFixed(0)}% | 得分 ${item.contribution}`
      doc.text(line, 14, yPos)
      yPos += 8
    })
    yPos += 10
    if (yPos > 270) { doc.addPage(); yPos = 20 }
    doc.setFontSize(14)
    doc.text('差距分析与提升建议：', 14, yPos)
    yPos += 10
    doc.setFontSize(12)
    const gaps = matchResult.value.gapAnalysis
    const gapList = [
      { t: '基础要求', c: gaps.base || '无' },
      { t: '职业技能', c: gaps.skills || '无' },
      { t: '职业素养', c: gaps.quality || '无' },
      { t: '发展潜力', c: gaps.potential || '无' }
    ]
    gapList.forEach(g => {
      if (yPos > 270) { doc.addPage(); yPos = 20 }
      doc.text(`${g.t}：`, 14, yPos)
      const lines = doc.splitTextToSize(g.c, 170)
      doc.text(lines, 14, yPos + 7)
      yPos += lines.length * 7 + 5
    })
    doc.save(`${jobName.value}_人岗匹配报告.pdf`)
    ElMessage.success('PDF 导出成功！')
  } catch (e) {
    console.error('导出失败', e)
    ElMessage.error('导出失败')
  }
}

// 更换岗位
const changeJob = () => {
  router.push('/jobmatch-analysis')
}

// 图表
let chartInstance = null
let resizeListener = null

const initMatchChart = () => {
  const dom = document.getElementById('match-chart')
  if (!dom) return
  if (chartInstance) chartInstance.dispose()
  
  chartInstance = echarts.init(dom)
  const data = matchResult.value.dimensionScores || []
  
  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['你的匹配度', '岗位基准线'], bottom: 0, left: 'center' },
    grid: { left: '10%', right: '5%', top: '15%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: data.map(i => i.dimension), axisLabel: { fontSize: 12, fontWeight: 'bold' } },
    yAxis: { type: 'value', name: '匹配分数', max: 100, axisLabel: { formatter: '{value}分' } },
    series: [
      {
        name: '你的匹配度',
        type: 'bar',
        data: data.map(i => i.score),
        itemStyle: { borderRadius: [6, 6, 0, 0], color: '#409EFF' },
        label: { show: true, position: 'top', formatter: '{c}分', fontWeight: 'bold' }
      },
      {
        name: '岗位基准线',
        type: 'line',
        data: [75, 75, 75, 75],
        symbol: 'none',
        lineStyle: { color: '#f56c6c', width: 2, type: 'dashed' },
        label: { show: true, position: 'top', formatter: '基准线', color: '#f56c6c' }
      }
    ]
  }
  
  chartInstance.setOption(option)
  resizeListener = () => chartInstance?.resize()
  window.addEventListener('resize', resizeListener)
}

onUnmounted(() => {
  if (resizeListener) window.removeEventListener('resize', resizeListener)
  if (chartInstance) chartInstance.dispose()
})

onMounted(() => {
  applyTheme()
  if (!isLogin.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  loadProfileAndMatch()
})
</script>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.star-rating .star {
  font-size: 16px;
  color: #e4e7ed;
  transition: color 0.2s;
}

.star-rating .star.active {
  color: #f7ba2a;
}

.star-rating .score-number {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

/* 暗黑模式适配 */
.job-match-container.dark .star-rating .star {
  color: #4b5563;
}

.job-match-container.dark .star-rating .star.active {
  color: #fbbf24;
}

.job-match-container.dark .star-rating .score-number {
  color: #9ca3af;
}
.job-match-container {
  padding: 0;
  background-color: #fff;
  min-height: 100vh;
  width: 100%;
  box-sizing: border-box;
  transition: all 0.3s ease;
}
.job-match-container.dark {
  background: #0f172a !important;
  color: #f1f5f9;
}

/* ————————————————————————————————————————
   导航栏样式（与岗位选择页完全一致）
———————————————————————————————————————— */
.top-nav {
  height: 60px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  transition: all 0.3s ease;
}
.job-match-container.dark .top-nav {
  background: #1e293b;
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
.job-match-container.dark .logo {
  color: #f1f5f9;
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
  transition: color 0.3s ease;
}
.job-match-container.dark .menu-item {
  color: #f1f5f9;
}
.menu-item:hover {
  color: #2f54eb;
}
.menu-item.active {
  color: #2f54eb;
  font-weight: 500;
}
.menu-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: #2f54eb;
  transition: all 0.3s ease;
}

/* 下拉菜单 */
.dropdown {
  position: relative;
}
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  width: 200px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-radius: 4px;
  list-style: none;
  padding: 8px 0;
  margin: 0;
  display: none;
  z-index: 9999;
  transition: all 0.3s ease;
}
.job-match-container.dark .dropdown-menu {
  background: #334155;
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
  transition: background 0.3s ease;
}
.job-match-container.dark .dropdown-item {
  color: #f1f5f9;
}
.dropdown-item:hover {
  background: #f5f7fa;
  color: #2f54eb;
}
.job-match-container.dark .dropdown-item:hover {
  background: #475569;
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

/* 导航右侧 */
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
  transition: all 0.3s ease;
}
.job-match-container.dark .nav-search-input {
  background: #334155;
  border-color: #475569;
  color: #f1f5f9;
}
.nav-search-input:focus {
  border-color: #2f54eb;
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
  transition: background 0.3s ease;
}
.nav-search-btn:hover {
  background: #1d3ecf;
}

.btn-toggle-theme {
  padding: 6px 10px;
  border: none;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  color: #000;
  transition: all 0.3s ease;
}
.job-match-container.dark .btn-toggle-theme {
  background: #334155;
  color: #f1f5f9;
}
.btn-toggle-theme:hover {
  background: #e2e8f0;
}
.btn-login {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.job-match-container.dark .btn-login {
  background: transparent;
}
.btn-login:hover {
  background: #2f54eb;
  color: #fff;
}
.btn-register {
  padding: 6px 15px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s ease;
}
.btn-register:hover {
  background: #1d3ecf;
}

/* 用户头像菜单 */
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
  transition: border-color 0.3s ease;
}
.avatar:hover {
  border-color: #2f54eb;
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
.job-match-container.dark .user-menu {
  background: #334155;
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
.job-match-container.dark .user-menu .menu-item {
  color: #f1f5f9;
}
.user-menu .menu-item:hover {
  background: #f5f7fa;
  color: #2f54eb;
}
.job-match-container.dark .user-menu .menu-item:hover {
  background: #475569;
}
.user-menu .logout {
  color: #ff4d4f;
  border-top: 1px solid #e8e8e8;
}

/* ————————————————————————————————————————
   原有页面内容样式（保持不变）
———————————————————————————————————————— */
.main-content {
  padding-top: 60px;
}

.guide-card {
  background: #e8f4f8;
  padding: 16px 20px;
  border-radius: 0;
  border-bottom: 1px solid #d1e9f1;
}
.job-match-container.dark .guide-card {
  background: #1e293b;
  border-color: #334155;
}
.guide-content {
  max-width: 1200px;
  margin: 0 auto;
}
.guide-content h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 60;
}
.job-match-container.dark .guide-content h3 {
  color: #f1f5f9;
}
.guide-content p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}
.job-match-container.dark .guide-content p {
  color: #cbd5e1;
}

.card-item {
  border-radius: 0;
  border: none;
  background-color: #ffffff;
  margin-bottom: 0;
  overflow: hidden;
  transition: all 0.3s ease;
  max-width: 1200px;
  margin: 0 auto;
}
.job-match-container.dark .card-item {
  background: #1e293b;
}
.result-card {
  padding: 0;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e5e7eb;
}
.job-match-container.dark .result-header {
  background: #334155;
  border-color: #475569;
}
.job-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.job-match-container.dark .job-title {
  color: #f1f5f9;
}

.total-score-section {
  display: flex;
  flex-wrap: wrap;
  padding: 24px;
  gap: 24px;
  border-bottom: 1px solid #f0f0f0;
}
.job-match-container.dark .total-score-section {
  border-color: #475569;
}
.score-card {
  flex: 1;
  min-width: 280px;
  background: #e8f4f8;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
}
.job-match-container.dark .score-card {
  background: #334155;
}
.score-card h3 {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 16px;
  font-weight: 500;
}
.job-match-container.dark .score-card h3 {
  color: #cbd5e1;
}
.score-value {
  font-size: 48px;
  font-weight: 700;
  color: #409EFF;
  margin-bottom: 16px;
  line-height: 1;
}
.match-suggestion {
  flex: 2;
  min-width: 280px;
  padding: 24px;
  background-color: #f9f9f9;
  border-radius: 12px;
  display: flex;
  align-items: center;
}
.job-match-container.dark .match-suggestion {
  background: #334155;
}
.match-suggestion p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
  font-size: 15px;
}
.job-match-container.dark .match-suggestion p {
  color: #cbd5e1;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
  padding-left: 8px;
  border-left: 4px solid #409EFF;
}
.job-match-container.dark .section-title {
  color: #f1f5f9;
}

.dimension-section,
.chart-section,
.gap-analysis-section {
  padding: 24px;
  border-bottom: 1px solid #f0f0f0;
}
.job-match-container.dark .dimension-section,
.job-match-container.dark .chart-section,
.job-match-container.dark .gap-analysis-section {
  border-color: #475569;
}
.gap-analysis-section {
  border-bottom: none;
}
.gap-content {
  line-height: 1.8;
  color: #606266;
  padding: 12px 0;
  margin: 0;
  font-size: 14px;
}
.job-match-container.dark .gap-content {
  color: #cbd5e1;
}

.operation-btn-group {
  padding: 24px;
  text-align: center;
  background-color: #f9f9fa;
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  border-top: 1px solid #e5e7eb;
}
.job-match-container.dark .operation-btn-group {
  background: #334155;
  border-color: #475569;
}
.operation-btn-group .el-button {
  padding: 12px 30px;
  border-radius: 8px;
  font-size: 15px;
}

:deep(.el-table) {
  --el-table-header-text-color: #303133;
  --el-table-row-hover-bg-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.job-match-container.dark :deep(.el-table) {
  --el-table-header-text-color: #f1f5f9;
  --el-table-row-hover-bg-color: #475569;
  background: #334155;
  border-color: #475569;
}
:deep(.el-table td),
:deep(.el-table th) {
  text-align: center;
  padding: 12px 0;
  font-size: 14px;
  color: #606266;
  border-bottom: 1px solid #f0f0f0;
}
.job-match-container.dark :deep(.el-table td),
.job-match-container.dark :deep(.el-table th) {
  color: #cbd5e1;
  border-color: #475569;
}
:deep(.el-table th) {
  background-color: #f8f9fa;
  font-weight: 600;
}
.job-match-container.dark :deep(.el-table th) {
  background: #475569;
}

:deep(.el-collapse-item__header) {
  font-weight: 600;
  color: #303133;
  padding: 16px 20px;
  font-size: 15px;
  background-color: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}
.job-match-container.dark :deep(.el-collapse-item__header) {
  background: #334155;
  color: #f1f5f9;
  border-color: #475569;
}
:deep(.el-collapse-item__content) {
  padding: 20px;
  background-color: #ffffff;
  border: none;
}
.job-match-container.dark :deep(.el-collapse-item__content) {
  background: #334155;
}

@media (max-width: 768px) {
  .nav-menu { display: none; }
  .nav-wrap { width: 95%; }
  .main-content { padding-top: 60px; }
  .total-score-section { flex-direction: column; gap: 16px; }
  .score-card, .match-suggestion { min-width: 100%; }
  .operation-btn-group { flex-direction: column; align-items: center; }
  .operation-btn-group .el-button { width: 100%; margin: 8px 0; }
  .chart-section #match-chart { height: 300px !important; }
  .result-header { flex-direction: column; align-items: flex-start; gap: 12px; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>