<template>
  <div class="job-match-page">
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

    <div class="match-container">
      <div class="page-header">
        <h1>岗位信息</h1>
      </div>

      <!-- 🔥 AI 真实推荐岗位 -->
      <div class="recommend-job-section">
        <h3>🎯 AI为你推荐的10个最佳匹配岗位</h3>
        <div v-if="recommendJobs.length === 0" class="loading-tip">
          <div>正在计算你的最佳匹配岗位...</div>
        </div>
        <div class="job-card-list" v-else>
          <div 
            class="job-card recommend-card" 
            v-for="(job,idx) in recommendJobs" 
            :key="job.job_name"
            :class="{ active: selectedJob.job_name === job.job_name }"
            @click="selectRecommendJob(job)"
            :style="getCardColor(idx)"
          >
            <h4 class="job-name">{{ job.job_name }}</h4>
            <div class="score-tag">{{ job.overall_score }}分</div>
          </div>
        </div>
      </div>

      <!-- 所有岗位 -->
      <div class="all-job-selection">
        <h3>所有岗位列表</h3>
        <div class="job-category-tabs">
          <div 
            class="tab-item" 
            :class="{ active: activeCategory === '全部岗位' }"
            @click="activeCategory = '全部岗位'"
          >
            全部岗位
          </div>
          <div 
            v-for="cat in categoryList" 
            :key="cat"
            class="tab-item"
            :class="{ active: activeCategory === cat }"
            @click="activeCategory = cat"
          >
            {{ cat }}
          </div>
        </div>
        <div class="search-wrap">
          <input 
            type="text" 
            v-model="allJobsSearchKeyword"
            placeholder="搜索所有岗位..." 
            class="all-jobs-search-input"
            @keyup.enter="handleAllJobsSearch"
          />
          <button class="all-jobs-search-btn" @click="handleAllJobsSearch">搜索</button>
        </div>

        <div class="job-card-list">
          <div 
            class="job-card" 
            v-for="(job,idx) in uniqueFilteredJobs" 
            :key="job.id"
            :class="{ active: selectedJob.id === job.id }"
            @click="selectJob(job)"
            :style="getCardColor(idx)"
          >
            <h4 class="job-name">{{ job.job_name }}</h4>
          </div>
        </div>
      </div>

      <div class="match-action-bar">
        <el-button type="primary" size="large" @click="startJobMatch">
          开始人岗匹配
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const darkMode = ref(localStorage.getItem('darkMode') === 'true')
const searchKeyword = ref('')

const hasAbilityProfile = ref(false)
const categoryList = ref([])
const activeCategory = ref('全部岗位')
const allJobs = ref([])
const allJobsSearchKeyword = ref('')
const selectedJob = ref({})

// 🔥 AI推荐岗位（空数组，完全靠接口返回）
const recommendJobs = ref([])

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const handleLogout = () => {
  localStorage.clear()
  isLogin.value = false
  router.push('/')
  ElMessage.success('退出登录成功')
}

function applyTheme() {
  if (darkMode.value) {
    document.body.classList.add('dark')
  } else {
    document.body.classList.remove('dark')
  }
}

const toggleTheme = () => {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  applyTheme()
  ElMessage.success(`已切换为${darkMode.value ? '暗黑' : '明亮'}模式`)
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  router.push(`/search?keyword=${encodeURIComponent(keyword)}`)
  searchKeyword.value = ''
  ElMessage.success(`正在搜索：${keyword}`)
}

const getCardColor = (index) => {
  const list = [
    'linear-gradient(135deg, #e0f7ff 0%, #f3fcff 100%)',
    'linear-gradient(135deg, #fff0f6 0%, #fff5f7 100%)',
    'linear-gradient(135deg, #f0f9ff 0%, #f7fcff 100%)',
    'linear-gradient(135deg, #fffbf0 0%, #fffcf5 100%)',
    'linear-gradient(135deg, #f6ffed 0%, #fafff0 100%)'
  ]
  return { background: list[index % list.length] }
}

// 🔥 从后端获取真实推荐岗位
const loadRecommendJobs = async () => {
  try {
    const studentId = localStorage.getItem('studentId') 
                   || localStorage.getItem('student_id') 
                   || localStorage.getItem('id')

    if (!studentId) {
      ElMessage.warning('请先登录并完善个人信息')
      return
    }

    const { data } = await axios.get('/api/match/recommend', {
      params: { student_id: studentId, limit: 10 }
    })

    if (data.results && data.results.length > 0) {
      recommendJobs.value = data.results
      ElMessage.success(`AI 为你匹配到 ${data.results.length} 个最佳岗位`)
    } else {
      ElMessage.warning('暂无匹配岗位，请完善个人信息')
    }
  } catch (err) {
    console.error('获取推荐失败：', err)
    ElMessage.error('推荐岗位加载失败')
  }
}

const loadAllJobsFromDB = async () => {
  try {
    const res = await axios.get('/api/jobs/search?page=1&size=9999')
    allJobs.value = res.data.items || []
  } catch (err) {
    console.error(err)
  }
}

const loadJobCategories = async () => {
  try {
    const res = await axios.get('/api/jobs/names')
    categoryList.value = res.data.slice(0, 40)
  } catch (err) {}
}

const filteredAllJobs = computed(() => {
  let list = allJobs.value
  if (activeCategory.value !== '全部岗位') {
    list = list.filter(job => job.job_name.includes(activeCategory.value))
  }
  if (allJobsSearchKeyword.value) {
    const kw = allJobsSearchKeyword.value.toLowerCase()
    list = list.filter(j => j.job_name?.toLowerCase().includes(kw))
  }
  return list
})

const uniqueFilteredJobs = computed(() => {
  const seen = new Set()
  return filteredAllJobs.value.filter(item => {
    if (!item.job_name) return false
    if (seen.has(item.job_name)) return false
    seen.add(item.job_name)
    return true
  })
})

// 选择普通岗位
const selectJob = (job) => {
  selectedJob.value = { ...job, source: 'all' }
  localStorage.setItem('selectedJob', JSON.stringify(job))
  ElMessage.success(`已选择：${job.job_name}`)
}

// 选择AI推荐岗位
const selectRecommendJob = (job) => {
  const fullJob = allJobs.value.find(j => j.job_name === job.job_name) || {
    id: 9999,
    job_name: job.job_name
  }
  selectedJob.value = { ...fullJob, source: 'recommend' }
  localStorage.setItem('selectedJob', JSON.stringify(fullJob))
  ElMessage.success(`已选择推荐岗位：${job.job_name}`)
}

const handleAllJobsSearch = () => {
  ElMessage.success(`找到 ${uniqueFilteredJobs.value.length} 个岗位`)
}

const startJobMatch = async () => {
  if (!selectedJob.value.id && !selectedJob.value.job_name) {
    ElMessage.warning('请先选择一个岗位')
    return
  }
  router.push({
    path: '/match-result',
    query: {
      jobId: selectedJob.value.id || 9999,
      jobName: selectedJob.value.job_name
    }
  })
}

onMounted(async () => {
  applyTheme()
  hasAbilityProfile.value = true
  await loadAllJobsFromDB()
  await loadJobCategories()
  await loadRecommendJobs()

  if (route.query.jobId) {
    const job = allJobs.value.find(j => j.id == route.query.jobId)
    if (job) selectJob(job)
  }
})
</script>

<style scoped>
.job-match-page {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  background: #ffffff;
  margin: 0;
  padding: 60px 0 0 0;
  color: #333;
  transition: all 0.3s ease;
}
.job-match-page.dark {
  background: #0f172a !important;
  color: #f1f5f9;
}

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
.job-match-page.dark .top-nav {
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
.job-match-page.dark .logo {
  color: #f1f5f9;
}
.logo-icon {
  font: 24px;
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
.job-match-page.dark .menu-item {
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
.job-match-page.dark .nav-search-input {
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
.job-match-page.dark .btn-toggle-theme {
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
.job-match-page.dark .btn-login {
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
.job-match-page.dark .user-menu {
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
.job-match-page.dark .user-menu .menu-item {
  color: #f1f5f9;
}
.user-menu .menu-item:hover {
  background: #f5f7fa;
  color: #2f54eb;
}
.job-match-page.dark .user-menu .menu-item:hover {
  background: #475569;
}
.user-menu .logout {
  color: #ff4d4f;
  border-top: 1px solid #e8e8e8;
}

.match-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.job-match-page.dark .match-container {
  color: #f1f5f9;
}
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; color: #1f2937; margin: 0; }
.job-match-page.dark .page-header h1 { color: #f1f5f9; }

.recommend-job-section {
  background: linear-gradient(135deg, #f0f7ff 0%, #f8fcff 100%);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 30px;
  border: 1px solid #d0e8ff;
}
.job-match-page.dark .recommend-job-section {
  background: #1e293b;
  border-color: #334155;
}
.recommend-job-section h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #2f54eb;
}
.job-match-page.dark .recommend-job-section h3 {
  color: #60a5fa;
}
.loading-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #666;
}
.recommend-card {
  position: relative;
  border: 2px solid #fff !important;
  box-shadow: 0 8px 20px rgba(47,84,235,0.1) !important;
}
.score-tag {
  position: absolute;
  top: 10px;
  right: 12px;
  background: #2f54eb;
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.all-job-selection {
  background: #f8f9ff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 40px;
}
.job-match-page.dark .all-job-selection { background: #1e293b; }
.all-job-selection h3 {
  font-size: 20px;
  font-weight: 600;
  border-bottom: 1px solid #e8e8e8;
  padding-bottom: 10px;
  margin-bottom: 20px;
}
.job-match-page.dark .all-job-selection h3 { color: #f1f5f9; border-color: #475569; }
.job-category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  max-height: 80px;
  overflow-y: auto;
}
.tab-item {
  padding: 6px 14px;
  border-radius: 20px;
  background: #f5f7fa;
  font-size: 14px;
  cursor: pointer;
  transition: 0.25s;
}
.job-match-page.dark .tab-item { background: #334155; color: #f1f5f9; }
.tab-item.active { background: #2f54eb; color: #fff; }
.tab-item:hover { background: #e0e8ff; }
.job-match-page.dark .tab-item:hover { background: #475569; }

.search-wrap {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.all-jobs-search-input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  outline: none;
}
.job-match-page.dark .all-jobs-search-input {
  background: #334155;
  border-color: #475569;
  color: #f1f5f9;
}
.all-jobs-search-btn {
  padding: 10px 20px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.job-card-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 18px;
}
.job-card {
  border-radius: 20px;
  padding: 32px 16px;
  height: 110px;
  box-shadow: 0 6px 16px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.35s ease;
  border: 1px solid #e8f3ff;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
}
.job-match-page.dark .job-card {
  background: #334155 !important;
  border-color: #475569;
}
.job-card:hover {
  transform: translateY(-7px);
  box-shadow: 0 12px 24px rgba(47,84,235,0.12);
  border-color: #b8d0ff;
}
.job-card.active {
  border: 2px solid #2f54eb !important;
  background: #e6f7ff !important;
}
.job-match-page.dark .job-card.active { background: #475569 !important; }
.job-card .job-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.5;
}
.job-match-page.dark .job-card .job-name { color: #f1f5f9; }

.match-action-bar {
  text-align: center;
  margin-top: 30px;
  margin-bottom: 60px;
}
.match-action-bar .el-button {
  padding: 12px 40px;
  font-size: 16px;
  border-radius: 10px;
}

@media (max-width: 768px) {
  .nav-menu { display: none; }
  .nav-wrap { width: 95%; }
  .job-card-list { grid-template-columns: repeat(2, 1fr); }
}
</style>