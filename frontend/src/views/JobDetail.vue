<template>
  <div class="job-detail-page">
    <!-- 1. 顶部导航（保留原有逻辑） -->
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item" @click="$router.push('/')">首页</li>
            <li class="menu-item" @click="$router.push('/career-planning')">职业规划</li>
            <li class="menu-item" @click="$router.push('/report-export')">报告导出</li>
            <!-- <li class="menu-item" @click="$router.push('/about-us')">关于我们</li>
            <li class="menu-item dropdown">
              核心功能 ▼
              <ul class="dropdown-menu">
                <li class="dropdown-item" @click="goToFeature('测评')">
                  <span class="color-dot red"></span> 职业兴趣测评
                </li>
                <li class="dropdown-item" @click="goToFeature('分析')">
                  <span class="color-dot orange"></span> 能力短板分析
                </li>
                <li class="dropdown-item" @click="goToFeature('规划')">
                  <span class="color-dot green"></span> 发展路径规划
                </li>
                <li class="dropdown-item" @click="goToFeature('导出')">
                  <span class="color-dot blue"></span> 规划报告导出
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
              <!-- <div class="menu-item" @click="$router.push('/settings')">账号设置</div> -->
              <div class="menu-item logout" @click="handleLogout">退出登录</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 2. 岗位详情主体内容 -->
    <main class="job-detail-main">
      <div class="detail-container">
        <!-- 加载中提示 -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner">加载中...</div>
        </div>
        
        <!-- 数据加载失败提示 -->
        <div v-else-if="error" class="error-container">
          <div class="error-message">{{ error }}</div>
          <button class="reload-btn" @click="initJobData">重新加载</button>
        </div>
        
        <!-- 岗位详情内容 -->
        <div v-else>
          <!-- 面包屑导航 -->
          <div class="breadcrumb">
            <span @click="$router.push('/')">首页</span>
            <span class="separator">/</span>
            <span class="current">{{ jobDetail.job_name }}</span>
          </div>

          <!-- 顶部信息区：移除岗位标签卡片、岗位编码 -->
          <div class="job-top-section">
            <!-- 已删除：岗位封面图片 -->
            <div class="job-cover-wrap" style="display: none;"></div>
            
            <div class="job-info-wrap">
              <div class="job-header">
                <h1 class="job-title">{{ jobDetail.job_name }}</h1>
                <!-- 移除：蓝色岗位编码徽章 -->
              </div>
              
              <div class="job-tags">
                <span class="tag status">热招中</span>
                <span class="tag category">{{ jobDetail.industry }}</span>
                <span class="tag category">{{ jobDetail.company_type }}</span>
              </div>
              
              <div class="job-meta">
                <div class="meta-group">
                  <i class="meta-icon">💰</i>
                  <span class="meta-item">薪资范围：{{ jobDetail.salary_range || '面议' }}</span>
                </div>
                <!-- 移除：岗位编码展示 -->
                <div class="meta-group">
                  <i class="meta-icon">📅</i>
                  <span class="meta-item">最近更新：{{ jobDetail.updated_at || '未知' }}</span>
                </div>
                <div class="meta-group">
                  <i class="meta-icon">📍</i>
                  <span class="meta-item">工作地点：{{ jobDetail.location || '未知' }}</span>
                </div>
              </div>
              
              <div class="job-actions">
                <button class="btn-read" @click="goToJobProfile">
                  <i class="action-icon">📊</i> 查看岗位画像
                </button>
                <button class="btn-share" @click="handleShare">
                  <i class="action-icon">🔗</i> 分享
                </button>
              </div>
            </div>
            
            <div class="job-author-wrap">
              <!-- 已删除：企业头像图片 -->
              <div class="author-info">
                <div class="author-name">{{ jobDetail.company || '未知公司' }}</div>
                <div class="author-desc">{{ `${jobDetail.location || '未知地点'} | ${jobDetail.company_size || '未知规模'}` }}</div>
                <!-- 移除：公司星级评分 -->
              </div>
            </div>
          </div>

          <!-- 岗位详情和公司详情：断开卡片样式，重新布局 -->
          <div class="job-detail-content">
            <!-- 岗位详情：独立区域，不再是卡片式 -->
            <div class="job-description-section">
              <h2 class="section-title">
                <i class="section-icon">📋</i> 岗位详情
              </h2>
              
              <div class="section-content">
                <div v-if="jobDetail.job_description" class="description-content">
                  <!-- 保留数据库自带的1.2.3分点，处理<br>标签 -->
                  <div v-for="(item, index) in formatJobDescription()" :key="index" class="description-item">
                    {{ item }}
                  </div>
                </div>
                <div v-else class="empty-content">
                  <i class="empty-icon">📭</i>
                  <span class="empty-text">暂无岗位详情信息</span>
                </div>
              </div>
            </div>

            <!-- 公司详情：独立区域，段落形式，首行空两格 -->
            <div class="company-info-section">
              <h2 class="section-title">
                <i class="section-icon">🏢</i> 公司详情
              </h2>
              
              <div class="section-content">
                <div v-if="jobDetail.company_info" class="company-paragraph">
                  {{ jobDetail.company_info }}
                </div>
                <div v-else class="empty-content">
                  <i class="empty-icon">🏠</i>
                  <span class="empty-text">暂无公司详情信息</span>
                </div>
                
                <!-- 保留公司基本信息表格，但去掉多余样式 -->
                <div class="company-info-table">
                  <div class="table-row">
                    <div class="table-label">公司名称</div>
                    <div class="table-value">{{ jobDetail.company || '未知' }}</div>
                  </div>
                  <div class="table-row">
                    <div class="table-label">所属行业</div>
                    <div class="table-value">{{ jobDetail.industry || '未知' }}</div>
                  </div>
                  <div class="table-row">
                    <div class="table-label">公司规模</div>
                    <div class="table-value">{{ jobDetail.company_size || '未知' }}</div>
                  </div>
                  <div class="table-row">
                    <div class="table-label">公司类型</div>
                    <div class="table-value">{{ jobDetail.company_type || '未知' }}</div>
                  </div>
                  <div class="table-row">
                    <div class="table-label">工作地点</div>
                    <div class="table-value">{{ jobDetail.location || '未知' }}</div>
                  </div>
                  <div v-if="jobDetail.source_url" class="table-row">
                    <div class="table-label">岗位来源</div>
                    <div class="table-value">
                      <a :href="jobDetail.source_url" target="_blank" class="link-text">{{ jobDetail.source_url }}</a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 移除：职业发展路径整个模块 -->
        </div>
      </div>
    </main>

    <!-- 3. 页脚 -->
    <footer class="footer">
      <div class="footer-wrap">
        © 2026 大学生职业规划系统 | 助力大学生精准规划职业方向
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// ========== 导航栏相关逻辑（保留原有） ==========
const router = useRouter()
const route = useRoute()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)

watch(
  () => route.path,
  () => {
    isLogin.value = !!localStorage.getItem('token')
    userAvatar.value = localStorage.getItem('avatar') || ''
  },
  { immediate: true }
)

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('avatar')
  localStorage.removeItem('nickname')
  isLogin.value = false
  isUserMenuOpen.value = false
  router.push('/')
}

const darkMode = ref(localStorage.getItem('darkMode') === 'true')
function applyTheme() {
  if (darkMode.value) document.body.classList.add('dark')
  else document.body.classList.remove('dark')
}
function toggleTheme() {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  applyTheme()
}

const goToFeature = (type) => {
  switch(type) {
    case '测评':
      router.push('/interest-test')
      break
    case '分析':
      router.push('/ability-analysis')
      break
    case '规划':
      router.push('/development-path')
      break
    case '导出':
      router.push('/report-export')
      break
    default:
      break
  }
}

const handleSearch = () => {
  const searchInput = document.querySelector('.nav-search-input')
  const keyword = searchInput.value.trim()
  if (keyword) {
    router.push(`/search?keyword=${encodeURIComponent(keyword)}`)
    searchInput.value = ''
  }
}

// ========== API 配置 ==========
axios.defaults.baseURL = 'http://localhost:5000'
axios.defaults.timeout = 10000

// ========== 状态管理 ==========
const jobDetail = ref({})
const jobProfile = ref(null)
// 移除：职业发展路径相关变量
const loading = ref(true)
const error = ref('')

// ========== 工具函数 ==========
// 格式化岗位详情：处理<br>标签，保留原有分点，不自动加数字
const formatJobDescription = () => {
  if (!jobDetail.value.job_description) return []
  
  let text = jobDetail.value.job_description
  // 处理<br>标签：多个连续<br>替换为单个换行，单个<br>替换为换行
  text = text.replace(/<br\s*\/?>+/gi, '\n')
  // 按换行分割，保留原有分点格式
  let items = text.split('\n').filter(item => item.trim())
  
  // 去除空项和多余空格
  return items.map(item => item.trim()).filter(item => item)
}

// ========== API 调用函数 ==========
const fetchJobDetail = async (jobId) => {
  try {
    const response = await axios.get(`/api/jobs/${jobId}`)
    return response.data
  } catch (err) {
    throw new Error(`获取岗位详情失败：${err.message}`)
  }
}

const fetchJobProfile = async (jobId) => {
  try {
    const response = await axios.get(`/api/jobs/${jobId}/profile`)
    return response.data
  } catch (err) {
    console.warn('获取岗位画像失败:', err.message)
    return null
  }
}

// 移除：职业发展路径相关API调用函数

// ========== 初始化数据 ==========
const initJobData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const jobId = route.params.id || route.query.id
    
    if (!jobId) {
      throw new Error('未指定岗位ID')
    }
    
    // 1. 获取岗位基本详情
    const jobData = await fetchJobDetail(jobId)
    jobDetail.value = jobData
    
    // 2. 仅获取岗位画像，移除职业发展路径获取
    const profileData = await fetchJobProfile(jobId)
    if (profileData) {
      jobProfile.value = profileData
    }
    
  } catch (err) {
    error.value = err.message
    console.error('数据加载失败:', err)
  } finally {
    loading.value = false
  }
}

// ========== 交互方法 ==========
const goToJobProfile = () => {
  if (jobDetail.value.id) {
    router.push(`/job-portrait?jobId=${jobDetail.value.id}&jobName=${encodeURIComponent(jobDetail.value.job_name)}`)
    ElMessage.info('即将跳转到岗位画像详情页')
  } else {
    ElMessage.warning('岗位数据未加载完成')
  }
}

const handleShare = () => {
  if (jobDetail.value.source_url) {
    navigator.clipboard.writeText(jobDetail.value.source_url)
      .then(() => ElMessage.success('岗位链接已复制到剪贴板'))
      .catch(() => ElMessage.info(`岗位来源：${jobDetail.value.source_url}`))
  } else {
    const shareUrl = `${window.location.origin}/job-detail?id=${jobDetail.value.id}`
    navigator.clipboard.writeText(shareUrl)
      .then(() => ElMessage.success('岗位详情链接已复制到剪贴板'))
      .catch(() => ElMessage.info(`分享链接：${shareUrl}`))
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  applyTheme()
  initJobData()
  
  watch(
    () => [route.params.id, route.query.id],
    () => {
      initJobData()
    },
    { deep: true }
  )
})
</script>

<style scoped>
/* 全局容器 */
.job-detail-page {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  background: #f5f7fa;
  margin: 0;
  padding: 60px 0 0 0;
}

/* 加载中和错误提示样式 */
.loading-container, .error-container {
  text-align: center;
  padding: 80px 0;
  background: #fff;
  border-radius: 12px;
  margin: 20px 0;
}

.loading-spinner {
  font-size: 20px;
  color: #2f54eb;
  animation: spin 1.5s ease-in-out infinite;
  display: inline-block;
}

.error-message {
  font-size: 18px;
  color: #ff4d4f;
  margin-bottom: 24px;
}

.reload-btn {
  padding: 10px 24px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
}

.reload-btn:hover {
  background: #1d39c4;
  transform: translateY(-2px);
}

@keyframes spin {
  0% { opacity: 0.5; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
  100% { opacity: 0.5; transform: scale(0.9); }
}

/* ========== 顶部导航样式（保留原有） ========== */
.top-nav {
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
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
  transition: color 0.3s ease;
}
.menu-item:hover {
  color: #2f54eb;
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
  height: 3px;
  background: #2f54eb;
  border-radius: 3px 3px 0 0;
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
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  border-radius: 8px;
  list-style: none;
  padding: 8px 0;
  margin: 0;
  display: none;
  z-index: 9999;
}
.dropdown:hover .dropdown-menu {
  display: block;
  animation: fadeIn 0.3s ease;
}
.dropdown-item {
  padding: 12px 20px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  height: auto;
  line-height: normal;
  color: #333;
  transition: background 0.3s ease;
}
.dropdown-item:hover {
  background: #f0f7ff;
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
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  transition: border 0.3s ease;
}
.nav-search-wrap:focus-within {
  border-color: #2f54eb;
}
.nav-search-input {
  flex: 1;
  height: 100%;
  padding: 0 12px;
  border: none;
  outline: none;
  font-size: 12px;
  background: transparent;
}
.nav-search-btn {
  width: 53px;
  height: 100%;
  background: #2f54eb;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s ease;
}
.nav-search-btn:hover {
  background: #1d39c4;
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
.btn-toggle-theme:hover {
  background: #e8e8e8;
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
.btn-login:hover {
  background: #f0f7ff;
}
.btn-register {
  padding: 6px 15px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.btn-register:hover {
  background: #1d39c4;
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
  transition: border 0.3s ease;
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
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  border-radius: 8px;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}
.user-menu .menu-item {
  padding: 10px 15px;
  font-size: 14px;
  cursor: pointer;
  height: auto;
  line-height: normal;
  margin: 0;
  color: #333;
  transition: background 0.3s ease;
}
.user-menu .menu-item:hover {
  background: #f0f7ff;
  color: #333;
}
.user-menu .logout {
  color: #ff4d4f;
  border-top: 1px solid #f0f0f0;
}

/* ========== 面包屑导航样式 ========== */
.breadcrumb {
  font-size: 14px;
  line-height: 1.8;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}
.breadcrumb span {
  cursor: pointer;
  transition: color 0.3s ease;
}
.breadcrumb span:hover {
  color: #2f54eb;
}
.breadcrumb .separator {
  color: #999;
  cursor: default;
}
.breadcrumb .current {
  color: #333;
  font-weight: 600;
  cursor: default;
}

/* ========== 岗位详情主体样式 ========== */
.job-detail-main {
  width: 100%;
  padding: 30px 0;
  background: #f5f7fa;
}
.detail-container {
  width: 1200px;
  margin: 0 auto;
  background: #fff;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

/* 顶部信息区样式 */
.job-top-section {
  display: flex;
  gap: 30px;
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid #f0f0f0;
}

.job-cover-wrap {
  width: 200px;
  flex-shrink: 0;
  position: relative;
}

/* 岗位信息区域 */
.job-info-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.job-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.job-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tag {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.tag.status {
  background: #e8f4ff;
  color: #1890ff;
  border: 1px solid #b3ddff;
}

.tag.status:hover {
  background: #d6e9ff;
}

.tag.category {
  background: #f6f7f9;
  color: #666;
  border: 1px solid #e8e8e8;
}

.tag.category:hover {
  background: #e8e8e8;
}

.job-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.meta-group {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #666;
}

.meta-icon {
  font-size: 16px;
  margin-right: 8px;
  width: 20px;
  text-align: center;
}

.meta-item {
  color: #444;
}

.job-actions {
  display: flex;
  gap: 16px;
}

.btn-read, .btn-share {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.action-icon {
  font-size: 16px;
}

.btn-read {
  background: #ff7a45;
  color: #fff;
}

.btn-read:hover {
  background: #ff5a1f;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 122, 69, 0.2);
}

.btn-share {
  background: #fff;
  color: #666;
  border: 1px solid #e8e8e8;
}

.btn-share:hover {
  background: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

/* 公司信息区域 */
.job-author-wrap {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 15px;
  border-left: 1px solid #f0f0f0;
  padding-left: 30px;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.author-name {
  font-size: 18px;
  font-weight: 600;
  color: #222;
  margin: 0;
}

.author-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
}

/* 重新设计的详情内容区域（断开卡片样式） */
.job-detail-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* 岗位详情区域样式 */
.job-description-section, .company-info-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  font-size: 20px;
  color: #2f54eb;
}

.section-content {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}

/* 岗位详情项样式：保留原有分点，不加额外数字 */
.description-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.description-item {
  line-height: 1.8;
  font-size: 15px;
  color: #333;
}

/* 公司详情段落样式：首行空两格 */
.company-paragraph {
  text-indent: 2em;
  line-height: 1.8;
  font-size: 15px;
  color: #333;
  margin: 0;
}

/* 空内容提示 */
.empty-content {
  text-align: center;
  padding: 40px 0;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
}

/* 公司信息表格 */
.company-info-table {
  width: 100%;
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
  margin-top: 20px;
}

.table-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #f8f9fa;
}

.table-row:last-child {
  border-bottom: none;
}

.table-label {
  width: 120px;
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.table-value {
  flex: 1;
  color: #333;
  font-size: 14px;
}

.link-text {
  color: #2f54eb;
  text-decoration: none;
  transition: color 0.3s ease;
}

.link-text:hover {
  color: #1d39c4;
  text-decoration: underline;
}

/* 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ========== 页脚样式 ========== */
.footer {
  background: #fff;
  padding: 30px 0;
  border-top: 1px solid #f0f0f0;
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 40px;
}

.footer-wrap {
  width: 1200px;
  margin: 0 auto;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .nav-wrap, .detail-container, .footer-wrap {
    width: 95%;
    padding: 0 20px;
  }
  
  .job-top-section {
    flex-direction: column;
    gap: 20px;
  }
  
  .job-cover-wrap, .job-author-wrap {
    width: 100%;
  }
  
  .job-author-wrap {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid #f0f0f0;
    padding-top: 20px;
  }
}
</style>