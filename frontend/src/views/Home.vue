<template>
  <div class="career-home">
    <!-- 顶部导航（不变） -->
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item active" @click="$router.push('/')">首页</li>
            <li class="menu-item" @click="$router.push('/career-planning-intro')">职业规划</li>
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
            <input type="text" class="nav-search-input" v-model="searchKeyword" placeholder="搜索职业方向、专业、院校、岗位类型" @keyup.enter="handleSearch">
            <button class="nav-search-btn" @click="handleSearch">搜索</button>
          </div>
          <button class="btn-toggle-theme" @click="toggleTheme">🌙</button>
          <button class="btn-login" @click="$router.push('/login')" v-if="!isLogin">登录</button>
          <button class="btn-register" @click="$router.push('/register')" v-if="!isLogin">注册</button>
          <div class="user-profile" v-if="isLogin">
            <img :src="userAvatar || 'https://picsum.photos/seed/avatar/40/40'" alt="用户头像" class="avatar" @click="toggleUserMenu">
            <div class="user-menu" v-show="isUserMenuOpen">
              <div class="menu-item" @click="$router.push('/profile')">个人中心</div>
              <!-- <div class="menu-item" @click="$router.push('/settings')">账号设置</div> -->
              <div class="menu-item logout" @click="handleLogout">退出登录</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 轮播图区（不变） -->
    <section class="banner-carousel">
      <div class="carousel-container" ref="carouselRef">
        <div class="carousel-track" :style="{ transform: `translateX(-${currentIndex * 100}%)` }">
          <div class="carousel-item" v-for="(item, index) in carouselList" :key="index">
            <img :src="item.url" alt="轮播图" class="carousel-img">
            <div class="carousel-overlay">
              <div class="overlay-left">
                <h1 class="overlay-title">大学生智能职业规划系统</h1>
                <p class="overlay-subtitle">精准匹配职业方向 · 科学规划成长路径</p>
                <div class="overlay-tags">
                  <span class="tag">个性化分析</span>
                  <span class="tag">多维度评估</span>
                  <span class="tag">一站式规划</span>
                  <span class="tag">数据驱动</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <button class="carousel-btn prev-btn" @click="prevSlide">◀</button>
        <button class="carousel-btn next-btn" @click="nextSlide">▶</button>
        <div class="carousel-indicators">
          <span class="indicator" v-for="(item, index) in carouselList" :key="index" :class="{ active: index === currentIndex }" @click="goToSlide(index)"></span>
        </div>
        <div class="upload-area">
          <label class="upload-btn">
            <input type="file" accept="image/*" @change="handleImageUpload" hidden>
            📤 更换轮播图片
          </label>
        </div>
      </div>
    </section>

    <!-- 功能模块（已修改） -->
    <section class="function-modules">
      <div class="modules-wrap">
        <div class="module-item" @click="$router.push('/interest-test')">
          <div class="module-content">
            <div class="module-title">兴趣测试</div>
            <div class="module-desc">职业兴趣在线测评</div>
          </div>
          <span class="module-arrow">></span>
        </div>
        <div class="module-item" @click="$router.push('/career-planning-intro')">
          <div class="module-content">
            <div class="module-title">AI职业规划</div>
            <div class="module-desc">智能生成职业规划</div>
          </div>
          <span class="module-arrow">></span>
        </div>
        <div class="module-item" @click="$router.push('/report-export')">
          <div class="module-content">
            <div class="module-title">报告导出</div>
            <div class="module-desc">规划报告一键导出</div>
          </div>
          <span class="module-arrow">></span>
        </div>
      </div>
    </section>

    <!-- 招聘岗位卡片区（纯后端分页，快速加载） -->
    <section class="job-section">
      <div class="job-wrap">
        <div class="job-header">
          <h2 class="job-title-main">
            岗位信息
            <span v-if="searchKeyword" style="font-size:16px;color:#666;margin-left:10px;">搜索结果：{{ searchKeyword }}</span>
          </h2>
          <div class="job-filter">
            <div class="filter-tags">
              <span class="filter-tag" :class="{ active: filterJobName === '' && searchKeyword === '' }" @click="resetAllFilter">全部岗位</span>
              <span class="filter-tag" v-for="jobName in jobNameList" :key="jobName" :class="{ active: filterJobName === jobName }" @click="filterJobName = jobName; filterJobs()">{{ jobName }}</span>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>正在加载岗位数据...</p>
        </div>

        <!-- 错误提示 -->
        <div v-else-if="error" class="error-container">
          <p class="error-text">{{ error }}</p>
          <button class="reload-btn" @click="fetchJobs(1)">重新加载</button>
        </div>

        <!-- 岗位卡片列表 -->
        <div class="job-card-container" ref="jobContainerRef" v-else>
          <div class="job-card" v-for="(item, index) in currentPageJobs" :key="item.id" :class="{ 'animate-in': jobCardAnimateStates[index] }"
               @mouseenter="hoverJobCard = item.id" @mouseleave="hoverJobCard = null" @dblclick="goToJobDetail(item.id)">
            <div class="job-card-content">
              <div class="job-title">{{ item.job_name || '未知岗位' }}</div>
              <div class="job-company">{{ item.company || '未知公司' }}</div>
              <div class="job-meta"><span class="salary">{{ item.salary_range || '面议' }}</span></div>
              <div class="job-hover-info" v-if="hoverJobCard === item.id"><span class="job-portrait-tag">岗位画像</span></div>
            </div>
          </div>
          <div v-if="currentPageJobs.length === 0 && !loading" class="empty-job-container"><p class="empty-text">暂无匹配的岗位数据</p></div>
        </div>

        <!-- 分页组件 -->
        <div v-if="total > 0" class="pagination-container">
          <div class="pagination-info">共 {{ total }} 个岗位，当前第 {{ currentPage }}/{{ totalPages }} 页</div>
          <div class="pagination">
            <button class="page-btn" @click="changePage(1)" :disabled="currentPage === 1">首页</button>
            <button class="page-btn" @click="changePage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
            <button v-for="pageNum in pageNumbers" :key="pageNum" class="page-number" :class="{ active: pageNum === currentPage }" @click="changePage(pageNum)" v-if="pageNum !== -1">{{ pageNum }}</button>
            <span class="page-ellipsis" v-for="(pageNum, index) in pageNumbers" :key="`ellipsis-${index}`" v-if="pageNum === -1">...</span>
            <button class="page-btn" @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">下一页</button>
            <button class="page-btn" @click="changePage(totalPages)" :disabled="currentPage === totalPages">尾页</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 最适配十大岗位传送带
    <section class="top-ten-jobs-section">
      <div class="section-header">
        <h2 class="section-title">最适配十大岗位</h2>
        <el-button type="text" @click="$router.push('/match-result')">查看全部 ></el-button>
      </div>
      <div class="slider-container" ref="sliderRef">
        <div class="slider-track" :style="{ transform: `translateX(-${sliderOffset}%)` }">
          <div class="slider-card" v-for="(job, index) in [...topTenJobs, ...topTenJobs]" :key="index" @click="$router.push('/match-result')">
            <img :src="job.cover" :alt="job.jobName" class="slider-card-cover" />
            <div class="slider-card-info">
              <div class="slider-card-title">{{ job.jobName }}</div>
              <div class="slider-card-match">匹配度：{{ job.matchRate }}%</div>
            </div>
          </div>
        </div>
      </div>
    </section> -->

    <!-- 热门岗位画像卡片区域 -->
    <section class="job-portrait-card-section" ref="portraitSectionRef">
      <div class="section-header">
        <h2 class="section-title">热门岗位画像</h2>
      </div>
      <div class="portrait-card-container" ref="portraitContainerRef" @mousemove="handleMouseMove">
        <div class="portrait-card" v-for="(job, index) in jobPortraitList" :key="job.jobName" :style="getCardStyle(index)" :class="{ 'animate-in': cardAnimateStates[index] }"
             @mouseenter="hoverPortrait = job.jobName" @mouseleave="hoverPortrait = null" @dblclick="goToJobPortraitDetail(job.jobName)">
          <div class="portrait-text-content"><span class="portrait-job-name">{{ job.jobName }}</span></div>
          <div class="portrait-name-tooltip" v-if="hoverPortrait === job.jobName">{{ job.jobName }}</div>
        </div>
        <div v-if="jobPortraitList.length === 0 && !loading" class="empty-portrait-container"><p class="empty-text">暂无岗位画像数据</p></div>
      </div>
    </section>

    <footer class="footer">
      <div class="footer-wrap">© 2026 大学生职业规划系统 | 助力大学生精准规划职业方向</div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// ========== 模拟登录 ==========
const initMockLogin = () => {
  if (!localStorage.getItem('token')) {
    localStorage.setItem('token', 'mock-token-1')
    localStorage.setItem('currentUser', JSON.stringify({ id: 1, username: '测试用户', role: 'user', avatar: '' }))
    localStorage.setItem('avatar', '')
    localStorage.setItem('nickname', '测试用户')
  }
}
initMockLogin()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const router = useRouter()
const route = useRoute()

watch(() => route.path, () => {
  isLogin.value = !!localStorage.getItem('token')
  userAvatar.value = localStorage.getItem('avatar') || ''
}, { immediate: true })

const toggleUserMenu = () => { isUserMenuOpen.value = !isUserMenuOpen.value }
const handleLogout = () => {
  localStorage.clear()
  isLogin.value = false
  isUserMenuOpen.value = false
  initMockLogin()
  isLogin.value = true
  userAvatar.value = ''
  ElMessage.success('已切换为测试用户')
}

// 主题切换
const darkMode = ref(localStorage.getItem('darkMode') === 'true')
function applyTheme() {
  if (darkMode.value) document.body.classList.add('dark')
  else document.body.classList.remove('dark')
}
function toggleTheme() {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  applyTheme()
  ElMessage.success(`已切换为${darkMode.value ? '暗黑' : '明亮'}模式`)
}

// 轮播图
const carouselRef = ref(null)
const currentIndex = ref(0)
const carouselList = ref([
  { url: 'https://picsum.photos/seed/carousel1/1200/300' },
  { url: 'https://picsum.photos/seed/carousel2/1200/300' },
  { url: 'https://picsum.photos/seed/carousel3/1200/300' }
])
let carouselTimer = null
const startCarousel = () => { carouselTimer = setInterval(() => nextSlide(), 3000) }
const prevSlide = () => { currentIndex.value = (currentIndex.value - 1 + carouselList.value.length) % carouselList.value.length }
const nextSlide = () => { currentIndex.value = (currentIndex.value + 1) % carouselList.value.length }
const goToSlide = (index) => { currentIndex.value = index }
const handleImageUpload = (e) => {
  const file = e.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { ElMessage.error('请选择图片文件'); return }
  if (file.size / 1024 / 1024 > 5) { ElMessage.error('图片大小不能超过5MB'); return }
  const reader = new FileReader()
  reader.onload = (event) => {
    carouselList.value.push({ url: event.target.result })
    currentIndex.value = carouselList.value.length - 1
    ElMessage.success('轮播图片上传成功')
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}

// 岗位数据（后端分页）
const jobList = ref([])
const jobNameList = ref([])
const loading = ref(false)
const error = ref('')
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const filterJobName = ref('')
const searchKeyword = ref('')

const API_BASE_URL = 'http://localhost:5000'
const JOB_SEARCH_API_URL = `${API_BASE_URL}/api/jobs/search`
const JOB_NAMES_API_URL = `${API_BASE_URL}/api/jobs/names`

const calculateSalaryValue = (salaryRange) => {
  if (!salaryRange || salaryRange === '面议') return 0
  const match = salaryRange.match(/(\d+)K-(\d+)K/)
  if (match && match.length === 3) {
    return (parseFloat(match[1]) + parseFloat(match[2])) / 2
  }
  return 0
}

const fetchJobNames = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(JOB_NAMES_API_URL, { headers: { Authorization: token ? `Bearer ${token}` : '' } })
    if (Array.isArray(res.data)) jobNameList.value = res.data.filter(name => name && name.trim())
  } catch (err) {
    console.error('获取岗位名称失败:', err)
    if (jobList.value.length > 0) {
      const names = [...new Set(jobList.value.map(j => j.job_name).filter(Boolean))]
      jobNameList.value = names
    }
  }
}

const fetchJobs = async (page = 1) => {
  loading.value = true
  error.value = ''
  currentPage.value = page
  try {
    const token = localStorage.getItem('token')
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      keyword: searchKeyword.value.trim() || undefined,
    }
    if (filterJobName.value) params.keyword = filterJobName.value
    const res = await axios.get(JOB_SEARCH_API_URL, { params, headers: { Authorization: token ? `Bearer ${token}` : '' } })
    const data = res.data
    let items = data.items || data.data || []
    if (!Array.isArray(items)) items = []
    jobList.value = items.map(item => ({
      id: item.id || item.rowid,
      job_name: item.job_name || '未知岗位',
      company: item.company || '未知公司',
      salary_range: item.salary_range || '面议',
      salaryValue: calculateSalaryValue(item.salary_range),
      industry: item.industry || '',
      location: item.location || '',
      experience: item.experience || '1-3年'
    }))
    total.value = data.total || data.count || 0
  } catch (err) {
    console.error('获取岗位数据失败:', err)
    error.value = err.response?.data?.error || err.message || '加载失败'
    jobList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const goToJobDetail = (jobId) => { router.push({ path: '/job-detail', query: { id: jobId } }) }
const filterJobs = () => { currentPage.value = 1; fetchJobs(1) }
const resetAllFilter = () => { filterJobName.value = ''; searchKeyword.value = ''; currentPage.value = 1; fetchJobs(1) }
const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (keyword) {
    filterJobName.value = ''
    currentPage.value = 1
    fetchJobs(1)
    ElMessage.success(`已搜索：${keyword}`)
    const jobSection = document.querySelector('.job-section')
    if (jobSection) jobSection.scrollIntoView({ behavior: 'smooth' })
  } else {
    ElMessage.warning('请输入搜索关键词')
  }
}
const changePage = (pageNum) => {
  if (pageNum < 1 || pageNum > totalPages.value || pageNum === currentPage.value) return
  fetchJobs(pageNum)
  const jobSection = document.querySelector('.job-section')
  if (jobSection) jobSection.scrollIntoView({ behavior: 'smooth' })
}
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
const currentPageJobs = computed(() => jobList.value)
const pageNumbers = computed(() => {
  const pages = []
  const total = totalPages.value
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    if (currentPage.value <= 3) {
      pages.push(1, 2, 3, 4, 5, -1, total)
    } else if (currentPage.value >= total - 2) {
      pages.push(1, -1, total - 4, total - 3, total - 2, total - 1, total)
    } else {
      pages.push(1, -1, currentPage.value - 2, currentPage.value - 1, currentPage.value,
                 currentPage.value + 1, currentPage.value + 2, -1, total)
    }
  }
  return pages
})

// 岗位画像列表（单独从接口获取，不依赖岗位分页）
const jobPortraitList = ref([])
const fetchPortraitList = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(JOB_NAMES_API_URL, { headers: { Authorization: token ? `Bearer ${token}` : '' } })
    if (Array.isArray(res.data)) {
      jobPortraitList.value = res.data.filter(name => name && name.trim()).map(name => ({ jobName: name }))
    }
  } catch (err) {
    console.error('获取岗位画像列表失败:', err)
    if (jobList.value.length > 0) {
      const names = [...new Set(jobList.value.map(j => j.job_name).filter(Boolean))]
      jobPortraitList.value = names.map(name => ({ jobName: name }))
    }
  }
  initCardAnimateStates()
}
const goToJobPortraitDetail = (jobName) => {
  router.push({ path: '/job-portrait', query: { jobName: encodeURIComponent(jobName) } })
}

// 其他功能
const goToFeature = (type) => {
  const map = { '测评': '/interest-test', '分析': '/ability-analysis', '规划': '/development-path', '导出': '/report-export' }
  router.push(map[type] || '/')
}

// 传送带数据
const topTenJobs = ref([
  { jobName: '前端开发工程师', matchRate: 95, cover: 'https://picsum.photos/seed/top1/200/280' },
  { jobName: '产品经理', matchRate: 92, cover: 'https://picsum.photos/seed/top2/200/280' },
  { jobName: '数据分析师', matchRate: 89, cover: 'https://picsum.photos/seed/top3/200/280' },
  { jobName: 'UI设计师', matchRate: 87, cover: 'https://picsum.photos/seed/top4/200/280' },
  { jobName: 'Java开发工程师', matchRate: 85, cover: 'https://picsum.photos/seed/top5/200/280' },
  { jobName: '运营专员', matchRate: 83, cover: 'https://picsum.photos/seed/top6/200/280' },
  { jobName: 'AI算法工程师', matchRate: 81, cover: 'https://picsum.photos/seed/top7/200/280' },
  { jobName: '测试开发工程师', matchRate: 79, cover: 'https://picsum.photos/seed/top8/200/280' },
  { jobName: '嵌入式工程师', matchRate: 77, cover: 'https://picsum.photos/seed/top9/200/280' },
  { jobName: '游戏策划', matchRate: 75, cover: 'https://picsum.photos/seed/top10/200/280' }
])
const sliderRef = ref(null)
const sliderOffset = ref(0)
let sliderTimer = null
const sliderSpeed = 0.1
const startSlider = () => { sliderTimer = setInterval(() => { sliderOffset.value += sliderSpeed; if (sliderOffset.value >= 100) sliderOffset.value = 0 }, 30) }

// 动画相关
const portraitContainerRef = ref(null)
const portraitSectionRef = ref(null)
const mousePos = ref({ x: 0, y: 0 })
const containerRect = ref({ left: 0, top: 0, width: 0, height: 0 })
const cardAnimateStates = ref([])
const jobCardAnimateStates = ref([])
const animateTimers = ref([])
const jobAnimateTimers = ref([])
const hoverCard = ref(null)
const hoverPortrait = ref(null)
const hoverJobCard = ref(null)

const initCardAnimateStates = () => {
  cardAnimateStates.value = jobPortraitList.value.map(() => false)
  jobCardAnimateStates.value = currentPageJobs.value.map(() => false)
}
const handleScroll = () => {
  if (portraitSectionRef.value) {
    const rect = portraitSectionRef.value.getBoundingClientRect()
    if (rect.top < window.innerHeight * 0.8 && !cardAnimateStates.value[0]) {
      jobPortraitList.value.forEach((_, i) => {
        const timer = setTimeout(() => { cardAnimateStates.value[i] = true }, i * 150)
        animateTimers.value.push(timer)
      })
    }
  }
  const jobRect = document.querySelector('.job-section')?.getBoundingClientRect()
  if (jobRect && jobRect.top < window.innerHeight * 0.8 && !jobCardAnimateStates.value[0] && currentPageJobs.value.length > 0) {
    currentPageJobs.value.forEach((_, i) => {
      const timer = setTimeout(() => { jobCardAnimateStates.value[i] = true }, i * 150)
      jobAnimateTimers.value.push(timer)
    })
  }
}
const startCardAnimation = () => {
  jobPortraitList.value.forEach((_, i) => {
    const timer = setTimeout(() => { cardAnimateStates.value[i] = true }, i * 150)
    animateTimers.value.push(timer)
  })
}
const startJobCardAnimation = () => {
  currentPageJobs.value.forEach((_, i) => {
    const timer = setTimeout(() => { jobCardAnimateStates.value[i] = true }, i * 150)
    jobAnimateTimers.value.push(timer)
  })
}
const handleMouseMove = (e) => {
  if (!portraitContainerRef.value) return
  const rect = portraitContainerRef.value.getBoundingClientRect()
  containerRect.value = rect
  mousePos.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
}
const getCardStyle = (index) => {
  const { x, y } = mousePos.value
  const { width, height } = containerRect.value
  if (!width || !height) return {}
  const col = index % 6
  const row = Math.floor(index / 6)
  const cardWidth = 200, cardHeight = 140, gapX = 60, gapY = 30
  const colOffset = col % 2 === 1 ? cardHeight / 2 : 0
  const baseX = (width - 6 * cardWidth - 5 * gapX) / 2 + col * (cardWidth + gapX)
  const baseY = row * (cardHeight + gapY) + colOffset
  const ratioX = x / width, ratioY = y / height
  let followY = ratioY > 0.5 ? -(ratioY - 0.5) * 1800 : -(ratioY - 0.5) * 600
  const followX = -(ratioX - 0.5) * 1200
  return { left: `${baseX + followX}px`, top: `${baseY + followY}px`, transition: cardAnimateStates.value[index] ? 'all 0.3s ease' : 'none' }
}

onMounted(() => {
  startCarousel()
  startSlider()
  applyTheme()
  initCardAnimateStates()
  nextTick(() => {
    if (portraitContainerRef.value) containerRect.value = portraitContainerRef.value.getBoundingClientRect()
    window.addEventListener('scroll', handleScroll)
    handleScroll()
    fetchJobNames()
    fetchJobs(1)
    fetchPortraitList()
  })
})

onUnmounted(() => {
  clearInterval(carouselTimer)
  clearInterval(sliderTimer)
  animateTimers.value.forEach(timer => clearTimeout(timer))
  jobAnimateTimers.value.forEach(timer => clearTimeout(timer))
  window.removeEventListener('scroll', handleScroll)
})
</script>


<style scoped>
/* 全局容器 */
.career-home {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  background: #f8f9fa;
  margin: 0;
  padding: 60px 0 0 0;
}

/* 用户头像和菜单样式 */
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

/* 顶部导航样式 */
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

/* 下拉菜单样式 */
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

/* 导航栏右侧 */
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

/* 轮播Banner区样式 */
.banner-carousel {
  width: 100%;
  height: 320px;
  position: relative;
  overflow: hidden;
  margin-top: 0;
}
.carousel-container {
  width: 100%;
  height: 100%;
  position: relative;
}
.carousel-track {
  display: flex;
  height: 100%;
  transition: transform 0.5s ease;
}
.carousel-item {
  flex: 0 0 100%;
  height: 100%;
  position: relative;
}
.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.carousel-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 120px;
  box-sizing: border-box;
  color: #fff;
}
.overlay-left {
  text-align: center;
}
.overlay-title {
  font-size: 38px;
  font-weight: bold;
  margin: 0 0 15px 0;
}
.overlay-subtitle {
  font-size: 18px;
  margin: 0 0 20px 0;
  opacity: 0.9;
}
.overlay-tags {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.overlay-tags .tag {
  background: rgba(255,255,255,0.2);
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 14px;
}
.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.3);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  z-index: 10;
}
.carousel-btn:hover {
  background: rgba(0,0,0,0.5);
}
.prev-btn {
  left: 20px;
}
.next-btn {
  right: 20px;
}
.carousel-indicators {
  position: absolute;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}
.indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
}
.indicator.active {
  background: #fff;
}
.upload-area {
  position: absolute;
  bottom: 15px;
  right: 20px;
}
.upload-btn {
  padding: 6px 15px;
  background: rgba(255,255,255,0.8);
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.upload-btn:hover {
  background: #fff;
}

/* 功能模块样式 */
.function-modules {
  width: 100%;
  background: #fff;
  padding: 20px 0;
  border-bottom: 1px solid #e8e8e8;
}
.modules-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
}
.module-item {
  width: 33.33%;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  border-right: 1px solid #e8e8e8;
}
.module-item:last-child {
  border-right: none;
}
.module-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.module-title {
  font-size: 16px;
  color: #222;
  margin-bottom: 4px;
}
.module-desc {
  font-size: 14px;
  color: #999;
}
.module-arrow {
  font-size: 16px;
  color: #999;
}

/* 招聘岗位卡片区样式 */
.job-section {
  padding: 30px 0;
  background: #f8f9fa;
}
.job-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

/* 岗位信息标题 + 筛选栏样式 - 调整布局 */
.job-header {
  width: 100%;
  display: flex;
  flex-direction: column; /* 改为垂直布局 */
  align-items: flex-start; /* 左对齐 */
  margin-bottom: 20px;
  gap: 15px; /* 添加间距 */
}
.job-title-main {
  font-size: 24px;
  color: #222;
  font-weight: 600;
  margin: 0;
}
.job-filter {
  width: 100%; /* 占满宽度 */
  display: flex;
  justify-content: flex-start; /* 左对齐 */
}

/* 修改：岗位名称筛选标签样式（适配多标签换行） */
.filter-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap; /* 允许换行 */
  max-height: 120px; /* 限制最大高度，避免标签过多 */
  overflow-y: auto; /* 超出高度滚动 */
  padding: 5px;
  width: 100%;
}
.filter-tag {
  padding: 6px 15px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap; /* 防止标签文字换行 */
}
.filter-tag:hover {
  border-color: #2f54eb;
  color: #2f54eb;
}
.filter-tag.active {
  background: #2f54eb;
  color: #fff;
  border-color: #2f54eb;
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #666;
}
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2f54eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误提示样式 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #ff4d4f;
  gap: 15px;
}
.error-text {
  margin-bottom: 10px;
  font-size: 14px;
}
.reload-btn {
  padding: 8px 16px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.reload-btn:hover {
  background: #1d39c4;
}

/* 空数据样式 */
.empty-job-container {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #999;
}
.empty-text {
  font-size: 14px;
}

/* 岗位卡片容器 */
.job-card-container {
  width: 100%;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  padding: 20px 0;
  box-sizing: border-box;
}

/* 岗位卡片样式（优化版，增加渐变背景和精致样式） */
.job-card {
  width: 100%;
  /* 渐变背景 */
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
  border-radius: 12px;
  /* 更精致的阴影 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  /* 增加边框 */
  border: 1px solid #f0f2ff;
  overflow: hidden;
  cursor: pointer;
  transform: translateY(20px);
  opacity: 0;
  transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1;
  box-sizing: border-box;
  /* 调整卡片高度 */
  height: 180px;
  display: flex;
  flex-direction: column;
  padding: 10px;
  position: relative;
  /* 增加装饰元素 */
}
/* 卡片装饰元素 - 左上角小三角 */
.job-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 40px 40px 0;
  border-color: transparent #2f54eb30 transparent transparent;
  opacity: 0.5;
}

/* 岗位卡片飞入动画 */
.job-card.animate-in {
  transform: translateY(0);
  opacity: 1;
}

/* 岗位卡片悬浮效果（增强） */
.job-card:hover {
  transform: translateY(-8px) scale(1.02);
  /* 更强的阴影 */
  box-shadow: 0 8px 24px rgba(47, 84, 235, 0.15);
  z-index: 10;
  /* 悬浮时边框变色 */
  border-color: #2f54eb;
}

/* 岗位卡片内容样式（优化排版和间距） */
.job-card-content {
  flex: 1;
  padding: 15px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  height: 100%;
  box-sizing: border-box;
}
.job-card-content .job-title {
  font-size: 18px;
  font-weight: 600;
  color: #222;
  margin-bottom: 12px;
  line-height: 1.4;
  word-break: break-all;
  /* 增加文字阴影 */
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}
.job-card-content .job-company {
  font-size: 15px;
  color: #666;
  margin-bottom: 15px;
  line-height: 1.4;
}

/* 岗位元信息（薪资+经验） */
.job-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  margin-bottom: 0;
  flex-wrap: wrap;
  gap: 8px;
}
.salary {
  color: #ff7a45;
  font-weight: 600;
  /* 增加薪资文字效果 */
  text-shadow: 0 1px 3px rgba(255, 122, 69, 0.2);
}
.experience {
  color: #666;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

/* 悬浮时显示的岗位画像标签 */
.job-hover-info {
  position: absolute;
  bottom: 15px;
  right: 15px;
  z-index: 5;
}
.job-portrait-tag {
  background: rgba(47, 84, 235, 0.9);
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  text-align: center;
  animation: fadeInUp 0.3s ease;
}

/* 分页导航样式 */
.pagination-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  gap: 15px;
}
.pagination-info {
  font-size: 14px;
  color: #666;
}
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}
.page-btn {
  padding: 8px 15px;
  border: 1px solid #e8e8e8;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s ease;
}
.page-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #2f54eb;
  border-color: #2f54eb;
}
.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.page-number {
  width: 36px;
  height: 36px;
  border: 1px solid #e8e8e8;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.page-number:hover:not(.active) {
  border-color: #2f54eb;
  color: #2f54eb;
}
.page-number.active {
  background: #2f54eb;
  color: #fff;
  border-color: #2f54eb;
}
.page-ellipsis {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #ccc;
}

/* 最适配十大岗位 - 传送带样式 */
.top-ten-jobs-section {
  padding: 40px 0;
  background: #000;
  width: 100%;
}
.top-ten-jobs-section .section-header {
  width: 90%;
  max-width: 1400px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.top-ten-jobs-section .section-title {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}
/* 传送带容器 */
.slider-container {
  width: 100%;
  overflow: hidden;
  position: relative;
  height: 320px;
}
/* 传送带轨道 */
.slider-track {
  display: flex;
  gap: 20px;
  transition: none;
  will-change: transform;
}
/* 传送带卡片 */
.slider-card {
  width: 200px;
  height: 280px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.3s ease;
}
.slider-card:hover {
  transform: translateY(-8px) scale(1.05);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}
.slider-card-cover {
  width: 100%;
  height: 220px;
  object-fit: cover;
}
.slider-card-info {
  padding: 12px;
}
.slider-card-title {
  font-size: 16px;
  font-weight: 600;
  color: #222;
  margin-bottom: 4px;
}
.slider-card-match {
  font-size: 14px;
  color: #2f54eb;
  font-weight: 50;
}

/* 【修改 2】热门岗位画像容器放大 1/3 */
.job-portrait-card-section {
  padding: 53px 0;
  background: #f5f5f0;
  width: 100%;
}
.job-portrait-card-section .section-header {
  width: 90%;
  max-width: 1400px;
  margin: 0 auto 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.job-portrait-card-section .section-title {
  font-size: 24px;
  font-weight: 600;
  color: #000;
  margin: 0;
}
/* 容器高度放大 1/3 */
.portrait-card-container {
  width: 100%;
  min-height: 667px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  padding: 27px 0;
}

/* ====================== ✅ 仅这里优化：岗位画像卡片美化 ====================== */
.portrait-card {
  width: 200px;
  height: 140px;
  /* 柔和渐变背景 + 随机色彩 */
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
  border-radius: 16px;
  border: 2px solid transparent;
  box-shadow: 0 6px 16px rgba(0,0,0,0.08);
  overflow: hidden;
  cursor: pointer;
  position: absolute;
  transform: translateX(1000px) translateY(0);
  opacity: 0;
  transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  box-sizing: border-box;
}
/* 卡片颜色系列（柔和不刺眼） */
.portrait-card:nth-child(5n+1) {
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  border-color: #91d5ff;
}
.portrait-card:nth-child(5n+2) {
  background: linear-gradient(135deg, #f0f5ff 0%, #f5f8ff 100%);
  border-color: #adc6ff;
}
.portrait-card:nth-child(5n+3) {
  background: linear-gradient(135deg, #fff7e6 0%, #fffbf0 100%);
  border-color: #ffd591;
}
.portrait-card:nth-child(5n+4) {
  background: linear-gradient(135deg, #f0f2f5 0%, #f7f8fa 100%);
  border-color: #d9d9d9;
}
.portrait-card:nth-child(5n+5) {
  background: linear-gradient(135deg, #f6ffed 0%, #fcffe6 100%);
  border-color: #b7eb8f;
}

/* 飞入动画激活状态（不变） */
.portrait-card.animate-in {
  transform: translateX(0) translateY(0);
  opacity: 1;
}
/* 悬浮效果（保留并优化） */
.portrait-card:hover {
  transform: translateY(-12px) scale(1.05);
  box-shadow: 0 15px 30px rgba(0,0,0,0.15);
  z-index: 10;
  border-color: #2f54eb;
}

/* 纯文字内容 + 图标样式 */
.portrait-text-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 8px;
}
/* 职业图标（自动匹配风格） */
.portrait-text-content::before {
  content: "💼";
  font-size: 24px;
  opacity: 0.8;
}
.portrait-card:nth-child(3n+1) .portrait-text-content::before { content: "💻"; }
.portrait-card:nth-child(3n+2) .portrait-text-content::before { content: "📊"; }
.portrait-card:nth-child(3n+3) .portrait-text-content::before { content: "🎨"; }

.portrait-job-name {
  font-size: 17px;
  font-weight: 600;
  color: #222;
  text-align: center;
  word-break: break-all;
  line-height: 1.4;
}

/* 提示框（不变） */
.portrait-name-tooltip {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255,255,255,0.95);
  color: #2f54eb;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  z-index: 11;
  animation: fadeInUp 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
/* ======================================================================== */

/* 空数据样式 */
.empty-portrait-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #999;
}

/* 通用动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 淡入上移动画 */
@keyframes fadeInUp {
  from { 
    opacity: 0; 
    transform: translate(-50%, 10px); 
  }
  to { 
    opacity: 1; 
    transform: translate(-50%, 0); 
  }
}

/* 页脚样式 */
.footer {
  background: #fff;
  padding: 20px 0;
  border-top: 1px solid #e8e8e8;
  text-align: center;
  color: #666;
  font-size: 14px;
}
.footer-wrap {
  width: 1200px;
  margin: 0 auto;
}
</style>