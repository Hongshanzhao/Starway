<template>
  <div class="career-planning-intro-page">
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
            <li class="menu-item active" @click="$router.push('/career-planning-intro')">职业规划</li>
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

    <!-- 主视觉区域（左上角居左） -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-tags">
          <span class="hero-tag">可辅助用于大学生职业规划大赛</span>
          <span class="hero-tag tag-highlight">AI智能赋能·免费使用</span>
        </div>
        <h1 class="hero-title">AI智能职业规划系统</h1>
        <p class="hero-subtitle">
          职业兴趣探索 · 职业目标洞察 · 深度诊断分析 · 规划报告生成
        </p>
        <p class="hero-tip">
          告别职业迷茫、破解规划难题，一站式搞定求职/升学/竞赛全场景需求
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="startPlanning">
            立即开始规划
          </el-button>
          <!-- <el-button size="large" @click="goToMyPlan">我的规划</el-button> -->
        </div>
      </div>
    </div>

    <!-- 流程步骤区域 -->
    <div class="process-section">
      <div class="river-container">
        <div class="process-card step-1">
          <div class="step-number">1</div>
          <h3 class="step-title">职业能力自我诊断</h3>
          <p class="step-desc">
            快速解析个人简历<br />
            职业目标匹配度分析<br />
            挖掘个人职业竞争力
          </p>
        </div>
        
        <div class="process-card step-2">
          <div class="step-number">2</div>
          <h3 class="step-title">探索个人职业兴趣</h3>
          <p class="step-desc">
            基于AI大模型的职业兴趣测评<br />
            丰富的岗位、行业和专业百科<br />
            完善的职业目标认知测评体系
          </p>
        </div>
        
        <div class="process-card step-3">
          <div class="step-number">3</div>
          <h3 class="step-title">锁定个人职业目标</h3>
          <p class="step-desc">
            综合评估辅助锁定个人目标<br />
            剖析成功案例规划职业路径<br />
            配套课程提升岗位实践认知
          </p>
        </div>
        
        <div class="process-card step-4">
          <div class="step-number">4</div>
          <h3 class="step-title">背景提升项目补足短板</h3>
          <p class="step-desc">
            实习实践履历提升求职竞争力<br />
            国际义工志愿者丰富差异履历<br />
            科研论文项目提升升学竞争力
          </p>
        </div>
        
        <div class="process-card step-5">
          <div class="step-number">5</div>
          <h3 class="step-title">深度职业规划分析报告</h3>
          <p class="step-desc">
            7大竞争力维度匹配性分析<br />
            300+决策因子AI建模分析<br />
            10页+职业规划报告辅助生成<br />
            AI辅助PPT制作生成
          </p>
        </div>
        
        <div class="river">
          <div class="water-ripple" v-for="i in 30" :key="i" :style="{ '--i': i }"></div>
          <div class="wave wave-1"></div>
          <div class="wave wave-2"></div>
          <div class="wave wave-3"></div>
          <div class="duck-container">
            <div class="duck">🦆</div>
            <div class="duck-ripple"></div>
          </div>
          <div class="river-end"></div>
        </div>
      </div>
    </div>

    <!-- 核心优势模块 -->
    <div class="advantage-section">
      <h2 class="section-title">系统核心优势</h2>
      <div class="advantage-list">
        <div class="advantage-item">
          <div class="advantage-icon">🤖</div>
          <h4>AI智能分析</h4>
          <p>基于大模型深度测评，告别主观判断，结果更精准</p>
        </div>
        <div class="advantage-item">
          <div class="advantage-icon">📝</div>
          <h4>大赛适配</h4>
          <p>贴合大学生职业规划大赛评分标准，辅助获奖</p>
        </div>
        <div class="advantage-item">
          <div class="advantage-icon">📚</div>
          <h4>资源全覆盖</h4>
          <p>岗位百科、实习资源、规划模板一站式获取</p>
        </div>
        <div class="advantage-item">
          <div class="advantage-icon">⚡</div>
          <h4>高效便捷</h4>
          <p>10分钟完成测评，一键生成专属规划报告</p>
        </div>
      </div>
    </div>

    <!-- 适用人群模块（单列一行三分之二，左右交替分布） -->
    <div class="user-group-section">
      <h2 class="section-title">适合这样的你</h2>
      <div class="user-list">
        <!-- 大一迷茫新生 - 左侧 -->
        <div class="user-card left" ref="card1">
          <div class="user-header">
            <div class="user-icon">🎓</div>
            <div class="user-badge">新生专属</div>
          </div>
          <h3 class="user-title">大一迷茫新生</h3>
          <div class="user-features">
            <div class="feature-item">
              <span class="feature-icon">📍</span>
              <span class="feature-text">专业认知与职业前景分析</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🧭</span>
              <span class="feature-text">兴趣测评与方向探索</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📅</span>
              <span class="feature-text">四年大学生活规划制定</span>
            </div>
          </div>
          <p class="user-desc">
            刚踏入大学校园，面对全新的环境和众多的专业课程，你可能对未来方向感到迷茫，不清楚自己的专业对应的职业发展路径，也不知道如何规划大学生活。我们的系统通过科学的职业兴趣测评和行业洞察分析，帮助你深入了解不同职业方向的特点和要求，结合你的个人特质和兴趣偏好，为你推荐适合的发展方向，制定清晰的四年成长规划，让你从大一起就有明确的目标和方向。
          </p>
          <div class="user-card-bg"></div>
        </div>

        <!-- 大二专业定向 - 右侧 -->
        <div class="user-card right" ref="card2">
          <div class="user-header">
            <div class="user-icon">📚</div>
            <div class="user-badge">专业深耕</div>
          </div>
          <h3 class="user-title">大二专业定向</h3>
          <div class="user-features">
            <div class="feature-item">
              <span class="feature-icon">🔍</span>
              <span class="feature-text">专业细分方向对比分析</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📖</span>
              <span class="feature-text">核心课程选择建议</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🤝</span>
              <span class="feature-text">导师匹配与行业交流</span>
            </div>
          </div>
          <p class="user-desc">
            经过大一的基础课程学习和适应，你已经对大学学习有了基本认识，现在需要确定专业细分方向或考虑辅修/双学位选择。大二是专业能力构建的关键时期，选择合适的专业方向将直接影响后续的职业发展。我们的系统会结合你的学习成绩、兴趣特长和职业倾向，提供各专业细分方向的详细对比，包括课程设置、就业前景、深造路径等，同时推荐适合的核心课程和实践项目，帮助你做出最适合自己的专业选择，并匹配相关领域的导师和行业人士进行交流指导。
          </p>
          <div class="user-card-bg"></div>
        </div>

        <!-- 大三求职备战 - 左侧 -->
        <div class="user-card left" ref="card3">
          <div class="user-header">
            <div class="user-icon">💼</div>
            <div class="user-badge">求职冲刺</div>
          </div>
          <h3 class="user-title">大三求职备战</h3>
          <div class="user-features">
            <div class="feature-item">
              <span class="feature-icon">📄</span>
              <span class="feature-text">简历优化与求职信指导</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🎭</span>
              <span class="feature-text">模拟面试与技巧培训</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🎯</span>
              <span class="feature-text">精准岗位匹配与内推</span>
            </div>
          </div>
          <p class="user-desc">
            大三是求职备战的黄金时期，你即将面临实习和校招的双重挑战，需要全面提升求职竞争力。此时的你可能已经确定了大致的职业方向，但缺乏求职实战经验，简历制作、面试技巧、岗位选择等都是需要攻克的难题。我们的系统提供一站式求职备战服务，包括AI简历优化、多轮模拟面试、岗位匹配分析等功能，同时对接海量实习和校招资源，根据你的专业背景、技能水平和职业目标，精准推荐适合的岗位机会，并提供针对性的求职技巧培训，帮助你在激烈的求职竞争中脱颖而出。
          </p>
          <div class="user-card-bg"></div>
        </div>

        <!-- 大四升学规划 - 右侧 -->
        <div class="user-card right" ref="card4">
          <div class="user-header">
            <div class="user-icon">🎯</div>
            <div class="user-badge">升学规划</div>
          </div>
          <h3 class="user-title">大四升学规划</h3>
          <div class="user-features">
            <div class="feature-item">
              <span class="feature-icon">🏫</span>
              <span class="feature-text">院校专业匹配分析</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📝</span>
              <span class="feature-text">申请文书撰写指导</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">⏰</span>
              <span class="feature-text">申请时间线管理</span>
            </div>
          </div>
          <p class="user-desc">
            大四的你面临毕业抉择，准备考研、保研或出国留学，需要明确目标院校与专业，制定科学的备考和申请计划。升学是一项系统工程，涉及院校选择、备考复习、文书撰写、材料准备等多个环节，任何一个环节的失误都可能影响最终结果。我们的系统基于你的本科背景、成绩排名、科研经历等多维度数据，智能匹配适合的目标院校和专业，提供详细的备考规划和复习资料，指导申请文书的撰写和优化，同时建立完整的申请时间线，提醒关键节点，帮助你有条不紊地完成升学准备，最大化提升升学成功率。
          </p>
          <div class="user-card-bg"></div>
        </div>

        <!-- 竞赛备赛选手 - 左侧 -->
        <div class="user-card left" ref="card5">
          <div class="user-header">
            <div class="user-icon">🏆</div>
            <div class="user-badge">竞赛赋能</div>
          </div>
          <h3 class="user-title">竞赛备赛选手</h3>
          <div class="user-features">
            <div class="feature-item">
              <span class="feature-icon">💡</span>
              <span class="feature-text">竞赛选题与创意优化</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span class="feature-text">项目方案打磨与完善</span>
            </div>
            <div class="feature-item">
              <span class="feature-text">答辩技巧与模拟演练</span>
            </div>
          </div>
          <p class="user-desc">
            作为竞赛备赛选手，你参与各类学科竞赛、创新创业大赛，希望通过竞赛提升综合能力、丰富履历，甚至斩获奖项。竞赛备赛过程中，选题、方案设计、项目打磨、答辩展示等环节都需要专业指导。我们的系统汇聚了各类型竞赛的获奖案例和备赛经验，提供竞赛选题的智能推荐和创意优化，帮助你打造具有竞争力的项目方案，同时提供专业的答辩技巧培训和模拟演练，邀请往届获奖选手和评委进行点评指导，全方位提升你的竞赛表现，助力你在各类大赛中斩获佳绩。
          </p>
          <div class="user-card-bg"></div>
        </div>
      </div>
    </div>

    <!-- 回到顶部按钮 -->
    <div class="back-top" @click="backToTop" v-show="showBackTop">
      <el-icon size="20"><ArrowUp /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Flag,
  Avatar,
  ArrowUp
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 登录状态
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
  ElMessage.success('退出登录成功')
}

// 主题切换
const darkMode = ref(localStorage.getItem('darkMode') === 'true')
function applyTheme() {
  if (darkMode.value) {
    document.body.classList.add('dark')
  } else {
    document.body.classList.remove('dark')
  }
}

function toggleTheme() {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  applyTheme()
  ElMessage.success(`已切换为${darkMode.value ? '暗黑' : '明亮'}模式`)
}

// 搜索功能
const handleSearch = () => {
  const searchInput = document.querySelector('.nav-search-input')
  const keyword = searchInput.value.trim()
  if (keyword) {
    router.push(`/search?keyword=${encodeURIComponent(keyword)}`)
    searchInput.value = ''
    ElMessage.success(`正在搜索：${keyword}`)
  } else {
    ElMessage.warning('请输入搜索关键词')
  }
}

// 核心功能跳转
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

// 页面功能
const startPlanning = () => {
  router.push('/student-ability')
}

const goToMyPlan = () => {
  router.push('/career-planning')
}

// 回到顶部
const showBackTop = ref(false)
const handleScroll = () => {
  showBackTop.value = window.scrollY > 300
}
const backToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// 卡片飞入动画
const card1 = ref(null)
const card2 = ref(null)
const card3 = ref(null)
const card4 = ref(null)
const card5 = ref(null)

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('fly-in')
    }
  })
}, { threshold: 0.1 })

onMounted(() => {
  applyTheme()
  window.addEventListener('scroll', handleScroll)
  
  // 监听卡片进入视口
  if (card1.value) observer.observe(card1.value)
  if (card2.value) observer.observe(card2.value)
  if (card3.value) observer.observe(card3.value)
  if (card4.value) observer.observe(card4.value)
  if (card5.value) observer.observe(card5.value)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  observer.disconnect()
})
</script>

<style scoped>
/* 全局页面样式（强制底部为白色） */
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background-color: #ffffff !important;
  /* 移除滚动条核心样式 */
  overflow-y: hidden;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

/* 隐藏Chrome/Safari等webkit内核浏览器的滚动条 */
html::-webkit-scrollbar,
body::-webkit-scrollbar {
  display: none;
}

.career-planning-intro-page {
  min-height: 100vh;
  background: #ffffff;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  margin: 0;
  padding: 60px 0 0 0;
  transition: all 0.3s ease;
  /* 页面内容滚动，容器外无滚动条 */
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

/* 隐藏容器内的滚动条 */
.career-planning-intro-page::-webkit-scrollbar {
  display: none;
}

/* 暗黑模式适配 */
.career-planning-intro-page.dark,
.career-planning-intro-page.dark html,
.career-planning-intro-page.dark body {
  background: #0f172a !important;
  color: #f1f5f9;
}
.career-planning-intro-page.dark .top-nav,
.career-planning-intro-page.dark .process-card,
.career-planning-intro-page.dark .advantage-item,
.career-planning-intro-page.dark .user-card {
  background: #1e293b;
  color: #f1f5f9;
}
.career-planning-intro-page.dark .hero-tag,
.career-planning-intro-page.dark .user-tag {
  background: #334155;
  color: #e2e8f0;
}
.career-planning-intro-page.dark .tag-highlight {
  background: linear-gradient(90deg, #4f46e5, #3b82f6);
}

/* 顶部导航栏样式 */
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
  transition: all 0.3s ease;
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
.dropdown-item:hover {
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
  transition: all 0.3s ease;
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
  color: #2f54eb;
}
.user-menu .logout {
  color: #ff4d4f;
  border-top: 1px solid #e8e8e8;
}

/* 主视觉区域（左上角居左） */
.hero-section {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 60px 80px;
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 1s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-content {
  max-width: 600px;
  text-align: left;
}

.hero-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  justify-content: flex-start;
}
.hero-tag {
  display: inline-block;
  padding: 4px 12px;
  background: #f1f5f9;
  border-radius: 16px;
  font-size: 13px;
  color: #64748b;
  transition: all 0.3s ease;
}
.tag-highlight {
  background: linear-gradient(90deg, #2f54eb, #1890ff);
  color: #fff;
}

.hero-title {
  font-size: 38px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
  line-height: 1.2;
}
.career-planning-intro-page.dark .hero-title {
  color: #f1f5f9;
}

.hero-subtitle {
  font-size: 18px;
  color: #475569;
  margin-bottom: 16px;
  line-height: 1.5;
}
.career-planning-intro-page.dark .hero-subtitle {
  color: #cbd5e1;
}

.hero-tip {
  font-size: 15px;
  color: #64748b;
  margin-bottom: 28px;
  line-height: 1.4;
}
.career-planning-intro-page.dark .hero-tip {
  color: #94a3b8;
}

.hero-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-start;
}

.hero-actions .el-button {
  padding: 12px 28px;
  font-size: 15px;
  border-radius: 6px;
}

/* 流程步骤区域 */
.process-section {
  padding: 60px 0 20px 0;
  max-width: 100%;
  margin: 0 auto;
}

.river-container {
  position: relative;
  min-height: 500px;
  width: 100%;
  overflow: hidden;
}

.process-card {
  width: 200px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: absolute;
  z-index: 3;
  border: 1px solid #e8f4ff;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.step-1 { top: 60px; left: 10%; transform: rotate(-2deg); }
.step-2 { top: 120px; left: 28%; transform: rotate(3deg); }
.step-3 { top: 50px; left: 50%; transform: rotate(-1deg); }
.step-4 { top: 140px; left: 70%; transform: rotate(2deg); }
.step-5 { top: 70px; left: 85%; transform: rotate(-3deg); }

.process-card:hover {
  transform: translateY(-10px) scale(1.05) rotate(0deg);
  box-shadow: 0 12px 32px rgba(47, 84, 235, 0.2);
  border-color: #2f54eb;
}

.career-planning-intro-page.dark .process-card {
  background: rgba(30, 41, 59, 0.95);
  border-color: #1e40af;
}
.career-planning-intro-page.dark .process-card:hover {
  border-color: #3b82f6;
}

.step-number {
  position: absolute;
  top: -15px;
  left: -15px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2f54eb, #3b82f6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(47, 84, 235, 0.3);
  z-index: 4;
}

.step-1 .step-number { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.step-2 .step-number { background: linear-gradient(135deg, #3b82f6, #60a5fa); }
.step-3 .step-number { background: linear-gradient(135deg, #10b981, #34d399); }
.step-4 .step-number { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
.step-5 .step-number { background: linear-gradient(135deg, #ef4444, #f87171); }

.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 8px;
  padding-top: 10px;
}
.career-planning-intro-page.dark .step-title {
  color: #f1f5f9;
}

.step-desc {
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
}
.career-planning-intro-page.dark .step-desc {
  color: #cbd5e1;
}

/* 河流样式 */
.river {
  position: absolute;
  top: 100px;
  left: 0;
  width: 100%;
  height: 300px;
  background: linear-gradient(90deg, #87CEEB 0%, #B0E0E6 100%) !important;
  border-radius: 0;
  overflow: hidden;
  z-index: 1;
  background-image: 
    repeating-linear-gradient(
      0deg,
      rgba(255, 255, 255, 0.1) 0px,
      rgba(255, 255, 255, 0.1) 2px,
      transparent 2px,
      transparent 10px
    );
}
.career-planning-intro-page.dark .river {
  background: linear-gradient(90deg, #4682B4 0%, #5F9EA0 100%);
}

.water-ripple {
  position: absolute;
  width: 30px;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: ripple 8s linear infinite;
  top: calc(var(--i) * 12px);
  left: calc(var(--i) * 40px);
}

@keyframes ripple {
  0% { transform: translateX(0) rotate(0deg); opacity: 0.8; }
  100% { transform: translateX(1800px) rotate(360deg); opacity: 0; }
}

.wave {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 200%;
  height: 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  animation: waveAnimation 15s linear infinite;
}

.wave-1 { height: 15px; animation-duration: 8s; opacity: 0.3; }
.wave-2 { height: 25px; animation-duration: 12s; opacity: 0.2; bottom: 10px; }
.wave-3 { height: 20px; animation-duration: 15s; opacity: 0.1; bottom: 20px; }

@keyframes waveAnimation {
  0% { transform: translateX(0) translateZ(0) scaleY(1); }
  50% { transform: translateX(-50%) translateZ(0) scaleY(0.8); }
  100% { transform: translateX(-100%) translateZ(0) scaleY(1); }
}

.duck-container {
  position: absolute;
  z-index: 2;
  animation: duckSwimRect 20s linear infinite;
  top: 150px;
  left: 50px;
}

.duck {
  font-size: 36px;
  animation: duckFloat 3s ease-in-out infinite;
  position: relative;
  z-index: 1;
}

.duck-ripple {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 8px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  animation: duckRipple 2s ease-out infinite;
}

@keyframes duckRipple {
  0% { transform: translateX(-50%) scale(0.5); opacity: 0.8; }
  100% { transform: translateX(-50%) scale(2); opacity: 0; }
}

@keyframes duckFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-8px) rotate(3deg); }
}

@keyframes duckSwimRect {
  0% { left: 50px; top: 150px; }
  25% { left: 400px; top: 130px; }
  50% { left: 800px; top: 160px; }
  75% { left: 1200px; top: 140px; }
  100% { left: 1800px; top: 150px; }
}

.river-end {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  background: #ef4444;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.8);
  z-index: 2;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: translateY(-50%) scale(1); }
  50% { transform: translateY(-50%) scale(1.2); }
}

/* 核心优势模块 */
.advantage-section {
  max-width: 1400px;
  margin: 20px auto;
  padding: 0 80px;
  text-align: center;
}
.user-group-section {
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 80px;
  text-align: center;
}
.section-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 30px;
  position: relative;
}
.career-planning-intro-page.dark .section-title {
  color: #f1f5f9;
}
.section-title::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: #2f54eb;
  border-radius: 2px;
}
.advantage-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.advantage-item {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.3s ease;
}
.advantage-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}
.advantage-icon {
  font-size: 32px;
  margin-bottom: 12px;
}
.advantage-item h4 {
  font-size: 16px;
  color: #0f172a;
  margin-bottom: 8px;
}
.career-planning-intro-page.dark .advantage-item h4 {
  color: #f1f5f9;
}
.advantage-item p {
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
}
.career-planning-intro-page.dark .advantage-item p {
  color: #cbd5e1;
}

/* 适用人群模块（单列一行三分之二，左右交替分布） */
.user-list {
  display: flex;
  flex-direction: column;
  gap: 40px;
  padding: 20px 0;
  align-items: center;
  width: 100%;
}

.user-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 35px;
  background: #ffffff;
  border-radius: 20px;
  width: 93.333%; /* 原66.666%增长2/5后为93.333% */
  min-height: 304px; /* 原380px缩短1/5后为304px */
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  transition: all 0.5s ease;
  overflow: hidden;
  opacity: 0;
  margin: 0 auto;
}

/* 左侧卡片 */
.user-card.left {
  transform: translateX(-100px);
  margin-left: 0;
}

/* 右侧卡片 */
.user-card.right {
  transform: translateX(100px);
  margin-right: 0;
}

.user-card.fly-in {
  opacity: 1;
  transform: translateX(0);
  transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.career-planning-intro-page.dark .user-card {
  background: #1e293b;
}

.user-card:hover {
  transform: translateY(-8px) scale(1.01);
  box-shadow: 0 12px 35px rgba(47, 84, 235, 0.25);
}

.user-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  width: 100%;
  z-index: 2;
}

.user-icon {
  font-size: 48px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0f2fe, #bae6fd);
  border-radius: 50%;
  transition: all 0.3s ease;
  z-index: 2;
}

.user-badge {
  padding: 6px 12px;
  background: #f0f9ff;
  color: #2f54eb;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.career-planning-intro-page.dark .user-badge {
  background: #1e3a8a;
  color: #93c5fd;
}

.career-planning-intro-page.dark .user-icon {
  background: linear-gradient(135deg, #1e3a8a, #3b82f6);
}

.user-card:hover .user-icon {
  transform: scale(1.1) rotate(5deg);
}

.user-title {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 20px;
  z-index: 2;
}

.career-planning-intro-page.dark .user-title {
  color: #f1f5f9;
}

/* 功能特性列表 */
.user-features {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  width: 100%;
  z-index: 2;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 13px;
  color: #334155;
}

.career-planning-intro-page.dark .feature-item {
  background: #334155;
  color: #e2e8f0;
}

.feature-icon {
  font-size: 12px;
}

.user-desc {
  font-size: 15px;
  color: #475569;
  line-height: 1.8;
  z-index: 2;
  text-align: left;
  margin-bottom: 20px;
  width: 100%;
}

.career-planning-intro-page.dark .user-desc {
  color: #cbd5e1;
}

.user-card-bg {
  position: absolute;
  bottom: -40px;
  right: -40px;
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #2f54eb, #3b82f6);
  opacity: 0.1;
  border-radius: 50%;
  z-index: 1;
  transition: all 0.5s ease;
}

.user-card:hover .user-card-bg {
  transform: scale(1.8);
  opacity: 0.15;
}

/* 不同卡片渐变颜色 */
.user-list .user-card:nth-child(1) .user-icon { background: linear-gradient(135deg, #fef7fb, #fce7f3); }
.user-list .user-card:nth-child(2) .user-icon { background: linear-gradient(135deg, #f0f9ff, #e0f2fe); }
.user-list .user-card:nth-child(3) .user-icon { background: linear-gradient(135deg, #ecfdf5, #d1fae5); }
.user-list .user-card:nth-child(4) .user-icon { background: linear-gradient(135deg, #fffbeb, #fef3c7); }
.user-list .user-card:nth-child(5) .user-icon { background: linear-gradient(135deg, #fef2f2, #fee2e2); }

.career-planning-intro-page.dark .user-list .user-card:nth-child(1) .user-icon { background: linear-gradient(135deg, #831843, #be185d); }
.career-planning-intro-page.dark .user-list .user-card:nth-child(2) .user-icon { background: linear-gradient(135deg, #1e40af, #3b82f6); }
.career-planning-intro-page.dark .user-list .user-card:nth-child(3) .user-icon { background: linear-gradient(135deg, #065f46, #10b981); }
.career-planning-intro-page.dark .user-list .user-card:nth-child(4) .user-icon { background: linear-gradient(135deg, #92400e, #f59e0b); }
.career-planning-intro-page.dark .user-list .user-card:nth-child(5) .user-icon { background: linear-gradient(135deg, #991b1b, #ef4444); }

/* 回到顶部按钮 */
.back-top {
  position: fixed;
  bottom: 40px;
  right: 30px;
  width: 40px;
  height: 40px;
  background: #2f54eb;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 999;
  transition: all 0.3s ease;
}
.back-top:hover {
  background: #1d3ecf;
  transform: translateY(-4px);
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .hero-section {
    padding: 40px 20px;
  }
  .river-container {
    height: auto;
    min-height: 600px;
    padding: 40px 20px;
  }
  .river {
    height: 300px;
    top: 80px;
  }
  .duck {
    font-size: 28px;
  }
  .step-1 { left: 5%; top: 50px; }
  .step-2 { left: 20%; top: 150px; }
  .step-3 { left: 40%; top: 80px; }
  .step-4 { left: 60%; top: 180px; }
  .step-5 { left: 75%; top: 100px; }
  
  .advantage-list {
    grid-template-columns: repeat(2, 1fr);
  }
  .user-card {
    width: 90%; /* 在中等屏幕上宽度调整为90% */
    min-height: 280px; /* 响应式下高度同步调整 */
  }
  .nav-wrap {
    width: 95%;
  }
  .logo {
    margin-right: 20px;
  }
  .menu-item {
    margin: 0 8px;
  }
  .nav-search-wrap {
    width: 150px;
  }
}

@media (max-width: 768px) {
  .advantage-list {
    grid-template-columns: 1fr;
  }
  .nav-menu {
    display: none;
  }
  .river {
    height: 400px;
  }
  .process-card {
    position: relative;
    width: 80%;
    margin: 20px auto;
    left: 0 !important;
    top: 0 !important;
    transform: none !important;
  }
  .process-card:hover {
    transform: translateY(-10px) scale(1.02) !important;
  }
  .user-card {
    width: 95%; /* 在小屏幕上宽度调整为95% */
    padding: 25px;
    min-height: 260px; /* 响应式下高度同步调整 */
  }
  .user-icon {
    font-size: 40px;
    width: 70px;
    height: 70px;
  }
  .user-title {
    font-size: 20px;
  }
  .user-desc {
    font-size: 14px;
  }
  /* 移动端取消左右交替，统一居中 */
  .user-card.left, .user-card.right {
    transform: translateX(100px);
    margin: 0 auto;
  }
}
</style>