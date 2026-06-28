<template>
  <div class="job-portrait-page">
    <!-- 固定顶部的导航栏 -->
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item" :class="{active: $route.path === '/'}" @click="$router.push('/')">首页</li>
            <li class="menu-item" :class="{active: $route.path === '/career-planning'}" @click="$router.push('/career-planning-intro')">职业规划</li>
            <li class="menu-item" :class="{active: $route.path === '/report-export'}" @click="$router.push('/report-export')">报告导出</li>
          </ul>
        </div>

        <div class="nav-right">
          <div class="nav-search-wrap">
            <input type="text" class="nav-search-input" placeholder="搜索职业方向、专业、院校、岗位类型" @keyup.enter="handleSearch" ref="searchInputRef">
            <button class="nav-search-btn" @click="handleSearch">搜索</button>
          </div>
          <button class="btn-toggle-theme" @click="toggleTheme">🌙</button>
          <button class="btn-login" @click="$router.push('/login')" v-if="!isLogin">登录</button>
          <button class="btn-register" @click="$router.push('/register')" v-if="!isLogin">注册</button>
          <div class="user-profile" v-if="isLogin">
            <img :src="userAvatar || 'https://picsum.photos/seed/avatar/40/40'" alt="用户头像" class="avatar" @click="toggleUserMenu">
            <div class="user-menu" v-show="isUserMenuOpen">
              <div class="menu-item" @click="$router.push('/profile')">个人中心</div>
              <div class="menu-item logout" @click="handleLogout">退出登录</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  
    <div class="job-portrait-container">
      <div v-if="loading" class="loading-container">
        <el-loading-spinner></el-loading-spinner>
        <p>正在加载岗位画像数据...</p>
      </div>
      
      <div v-else>
        <div class="page-header">
          <div class="breadcrumb">
            <span class="breadcrumb-item" @click="$router.push('/')">首页</span>
            <span class="separator">/</span>
            <span class="breadcrumb-item">{{ currentJob?.job_name || '岗位画像' }}</span>
            <span class="separator">/</span>
            <span class="breadcrumb-item current">岗位画像详情</span>
          </div>
          <div class="job-header-card">
            <h1 class="job-title">{{ currentJob?.job_name || '岗位画像' }}</h1>
            <div class="job-tag-container">
              <el-tag v-for="tag in getCoreTags()" :key="tag" size="medium" class="job-tag">{{ tag }}</el-tag>
            </div>
          </div>
        </div>
        
        <!-- 核心信息区域 -->
        <div class="core-info-section">
          <div class="ability-card">
            <el-card header="专业技能要求" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div v-for="(skill, index) in (currentJob?.skills || [])" :key="skill || index" class="skill-card" :style="{animationDelay: `${index * 0.1}s`}">
                  <i class="el-icon-s-tools skill-icon"></i> <span class="skill-text">{{ skill }}</span>
                </div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card">
            <el-card header="证书资质要求" shadow="hover" class="info-card certs-card">
              <div class="cert-grid vertical">
                <div v-for="(cert, index) in (currentJob?.certificates || [])" :key="cert || index" class="cert-card" :style="{animationDelay: `${index * 0.1}s`}">
                  <i class="el-icon-trophy cert-icon"></i> <span class="cert-text">{{ cert }}</span>
                </div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card" v-if="currentJob?.soft_abilities?.创新能力">
            <el-card header="创新能力要求" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div class="skill-card"><i class="el-icon-document skill-icon"></i> <span class="skill-text">{{ currentJob.soft_abilities.创新能力.description }}</span></div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card" v-if="currentJob?.soft_abilities?.学习能力">
            <el-card header="学习能力要求" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div class="skill-card"><i class="el-icon-document skill-icon"></i> <span class="skill-text">{{ currentJob.soft_abilities.学习能力.description }}</span></div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card" v-if="currentJob?.soft_abilities?.抗压能力">
            <el-card header="抗压能力要求" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div class="skill-card"><i class="el-icon-document skill-icon"></i> <span class="skill-text">{{ currentJob.soft_abilities.抗压能力.description }}</span></div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card" v-if="currentJob?.soft_abilities?.沟通能力">
            <el-card header="沟通能力要求" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div class="skill-card"><i class="el-icon-document skill-icon"></i> <span class="skill-text">{{ currentJob.soft_abilities.沟通能力.description }}</span></div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card" v-if="currentJob?.soft_abilities?.实习能力">
            <el-card header="实践能力要求" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div class="skill-card"><i class="el-icon-document skill-icon"></i> <span class="skill-text">{{ currentJob.soft_abilities.实习能力.description }}</span></div>
              </div>
            </el-card>
          </div>
          
          <div class="ability-card" v-for="(ability, key) in getOtherSoftAbilities()" :key="key">
            <el-card :header="`${key}要求`" shadow="hover" class="info-card skills-card">
              <div class="skill-grid vertical">
                <div class="skill-card"><i class="el-icon-user skill-icon"></i> <span class="skill-text">{{ ability.description }}</span></div>
              </div>
            </el-card>
          </div>
        </div>
        
        <!-- 岗位发展路径区域 -->
        <div class="career-path-section">
          <el-card header="岗位发展路径规划" shadow="hover" class="info-card path-card">
            <div class="path-header">
              <el-button type="primary" icon="el-icon-map-location" @click="openGraphDialog" class="graph-btn">查看岗位发展路径图谱</el-button>
              <p class="path-desc">清晰的职业发展路径，助力你的职业规划（鼠标悬浮查看晋升要求）</p>
            </div>
            
            <div class="path-content">
              <!-- 垂直晋升路径 -->
              <div class="path-column">
                <h3 class="path-column-title"><i class="el-icon-arrow-up"></i> 垂直晋升路径</h3>
                <div class="path-timeline">
                  <div v-if="jobGraphConfig.vertical.length === 0" class="empty-tip">暂无晋升路径数据</div>
                  <div v-else>
                    <div v-for="(item, index) in jobGraphConfig.vertical" :key="index" class="timeline-item" @mouseenter="showPromotionTip($event, item)" @mouseleave="hideTip">
                      <div class="timeline-dot" :style="{backgroundColor: getStepColor(index)}"></div>
                      <div class="timeline-content">
                        <div class="timeline-step">第{{ index + 1 }}阶段</div>
                        <div class="timeline-position">{{ item.job_name || item }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 横向换岗路径 -->
              <div class="path-column">
                <h3 class="path-column-title"><i class="el-icon-switch"></i> 换岗发展路径</h3>
                <div class="path-grid">
                  <div v-if="jobGraphConfig.switch.length === 0" class="empty-tip">暂无换岗路径数据</div>
                  <div v-else>
                    <div v-for="(item, index) in jobGraphConfig.switch" :key="index" class="switch-card" @mouseenter="showSwitchTip($event, item)" @mouseleave="hideTip">
                      <div class="switch-icon"><i class="el-icon-refresh"></i></div>
                      <div class="switch-position">{{ item.job_name || item }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 软能力雷达图区域 -->
        <div class="soft-ability-radar-section">
          <el-card header="岗位软能力要求雷达图" shadow="hover" class="info-card radar-card">
            <div ref="radarChartRef" class="radar-chart-container"></div>
          </el-card>
        </div>
        
        <!-- 岗位图谱弹窗 -->
        <el-dialog v-model="graphVisible" :title="`${currentJob?.job_name || '岗位'} - 职业发展路径图谱`" width="90%" center class="graph-dialog" append-to-body>
          <div ref="graphChartRef" class="graph-chart-container"></div>
        </el-dialog>
      </div>
    </div>
    
    <!-- 全局悬浮提示框 -->
    <Teleport to="body">
      <div v-if="tipVisible" class="floating-tooltip" :style="tipStyle">
        <div class="tooltip-title">{{ tipTitle }}</div>
        <div class="tooltip-content">{{ tipContent }}</div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

// 导航栏相关状态
const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const searchInputRef = ref(null)
const graphChartRef = ref(null)
const radarChartRef = ref(null)
const loading = ref(true)

// 岗位数据
const currentJob = ref({
  job_name: '',
  skills: [],
  certificates: [],
  soft_abilities: {},
  coreTags: []
})

// 发展路径数据
const jobGraphConfig = ref({
  vertical: [],
  switch: []
})

const graphVisible = ref(false)
let graphChart = null
let radarChart = null

// 悬浮提示相关
const tipVisible = ref(false)
const tipTitle = ref('')
const tipContent = ref('')
const tipStyle = ref({})
let hideTimer = null

const showPromotionTip = (event, item) => {
  if (hideTimer) clearTimeout(hideTimer)
  tipTitle.value = `📌 ${item.job_name || item} 晋升要求`
  tipContent.value = item.description || '暂无详细要求'
  
  const rect = event.target.closest('.timeline-item')?.getBoundingClientRect()
  if (rect) {
    tipStyle.value = {
      position: 'fixed',
      left: (rect.right + 15) + 'px',
      top: (rect.top + rect.height / 2 - 40) + 'px',
      zIndex: 99999
    }
  } else {
    tipStyle.value = {
      position: 'fixed',
      left: (event.clientX + 20) + 'px',
      top: (event.clientY - 40) + 'px',
      zIndex: 99999
    }
  }
  tipVisible.value = true
}

const showSwitchTip = (event, item) => {
  if (hideTimer) clearTimeout(hideTimer)
  tipTitle.value = `🔄 转岗方向：${item.job_name || item}`
  tipContent.value = item.description || '暂无详细说明'
  
  const rect = event.target.closest('.switch-card')?.getBoundingClientRect()
  if (rect) {
    tipStyle.value = {
      position: 'fixed',
      left: (rect.right + 15) + 'px',
      top: (rect.top + rect.height / 2 - 40) + 'px',
      zIndex: 99999
    }
  } else {
    tipStyle.value = {
      position: 'fixed',
      left: (event.clientX + 20) + 'px',
      top: (event.clientY - 40) + 'px',
      zIndex: 99999
    }
  }
  tipVisible.value = true
}

const hideTip = () => {
  hideTimer = setTimeout(() => {
    tipVisible.value = false
  }, 100)
}

// 导航栏方法
const toggleUserMenu = () => { isUserMenuOpen.value = !isUserMenuOpen.value }
const handleLogout = () => {
  localStorage.clear()
  isLogin.value = false
  router.push('/')
  ElMessage.success('退出登录成功')
}

const toggleTheme = () => {
  const darkMode = localStorage.getItem('darkMode') === 'true'
  localStorage.setItem('darkMode', !darkMode)
  if (!darkMode) document.body.classList.add('dark')
  else document.body.classList.remove('dark')
  ElMessage.success(`已切换${!darkMode ? '暗黑' : '默认'}主题`)
}

const handleSearch = () => {
  if (!searchInputRef.value) return
  const keyword = searchInputRef.value.value?.trim()
  if (!keyword) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  router.push({ path: '/search', query: { keyword } })
  searchInputRef.value.value = ''
  ElMessage.success(`正在搜索：${keyword}`)
}

// 辅助函数
const getStepColor = (index) => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#722ED1', '#F7BA1E']
  return colors[index % colors.length]
}

const getCoreTags = () => {
  const skills = currentJob.value?.skills || []
  if (skills.length > 0) {
    return skills.slice(0, 3).map(skill => {
      if (skill.includes('/')) return skill.split('/')[0]
      return skill
    })
  }
  return ['暂无标签']
}

const getOtherSoftAbilities = () => {
  const fixedAbilities = ['创新能力', '学习能力', '抗压能力', '沟通能力', '实习能力']
  const otherAbilities = {}
  const softAbilities = currentJob.value?.soft_abilities || {}
  for (const [key, value] of Object.entries(softAbilities)) {
    if (!fixedAbilities.includes(key) && value && value.description) {
      otherAbilities[key] = value
    }
  }
  return otherAbilities
}

// 雷达图
const initRadarChart = () => {
  if (!radarChartRef.value) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(radarChartRef.value)

  const softAbilities = currentJob.value?.soft_abilities || {}
  const abilityData = [
    { name: '创新能力', value: softAbilities.创新能力?.score || 0 },
    { name: '学习能力', value: softAbilities.学习能力?.score || 0 },
    { name: '抗压能力', value: softAbilities.抗压能力?.score || 0 },
    { name: '沟通能力', value: softAbilities.沟通能力?.score || 0 },
    { name: '实践能力', value: softAbilities.实习能力?.score || 0 }
  ]

  const option = {
    title: { text: `${currentJob.value?.job_name || '岗位'} 软能力要求评估`, left: 'center' },
    radar: { indicator: abilityData.map(item => ({ name: item.name, max: 5 })) },
    series: [{ type: 'radar', data: [{ value: abilityData.map(item => item.value), name: '岗位要求' }] }]
  }
  radarChart.setOption(option)
  window.addEventListener('resize', () => radarChart?.resize())
}

// 获取发展路径
const fetchJobPaths = async (jobName) => {
  try {
    const res = await axios.get(`/api/jobs/${encodeURIComponent(jobName)}/full-path`)
    const data = res.data
    
    if (data.vertical_path && Array.isArray(data.vertical_path)) {
      const verticalPaths = data.vertical_path.map(item => ({
        job_name: item.to_job,
        description: item.description
      }))
      
      const lateralPaths = (data.lateral_paths || []).map(item => ({
        job_name: item.job_name,
        description: item.description
      }))
      
      jobGraphConfig.value.vertical = verticalPaths
      jobGraphConfig.value.switch = lateralPaths
    } else {
      await fetchJobPathsLegacy(jobName)
    }
  } catch (error) {
    console.error('获取发展路径失败:', error)
    await fetchJobPathsLegacy(jobName)
  }
}

const fetchJobPathsLegacy = async (jobName) => {
  try {
    const verticalRes = await axios.get(`/api/jobs/${encodeURIComponent(jobName)}/vertical`)
    const lateralRes = await axios.get(`/api/jobs/${encodeURIComponent(jobName)}/lateral`)
    
    const verticalPaths = (verticalRes.data || []).map(item => ({
      job_name: item.to_job,
      description: item.description
    }))
    
    const lateralPaths = (lateralRes.data || []).map(item => ({
      job_name: item.to_job || item.job_name,
      description: item.description
    }))
    
    jobGraphConfig.value.vertical = verticalPaths
    jobGraphConfig.value.switch = lateralPaths
  } catch (error) {
    console.error('获取发展路径失败:', error)
    jobGraphConfig.value.vertical = []
    jobGraphConfig.value.switch = []
  }
}

// 获取岗位画像
const fetchJobProfile = async () => {
  try {
    loading.value = true
    const jobId = route.query.job_id
    const jobName = route.query.jobName
    
    let res
    if (jobId) {
      res = await axios.get(`/api/jobs/${jobId}/profile`)
    } else if (jobName) {
      const jobDetail = await axios.get(`/api/jobs/profile/${jobName}`)
      if (jobDetail.data.id) {
        res = await axios.get(`/api/jobs/${jobDetail.data.id}/profile`)
      } else {
        throw new Error('未找到岗位ID')
      }
    } else {
      const categories = await axios.get('/api/jobs/categories')
      const firstJob = categories.data[0] || {}
      currentJob.value = {
        job_name: firstJob.name || '数据分析师',
        skills: firstJob.skills || [],
        certificates: firstJob.certificates || [],
        soft_abilities: firstJob.soft_abilities || {},
        coreTags: firstJob.coreTags || []
      }
      loading.value = false
      await fetchJobPaths(currentJob.value.job_name)
      nextTick(() => initRadarChart())
      return
    }
    
    if (res && res.data) {
      currentJob.value = {
        ...currentJob.value,
        job_name: res.data.job_name || '',
        skills: res.data.skills || [],
        certificates: res.data.certificates || [],
        soft_abilities: res.data.soft_abilities || {},
        coreTags: res.data.coreTags || []
      }
    }
    await fetchJobPaths(currentJob.value.job_name)
  } catch (error) {
    console.error('获取岗位画像失败:', error)
    ElMessage.error('加载岗位画像失败，将显示默认数据')
    currentJob.value = {
      job_name: '数据分析师',
      skills: ['Python', 'SQL', 'Tableau', 'Excel', '数据分析'],
      certificates: ['计算机二级', 'CDA', '英语六级'],
      soft_abilities: {
        '创新能力': { score: 4, description: '需要具备独立思考能力...' },
        '学习能力': { score: 5, description: '数据领域技术迭代快...' },
        '抗压能力': { score: 3, description: '需应对多任务并行处理...' },
        '沟通能力': { score: 4, description: '需要将复杂的数据分析结果转化为易懂的业务结论...' },
        '实习能力': { score: 4, description: '具备实际项目操作经验...' }
      },
      coreTags: ['Python', 'SQL', '数据分析']
    }
    jobGraphConfig.value = {
      vertical: [{ job_name: '高级数据分析师', description: '需要3-5年经验' }],
      switch: [{ job_name: '数据产品经理', description: '需要补充产品思维' }]
    }
  } finally {
    loading.value = false
    nextTick(() => initRadarChart())
  }
}

// 图谱弹窗
const openGraphDialog = () => {
  graphVisible.value = true
  nextTick(() => initJobGraph())
}

const initJobGraph = () => {
  if (!graphChartRef.value) return
  if (graphChart) graphChart.dispose()
  graphChart = echarts.init(graphChartRef.value)

  const vertical = jobGraphConfig.value.vertical || []
  const lateral = jobGraphConfig.value.switch || []

  const nodes = []
  const links = []
  const nodeMap = new Map()

  vertical.forEach((item, index) => {
    const jobName = item.job_name || item
    if (!nodeMap.has(jobName)) {
      nodeMap.set(jobName, { id: jobName, name: jobName, category: 0 })
      nodes.push(nodeMap.get(jobName))
    }
    if (index > 0) {
      const prevJob = vertical[index - 1].job_name || vertical[index - 1]
      links.push({ source: prevJob, target: jobName, lineStyle: { color: '#409EFF', width: 2 }, label: { show: true, formatter: '晋升' } })
    }
  })

  lateral.forEach(item => {
    const jobName = item.job_name || item
    if (!nodeMap.has(jobName)) {
      nodeMap.set(jobName, { id: jobName, name: jobName, category: 1 })
      nodes.push(nodeMap.get(jobName))
    }
    const currentJobName = currentJob.value.job_name
    if (currentJobName && !links.some(l => l.source === currentJobName && l.target === jobName)) {
      links.push({ source: currentJobName, target: jobName, lineStyle: { color: '#67C23A', width: 2, type: 'dashed' }, label: { show: true, formatter: '换岗' } })
    }
  })

  if (nodes.length === 0) {
    nodes.push({ id: 'default', name: '暂无发展路径', category: 0, symbolSize: 60, itemStyle: { color: '#909399' } })
  }

  const option = {
    title: { text: `${currentJob.value?.job_name || '岗位'} - 职业发展路径图谱`, left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{ type: 'graph', layout: 'force', data: nodes, links: links, roam: true, label: { show: true, fontSize: 12, position: 'right' }, force: { repulsion: 500, edgeLength: 150 } }]
  }
  graphChart.setOption(option)
  window.addEventListener('resize', () => graphChart?.resize())
}

// 监听路由
watch([() => route.query.job_id, () => route.query.jobName], () => {
  fetchJobProfile()
}, { immediate: true })

// 生命周期
onMounted(() => {
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark')
  }
  fetchJobProfile()
})

onUnmounted(() => {
  if (graphChart) graphChart.dispose()
  if (radarChart) radarChart.dispose()
})
</script>

<style scoped>
.empty-tip {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

.floating-tooltip {
  position: fixed;
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  width: 320px;
  pointer-events: none;
  z-index: 99999;
  animation: fadeIn 0.15s ease-out;
  border-left: 4px solid #409EFF;
}

.floating-tooltip .tooltip-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #409EFF;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}

.floating-tooltip .tooltip-content {
  line-height: 1.6;
  font-size: 13px;
  color: #333;
  max-height: 300px;
  overflow-y: auto;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 原有样式保持不变 */
.promotion-tooltip, .switch-tooltip {
  display: none;
}
</style>

<style scoped>
/* 全局容器 */
.job-portrait-page {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", "PingFang SC", sans-serif;
  color: #303133;
  background: #fafbfc;
  margin: 0;
  padding: 0;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 600px;
  color: #606266;
}

/* ========== 导航栏样式 ========== */
:deep(.top-nav) {
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
}

:deep(.nav-wrap) {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

:deep(.nav-left) {
  display: flex;
  align-items: center;
}

:deep(.logo) {
  display: flex;
  align-items: center;
  margin-right: 40px;
  font-size: 18px;
  font-weight: bold;
  color: #000;
}

:deep(.logo-icon) {
  font-size: 24px;
  margin-right: 8px;
}

:deep(.nav-menu) {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

:deep(.menu-item) {
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

:deep(.menu-item:hover) {
  color: #2f54eb;
}

:deep(.menu-item.active) {
  color: #2f54eb;
}

:deep(.dropdown) {
  position: relative;
}

:deep(.dropdown-menu) {
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

:deep(.dropdown:hover .dropdown-menu) {
  display: block;
  animation: fadeIn 0.3s ease;
}

:deep(.dropdown-item) {
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

:deep(.dropdown-item:hover) {
  background: #f0f7ff;
}

:deep(.color-dot) {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

:deep(.color-dot.red) { background: #ff7a45; }
:deep(.color-dot.orange) { background: #faad14; }
:deep(.color-dot.green) { background: #52c41a; }
:deep(.color-dot.blue) { background: #1890ff; }

:deep(.nav-right) {
  display: flex;
  gap: 15px;
  align-items: center;
}

:deep(.nav-search-wrap) {
  display: flex;
  width: 200px;
  height: 24px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  transition: border 0.3s ease;
}

:deep(.nav-search-wrap:focus-within) {
  border-color: #2f54eb;
}

:deep(.nav-search-input) {
  flex: 1;
  height: 100%;
  padding: 0 12px;
  border: none;
  outline: none;
  font-size: 12px;
  background: transparent;
}

:deep(.nav-search-btn) {
  width: 53px;
  height: 100%;
  background: #2f54eb;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s ease;
}

:deep(.nav-search-btn:hover) {
  background: #1d39c4;
}

:deep(.btn-toggle-theme) {
  padding: 6px 10px;
  border: none;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  color: #000;
  transition: all 0.3s ease;
}

:deep(.btn-toggle-theme:hover) {
  background: #e8e8e8;
}

:deep(.btn-login) {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

:deep(.btn-login:hover) {
  background: #f0f7ff;
}

:deep(.btn-register) {
  padding: 6px 15px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

:deep(.btn-register:hover) {
  background: #1d39c4;
}

:deep(.user-profile) {
  position: relative;
  display: flex;
  align-items: center;
}

:deep(.avatar) {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid #f0f0f0;
  transition: border 0.3s ease;
}

:deep(.avatar:hover) {
  border-color: #2f54eb;
}

:deep(.user-menu) {
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

:deep(.user-menu .menu-item) {
  padding: 10px 15px;
  font-size: 14px;
  cursor: pointer;
  height: auto;
  line-height: normal;
  margin: 0;
  color: #333;
  transition: background 0.3s ease;
}

:deep(.user-menu .menu-item:hover) {
  background: #f0f7ff;
  color: #333;
}

:deep(.user-menu .logout) {
  color: #ff4d4f;
  border-top: 1px solid #f0f0f0;
}

/* ========== 页面内容样式 ========== */
.job-portrait-container {
  width: 1200px;
  margin: 0 auto;
  padding: 80px 20px 60px;
  min-height: calc(100vh - 60px);
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

/* 页面头部 - 面包屑 + 岗位标题 */
.page-header {
  padding: 24px 32px;
  background: #fff !important;
}

.breadcrumb {
  font-size: 14px;
  line-height: 1.8;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.breadcrumb-item {
  cursor: pointer;
  transition: all 0.3s ease;
}

.breadcrumb-item:hover {
  color: #409EFF;
  transform: translateY(-1px);
}

.separator {
  color: #909399;
  cursor: default;
}

.current {
  color: #303133;
  font-weight: 600;
  cursor: default;
}

/* 岗位标题卡片 */
.job-header-card {
  padding: 0 0 24px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0;
  border-bottom: 1px solid #f0f2f5;
}

.job-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 20px 0 0;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.job-tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0 20px;
}

.job-tag {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409EFF;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.job-tag:hover {
  background: #409EFF;
  color: #ffffff;
  transform: scale(1.05);
}

/* 通用卡片样式 */
:deep(.info-card) {
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.info-card .el-card__header) {
  background: #f9fafc;
  border-bottom: 1px solid #f0f2f5;
  padding: 16px 20px;
  font-weight: 600;
  font-size: 16px;
  color: #1f2937;
  border-radius: 8px 8px 0 0;
}

:deep(.info-card .el-card__body) {
  padding: 20px;
  flex: 1;
}

/* 核心信息区域 - 横向排列（可滚动） */
.core-info-section {
  display: flex;
  gap: 20px;
  padding: 24px 0;
  border-bottom: 1px solid #f0f2f5;
  margin-bottom: 24px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-color: #409EFF #f0f2f5;
  padding-bottom: 10px;
}

/* 自定义滚动条 */
.core-info-section::-webkit-scrollbar {
  height: 6px;
}

.core-info-section::-webkit-scrollbar-track {
  background: #f0f2f5;
  border-radius: 3px;
}

.core-info-section::-webkit-scrollbar-thumb {
  background: #409EFF;
  border-radius: 3px;
}

.core-info-section::-webkit-scrollbar-thumb:hover {
  background: #3399ff;
}

.ability-card {
  flex: 0 0 280px;
  height: 400px;
}

/* 技能卡片样式 - 竖向排列 */
.skill-grid.vertical {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.skill-card {
  background: linear-gradient(135deg, #e8f4f8 0%, #f0f9ff 100%);
  border-radius: 10px;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 1px solid rgba(64, 158, 255, 0.1);
  transition: all 0.4s ease;
  animation: fadeInUp 0.6s ease forwards;
  opacity: 0;
  transform: translateY(10px);
  flex: 1;
}

.skill-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 8px 16px rgba(64, 158, 255, 0.15);
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
}

.skill-icon {
  font-size: 20px;
  color: #409EFF;
  margin-bottom: 6px;
}

.skill-text {
  font-size: 12px;
  font-weight: 500;
  color: #1989fa;
  word-break: break-all;
  padding: 0 4px;
}

/* 证书卡片样式 - 竖向排列 */
.cert-grid.vertical {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.cert-card {
  background: linear-gradient(135deg, #fef7fb 0%, #fef0c7 100%);
  border-radius: 10px;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 1px solid rgba(230, 162, 60, 0.1);
  transition: all 0.4s ease;
  animation: fadeInUp 0.6s ease forwards;
  opacity: 0;
  transform: translateY(10px);
  flex: 1;
}

.cert-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 8px 16px rgba(230, 162, 60, 0.15);
  background: linear-gradient(135deg, #fef0c7 0%, #fde68a 100%);
}

.cert-icon {
  font-size: 20px;
  color: '#E6A23C';
  margin-bottom: 6px;
}

.cert-text {
  font-size: 12px;
  font-weight: 500;
  color: #d48806;
}

/* 职业发展路径区域 */
.career-path-section {
  margin-bottom: 24px;
}

.path-card {
  height: 100%;
}

.path-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.graph-btn {
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.3s ease;
}

.graph-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  background: linear-gradient(135deg, #3399ff 0%, #52c41a 100%);
}

.path-desc {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.path-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.path-column {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
}

.path-column-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-column-title i {
  color: #409EFF;
  font-size: 18px;
}

/* 时间线样式 */
.path-timeline {
  position: relative;
  padding-left: 30px;
}

.path-timeline::before {
  content: '';
  position: absolute;
  left: 10px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, #409EFF 0%, #67C23A 100%);
  border-radius: 1px;
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
  padding-bottom: 8px;
  cursor: pointer;
}

.timeline-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -30px;
  top: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.1);
  z-index: 1;
}

.timeline-content {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.timeline-content:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.timeline-step {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.timeline-position {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

/* 换岗路径网格 */
.path-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.switch-card {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(103, 194, 58, 0.1);
  transition: all 0.3s ease;
  position: relative;
  cursor: pointer;
}

.switch-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.15);
}

.switch-icon {
  font-size: 24px;
  color: '#67C23A';
  margin-bottom: 8px;
}

.switch-position {
  font-size: 14px;
  font-weight: 500;
  color: #52c41a;
}

/* 软能力雷达图区域样式 */
.soft-ability-radar-section {
  margin-bottom: 24px;
}

.radar-card {
  height: 100%;
}

.radar-chart-container {
  width: 100%;
  height: 500px;
  background: #ffffff !important;
}

/* 图谱弹窗样式 */
:deep(.custom-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

:deep(.custom-dialog .el-dialog__header) {
  background: #ffffff !important;
  border-bottom: 1px solid #f0f2f5;
  padding: 20px 24px;
}

:deep(.custom-dialog .el-dialog__title) {
  font-weight: 600;
  color: #1f2937;
  font-size: 18px;
}

:deep(.custom-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: #606266 !important;
}
:deep(.custom-dialog .el-dialog__headerbtn .el-dialog__close:hover) {
  color: #409EFF !important;
}

:deep(.custom-dialog .el-dialog__body) {
  padding: 24px;
  background: #ffffff !important;
}

.graph-chart-container {
  width: 100%;
  height: 600px;
  background: #ffffff !important;
}

/* 悬浮提示框 - 你要的样式 + 防遮挡 */
.promotion-tooltip {
  position: absolute;
  left: 110%;
  top: 0;
  width: 280px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  padding: 14px;
  z-index: 99999;
  border-left: 4px solid #409EFF;
  transition: all 0.2s ease;
}

.switch-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 240px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  padding: 12px;
  z-index: 99999;
  margin-bottom: 8px;
  border-top: 4px solid #67C23A;
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}
.tooltip-section {
  margin-bottom: 6px;
}
.label {
  font-size: 12px;
  color: #999;
  margin-bottom: 2px;
}
.text {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
}

/* 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式适配 */
@media (max-width: 1200px) {
  :deep(.nav-wrap), .job-portrait-container {
    width: 95%;
    padding-left: 20px;
    padding-right: 20px;
  }
  
  .graph-chart-container {
    height: 500px;
  }
  
  .radar-chart-container {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .job-header-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .path-content {
    grid-template-columns: 1fr;
  }
  
  .graph-chart-container {
    height: 400px;
  }
  
  .radar-chart-container {
    height: 400px;
  }
  
  .ability-card {
    flex: 0 0 250px;
    height: 350px;
  }
}

@media (max-width: 480px) {
  .ability-card {
    flex: 0 0 220px;
    height: 300px;
  }
  
  .path-grid {
    grid-template-columns: 1fr;
  }
  
  .radar-chart-container {
    height: 300px;
  }
}
</style>