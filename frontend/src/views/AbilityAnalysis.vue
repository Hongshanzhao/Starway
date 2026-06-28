<template>
  <div class="ability-profile-page">
    <!-- 统一导航栏：与个人中心完全一致 -->
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item" @click="$router.push('/')">首页</li>
            <li class="menu-item active" @click="$router.push('/ability-analysis')">职业规划</li>
            <li class="menu-item" @click="$router.push('/report-export')">报告导出</li>
            <!-- <li class="menu-item" @click="$router.push('/about-us')">关于我们</li>
            <li class="menu-item dropdown">
              核心功能 ▼
              <ul class="dropdown-menu">
                <li class="dropdown-item" @click="goToFeature('测评')">
                  <span class="color-dot red"></span>
                  职业兴趣测评
                </li>
                <li class="dropdown-item" @click="goToFeature('分析')">
                  <span class="color-dot orange"></span>
                  能力短板分析
                </li>
                <li class="dropdown-item" @click="goToFeature('规划')">
                  <span class="color-dot green"></span>
                  发展路径规划
                </li>
                <li class="dropdown-item" @click="goToFeature('导出')">
                  <span class="color-dot blue"></span>
                  规划报告导出
                </li>
              </ul>
            </li> -->
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

          <button class="btn-toggle-theme" @click="toggleTheme">{{ darkMode ? '☀️' : '🌙' }}</button>
          
          <div class="user-profile">
            <img 
              :src="userAvatar || 'https://picsum.photos/seed/avatar/40/40'" 
              alt="用户头像" 
              class="avatar"
              @click="toggleUserMenu"
            >
            <div class="user-menu" v-show="isUserMenuOpen">
              <div class="menu-item" @click="$router.push('/profile')">个人中心</div>
              <!-- <div class="menu-item" @click="$router.push('/settings')">账号设置</div> -->
              <div class="menu-item logout" @click="handleLogout">退出登录</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="profile-container">
      <div class="step-content glass-panel">
        <h2 class="section-title">🤖 AI 学生就业能力画像</h2>

        <div v-if="generatingProfile" class="loading-container">
          <div class="loading-spinner">🔄</div>
          <p class="loading-text">AI 正在分析你的简历数据，生成多维度能力画像...</p>
        </div>

        <div v-else-if="profileGenerated" class="profile-result">
          <div class="basic-info-card card-effect">
            <div class="info-card-item">
              <span class="info-icon">👤</span>
              <span class="info-label">姓名</span>
              <span class="info-value">{{ profile.name || '未填写' }}</span>
            </div>
            <div class="info-card-divider"></div>
            <div class="info-card-item">
              <span class="info-icon">📞</span>
              <span class="info-label">联系方式</span>
              <span class="info-value">{{ profile.phone || '未填写' }} | {{ profile.email || '未填写' }}</span>
            </div>
            <div class="info-card-divider"></div>
            <div class="info-card-item">
              <span class="info-icon">📊</span>
              <span class="info-label">简历完整度</span>
              <span class="info-value">{{ profile.completeness }}%</span>
            </div>
          </div>

          <div class="core-scores">
            <div class="score-card card-effect">
              <span class="score-type">完整度评分</span>
              <span class="score-num">{{ profile.completeness }}%</span>
              <div class="score-bar">
                <div class="bar-fill" :style="{ width: profile.completeness + '%', background: getScoreColor(profile.completeness) }"></div>
              </div>
              <p class="score-desc">{{ getCompletenessDesc(profile.completeness) }}</p>
            </div>

            <div class="score-card card-effect">
              <span class="score-type">综合竞争力</span>
              <span class="score-num">{{ isCompetitiveScoreValid ? getCompetitiveScore() + '%' : '--' }}</span>
              <div class="score-bar">
                <div class="bar-fill" v-if="isCompetitiveScoreValid" :style="{ width: getCompetitiveScore() + '%', background: getScoreColor(getCompetitiveScore()) }"></div>
                <div v-else class="bar-empty"></div>
              </div>
              <p class="score-desc">{{ isCompetitiveScoreValid ? getCompetitiveDesc(getCompetitiveScore()) : '暂无足够简历信息评估综合竞争力' }}</p>
            </div>
          </div>

          <div class="dimension-scores">
            <h3 class="dimension-title">📊 软能力维度评分</h3>
            <div class="radar-chart-container card-effect">
              <div id="softAbilityRadarChart" class="radar-chart"></div>
            </div>
            <div class="dimension-grid">
              <div v-for="(item, key) in getSoftAbilityList()" :key="key" class="dimension-item card-effect">
                <div class="dimension-name">{{ key }}</div>
                <div class="dimension-bar">
                  <div class="bar-fill" :style="{ width: (item.score * 20) + '%', background: getScoreColor(item.score * 20) }"></div>
                </div>
                <div class="dimension-score">{{ item.score === 0 ? '--' : item.score * 20 }}分</div>
                <div class="dimension-tip">{{ item.description || '暂无评价' }}</div>
              </div>
            </div>
          </div>

          <div class="skill-cert-section">
            <div class="skill-card card-effect">
              <h3 class="skill-title">💻 专业技能</h3>
              <div class="tags">
                <span v-for="skill in profile.skills" :key="skill" class="tag skill-tag">
                  {{ skill }} <small>(熟练度{{ getSkillProficiency(skill) }}%)</small>
                </span>
                <span v-if="!profile.skills.length" class="empty-tag">暂无技能信息</span>
              </div>
            </div>
            <div class="cert-card card-effect">
              <h3 class="cert-title">📜 证书资质</h3>
              <div class="tags">
                <span v-for="cert in profile.certificates" :key="cert" class="tag cert-tag">
                  {{ cert }}
                </span>
                <span v-if="!profile.certificates.length" class="empty-tag">暂无证书信息</span>
              </div>
            </div>
          </div>

          <div class="experience-section">
            <div class="exp-card card-effect">
              <h3 class="exp-title">🎓 教育经历</h3>
              <div class="exp-content">
                <p v-if="profile.education_json.school">
                  {{ profile.education_json.school }} {{ profile.education_json.degree }} - {{ profile.education_json.major || '未填写专业' }}
                  <span v-if="profile.education_json.gpa"> | 绩点：{{ profile.education_json.gpa }}</span>
                  <span v-if="profile.education_json.ranking"> | 排名：{{ profile.education_json.ranking }}</span>
                </p>
                <p v-else>{{ profile.education_text || '暂无教育经历' }}</p>
              </div>
            </div>
            <div class="exp-card card-effect">
              <h3 class="exp-title">💼 工作/实习经历</h3>
              <div class="exp-content">
                <div v-if="profile.work_json.length">
                  <div v-for="(work, idx) in profile.work_json" :key="idx" class="work-item">
                    <p class="work-header">{{ work.company }} {{ work.position }} <span class="date-range">({{ work.date_range || '时间未填写' }})</span></p>
                    <p class="work-content">职责：{{ work.responsibilities || '未填写' }}</p>
                    <p class="work-achievements">成果：{{ work.achievements || '无' }}</p>
                    <hr v-if="idx < profile.work_json.length - 1" />
                  </div>
                </div>
                <p v-else>{{ profile.work_text || '暂无工作/实习经历' }}</p>
              </div>
            </div>
            <div class="exp-card card-effect">
              <h3 class="exp-title">📖 项目经历</h3>
              <div class="exp-content">
                <div v-if="profile.project_json.length">
                  <div v-for="(proj, idx) in profile.project_json" :key="idx" class="project-item">
                    <p class="project-header">{{ proj.project_name }} <span class="role">({{ proj.role || '参与者' }})</span></p>
                    <p class="project-tech">技术栈：{{ proj.technology_stack || '未填写' }}</p>
                    <p class="project-desc">描述：{{ proj.description || '未填写' }}</p>
                    <p class="project-outcome">成果：{{ proj.outcome || '无' }}</p>
                    <hr v-if="idx < profile.project_json.length - 1" />
                  </div>
                </div>
                <p v-else>{{ profile.project_text || '暂无项目经历' }}</p>
              </div>
            </div>
          </div>

          <div class="ai-evaluation card-effect">
            <h3 class="eval-title">📝 AI 综合能力评价</h3>
            <div class="eval-content">{{ profile.aiEvaluation }}</div>
          </div>

          <div class="profile-actions">
            <el-button class="btn-effect" @click="regenerateProfile" :loading="generatingProfile">重新生成画像</el-button>
            <el-button class="btn-effect" type="info" @click="goToEditInfo">重新填写学生信息</el-button>
            <el-button class="btn-effect" type="success" @click="goToInterestTest">兴趣测试</el-button>
          </div>
        </div>

        <div v-else class="empty-profile">
          <p class="empty-text">暂无能力画像数据，请先完成简历上传/手动录入</p>
          <el-button class="btn-effect" type="primary" @click="goBack">返回填写信息</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const darkMode = ref(localStorage.getItem('darkMode') === 'true')

const token = localStorage.getItem('token')
const userId = ref(localStorage.getItem('userId') || 3)
const studentId = ref(route.query.studentId || localStorage.getItem('studentId') || 1)

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  headers: { Authorization: token ? `Bearer ${token}` : '' },
  timeout: 30000
})

const generatingProfile = ref(false)
const profileGenerated = ref(false)
const profile = reactive({
  id: '', user_id: '', name: '', phone: '', email: '', completeness: 0,
  skills: [], certificates: [], soft_abilities: {},
  education_text: '', education_json: {}, work_text: '', work_json: [],
  project_text: '', project_json: [], aiEvaluation: ''
})

let radarChartInstance = null

const isCompetitiveScoreValid = computed(() => {
  const soft = getSoftAbilityList()
  return Object.values(soft).some(item => item.score > 0)
})

onMounted(() => {
  getProfileData()
})

watch(() => profile.soft_abilities, () => {
  if (profileGenerated.value) initRadarChart()
}, { deep: true })

const initRadarChart = () => {
  const chartDom = document.getElementById('softAbilityRadarChart')
  if (!chartDom) return setTimeout(() => initRadarChart(), 150)

  if (radarChartInstance) radarChartInstance.dispose()
  radarChartInstance = echarts.init(chartDom)

  const soft = getSoftAbilityList()
  const categories = Object.keys(soft)
  const values = Object.values(soft).map(i => i.score * 20)

  const option = {
    title: { text: '软能力维度分布', left: 'center', textStyle: { fontSize: 16, fontWeight: 600 } },
    tooltip: { trigger: 'item', formatter: '{b}: {c}分' },
    radar: {
      indicator: categories.map(name => ({ name, max: 100 })),
      shape: 'polygon', splitNumber: 5
    },
    series: [{
      name: '评分', type: 'radar',
      data: [{ value: values, areaStyle: { color: 'rgba(37,99,235,0.2)' } }]
    }]
  }
  radarChartInstance.setOption(option)
  window.addEventListener('resize', () => radarChartInstance?.resize())
}

const getProfileData = async () => {
  try {
    generatingProfile.value = true
    const res = await api.get(`/profile/${studentId.value}`)
    const data = res.data
    Object.assign(profile, data)
    profile.aiEvaluation = generateAIEvaluation(data)
    profileGenerated.value = true
    nextTick(() => initRadarChart())
  } catch (err) {
    console.error(err)
    ElMessage.error('获取画像失败：请先完善简历')
    profileGenerated.value = false
  } finally {
    generatingProfile.value = false
  }
}

const getSoftAbilityList = () => {
  const res = {}
  if (profile.soft_abilities && typeof profile.soft_abilities === 'object') {
    Object.entries(profile.soft_abilities).forEach(([k, v]) => {
      const score = typeof v === 'number' ? v : (v?.score || 0)
      res[k] = {
        score: Math.min(5, Math.max(0, score)),
        description: v?.description || (score === 0 ? '暂无信息评估' : 'AI已评估')
      }
    })
  }
  if (Object.keys(res).length === 0) {
    return {
      '创新能力': { score: 0, description: '暂无足够简历信息评估该能力' },
      '学习能力': { score: 0, description: '暂无足够简历信息评估该能力' },
      '抗压能力': { score: 0, description: '暂无足够简历信息评估该能力' },
      '沟通能力': { score: 0, description: '暂无足够简历信息评估该能力' },
      '实习能力': { score: 0, description: '暂无足够简历信息评估该能力' }
    }
  }
  return res
}

const generateAIEvaluation = (data) => {
  const skills = data.skills?.join('、') || '无'
  const certs = data.certificates?.join('、') || '无'
  const edu = data.education_text || '无'
  const work = data.work_text ? '有实习经历' : '无实习经历'
  const complete = data.completeness || 0

  let text = `简历完整度${complete}%，教育背景：${edu}。技能：${skills}；证书：${certs}。${work}。`
  const soft = getSoftAbilityList()
  const list = Object.entries(soft).sort((a, b) => b[1].score - a[1].score)
  const top = list[0], low = list.at(-1)

  if (top[1].score > 0) {
    text += `优势：${top[0]}(${top[1].score * 20}分)；待提升：${low[0]}。`
  } else {
    text += '当前信息不足，无法评估能力强弱，请补充完整简历。'
  }
  if (complete >= 80) text += '整体竞争力优秀。'
  else if (complete >= 60) text += '整体良好，补充实践更具优势。'
  else text += '信息偏少，建议优先补齐经历与技能。'
  return text
}

const regenerateProfile = async () => {
  try {
    await ElMessageBox.confirm('确定重新生成？', '提示', { type: 'warning' })
    await getProfileData()
    ElMessage.success('生成成功')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('生成失败')
  }
}

const exportProfile = async () => {
  ElMessage.warning('导出功能需后端实现 export 接口')
}

const getScoreColor = s => s >= 80 ? '#10b981' : s >= 60 ? '#f59e0b' : s >= 40 ? '#f97316' : '#ef4444'
const getCompletenessDesc = s => s >= 90 ? '极完整' : s >= 80 ? '优秀' : s >= 70 ? '良好' : s >= 60 ? '一般' : '偏低'
const getCompetitiveDesc = s => s >= 90 ? '极强' : s >= 80 ? '优秀' : s >= 70 ? '良好' : s >= 60 ? '一般' : '偏弱'
const getSkillProficiency = sk => ['Python', 'Java', 'SQL', 'Vue', 'Spring Boot'].includes(sk) ? 80 + Math.random() * 20 : 60 + Math.random() * 30
const getCompetitiveScore = () => {
  const soft = getSoftAbilityList()
  const avg = Object.values(soft).reduce((s, i) => s + i.score, 0) / Object.keys(soft).length * 20
  return Math.round(profile.completeness * 0.6 + avg * 0.4)
}

const goBack = () => router.push('/student-ability')
const goToEditInfo = () => router.push('/student-ability')
const goToInterestTest = () => router.push({ path: '/interest-test', query: { studentId: studentId.value } })
const toggleUserMenu = () => isUserMenuOpen.value = !isUserMenuOpen.value

const handleLogout = () => { 
  localStorage.clear(); 
  isLogin.value = false; 
  router.push('/'); 
  ElMessage.success('已退出') 
}

const toggleTheme = () => { 
  darkMode.value = !darkMode.value; 
  localStorage.setItem('darkMode', darkMode.value);
  document.body.classList.toggle('dark', darkMode.value)
}

const goToFeature = t => {
  const map = { '测评': '/interest-test', '分析': '/ability-analysis', '规划': '/development-path', '导出': '/report-export' }
  router.push(map[t] || '/')
}

const handleSearch = () => {
  const i = document.querySelector('.nav-search-input')
  if (i?.value.trim()) router.push(`/search?keyword=${encodeURIComponent(i.value.trim())}`)
}
</script>

<style scoped>
.ability-profile-page {
  width: 100%;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
  background: linear-gradient(145deg, #f9fafc 0%, #eef2f7 100%);
  margin: 0;
  padding: 60px 0 40px;
  color: #1a2639;
}

/* 统一导航栏样式 - 与个人中心完全一致 */
.top-nav {
  height: 60px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
  color: #000;
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
.dropdown-item:hover {
  background: #f5f7fa;
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

/* 原有页面样式保持不变 */
.profile-container {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}
.glass-panel {
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.7);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  padding: 40px;
  animation: fadeInUp 0.8s;
}
.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(37,99,235,0.1);
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
}
.section-title::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 80px;
  height: 2px;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
}

.card-effect {
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  border: double 1px transparent;
  background-image: linear-gradient(#fff, #fff), linear-gradient(135deg, #e0f2fe, #dbeafe);
  background-origin: border-box;
  background-clip: padding-box, border-box;
}
.card-effect:hover {
  transform: translateY(-5px) scale(1.01);
  box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}

.basic-info-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #f8fafc, #f0f9ff);
  border-radius: 16px;
  padding: 20px 30px;
  margin-bottom: 30px;
}
.info-card-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}
.info-icon { font-size: 18px; color: #2563eb; }
.info-label { font-weight: 600; color: #334155; font-size: 14px; }
.info-value { color: #1e293b; font-size: 15px; font-weight: 500; }
.info-card-divider { width: 1px; height: 30px; background: rgba(148,163,184,0.2); margin: 0 10px; }

.core-scores { display: flex; gap: 20px; margin-bottom: 35px; }
.score-card { flex: 1; background: #fff; border-radius: 16px; padding: 24px; }
.score-type { font-size: 15px; color: #64748b; margin-bottom: 10px; }
.score-num { font-size: 42px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
.score-bar { height: 10px; background: #f1f5f9; border-radius: 20px; overflow: hidden; margin-bottom: 10px; }
.bar-fill { height: 100%; border-radius: 20px; transition: width 1s; }
.bar-empty { height: 100%; background: #e2e8f0; border-radius: 20px; }
.score-desc { font-size: 14px; color: #64748b; line-height: 1.5; }

.dimension-title { font-size: 19px; font-weight: 600; color: #1e293b; margin-bottom: 20px; }
.radar-chart-container { width: 100%; height: 400px; margin-bottom: 30px; padding: 24px; border-radius: 16px; }
.radar-chart { width: 100%; height: 100%; }
.dimension-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 16px; margin-bottom: 35px; }
.dimension-item { background: #fff; border-radius: 12px; padding: 18px; }
.dimension-name { font-weight: 600; color: #1e293b; font-size: 15px; margin-bottom: 8px; }
.dimension-bar { height: 8px; background: #f1f5f9; border-radius: 20px; overflow: hidden; margin-bottom: 8px; }
.dimension-score { font-weight: 600; color: #1e293b; font-size: 14px; }
.dimension-tip { font-size: 12px; color: #94a3b8; font-style: italic; }

.skill-cert-section { display: flex; gap: 20px; margin-bottom: 35px; }
.skill-card, .cert-card { flex: 1; background: #fff; border-radius: 16px; padding: 24px; }
.skill-title, .cert-title { font-size: 17px; font-weight: 600; color: #1e293b; margin-bottom: 18px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { padding: 8px 16px; border-radius: 8px; font-size: 14px; transition: all 0.2s; }
.tag:hover { transform: translateY(-2px); }
.skill-tag { background: #eff6ff; color: #1e40af; border: 1px solid #dbeafe; }
.cert-tag { background: #f0fdf4; color: #166534; border: 1px solid #dcfce7; }
.empty-tag { color: #94a3b8; background: #f8fafc; border: 1px solid #e2e8f0; }

.experience-section { display: grid; grid-template-columns: repeat(auto-fill,minmax(320px,1fr)); gap: 20px; margin-bottom: 35px; }
.exp-card { background: #fff; border-radius: 16px; padding: 24px; }
.exp-title { font-size: 17px; font-weight: 600; color: #1e293b; margin-bottom: 18px; }
.exp-content { font-size: 14px; line-height: 1.6; color: #334155; }
.work-item, .project-item { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed rgba(148,163,184,0.1); }
.work-header, .project-header { font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.date-range, .role { font-size: 12px; color: #64748b; }
.work-achievements, .project-outcome { color: #0f766e; font-size: 13px; font-weight: 500; }

.ai-evaluation { background: #fff; border-radius: 16px; padding: 24px; margin-bottom: 30px; }
.eval-title { font-size: 17px; font-weight: 600; color: #1e293b; margin-bottom: 18px; }
.eval-content { font-size: 15px; line-height: 1.7; color: #334155; background: #f8fafc; padding: 16px; border-radius: 8px; border-left: 3px solid #2563eb; }

.profile-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
.btn-effect { position: relative; overflow: hidden; transition: all 0.3s ease !important; }
.btn-effect::after { content: ''; position: absolute; top:0; left:-100%; width:100%; height:100%; background: linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent); transition: left 0.6s; }
.btn-effect:hover::after { left:100%; }
:deep(.el-button) { border-radius: 8px !important; padding:10px 24px !important; font-weight:500 !important; }
:deep(.el-button--primary) { background: linear-gradient(135deg,#2563eb,#3b82f6) !important; border:none !important; }
:deep(.el-button--success) { background: linear-gradient(135deg,#10b981,#34d399) !important; border:none !important; }
:deep(.el-button--info) { background: linear-gradient(135deg,#64748b,#94a3b8) !important; border:none !important; color:#fff !important; }

.loading-container { display: flex; flex-direction: column; align-items: center; padding:60px 20px; }
.loading-spinner { font-size:48px; animation:spin 2s linear infinite; margin-bottom:20px; }
.loading-text { font-size:16px; color:#64748b; }
.empty-profile { display: flex; flex-direction: column; align-items: center; padding:80px 20px; text-align:center; }
.empty-text { font-size:16px; color:#64748b; margin-bottom:24px; line-height:1.6; }

@keyframes fadeInUp {
  from { opacity:0; transform:translateY(20px); }
  to { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
  from { opacity:0; transform:translateY(10px); }
  to { opacity:1; transform:translateY(0); }
}
@keyframes spin {
  0% { transform:rotate(0deg); }
  100% { transform:rotate(360deg); }
}

@media(max-width:768px) {
  .basic-info-card { flex-direction: column; gap:15px; padding:20px; }
  .info-card-divider { width:80%; height:1px; margin:10px 0; }
  .core-scores { flex-direction: column; }
  .skill-cert-section { flex-direction: column; }
  .experience-section { grid-template-columns:1fr; }
  .dimension-grid { grid-template-columns:1fr; }
  .glass-panel { padding:24px; }
  .nav-menu { display: none; }
  .radar-chart-container { height:300px; }
}
</style>