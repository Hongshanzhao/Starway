<template>
  <div class="student-ability-page">
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item" @click="$router.push('/')">首页</li>
            <li class="menu-item active" @click="$router.push('/student-ability')">职业规划</li>
            <li class="menu-item" @click="$router.push('/report-export')">报告导出</li>
          </ul>
        </div>
        <div class="nav-right">
          <div class="nav-search-wrap">
            <input type="text" class="nav-search-input" placeholder="搜索..." @keyup.enter="handleSearch" />
            <button class="nav-search-btn" @click="handleSearch">搜索</button>
          </div>
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
    </header>

    <div class="main-container">
      <div class="content-wrapper glass-panel">
        <h2 class="page-title">📋 学生信息与简历填写</h2>
        
        <div v-if="historyProfiles.length > 0" class="history-profile-section">
          <h3 class="section-subtitle">📊 历史能力画像</h3>
          <div class="history-profile-card">
            <div class="profile-info">
              <span class="profile-label">上次生成时间：</span>
              <span class="profile-value">{{ formatTime(historyProfiles[0].created_at) }}</span>
            </div>
            <el-button type="primary" @click="useHistoryProfile">使用上次生成的能力画像</el-button>
          </div>
        </div>
        
        <div class="basic-info-section">
          <h3 class="section-subtitle">个人基础信息</h3>
          <div class="form-row">
            <el-input v-model="formData.name" placeholder="姓名" size="large" class="form-item" clearable required />
            <el-input v-model="formData.phone" placeholder="手机号码" size="large" class="form-item" clearable />
            <el-input v-model="formData.email" placeholder="邮箱" size="large" class="form-item" clearable />
          </div>
        </div>

        <div class="input-mode-switch">
          <button class="mode-btn" :class="{ active: inputMode === 'manual' }" @click="inputMode = 'manual'">
            ✏️ 手动填写简历
          </button>
          <button class="mode-btn" :class="{ active: inputMode === 'upload' }" @click="inputMode = 'upload'">
            📤 上传简历文件
          </button>
        </div>

        <div v-if="inputMode === 'manual'" class="manual-input-section">
          <div class="form-tip"><i>💡</i> 请详细填写以下信息，AI将基于这些内容生成精准的能力画像</div>
          
          <div class="resume-block">
            <h3 class="block-title">🎓 教育经历</h3>
            <textarea v-model="formData.education" class="block-textarea" rows="2" placeholder="例如：清华大学 计算机科学与技术 本科 2021-2025" />
            <div class="block-hint">示例：北京大学 软件工程 硕士 2022-2025 | 绩点：3.8/4.0 | 专业排名：前5%</div>
          </div>

          <div class="resume-block">
            <h3 class="block-title">💼 工作/实习经历</h3>
            <textarea v-model="formData.work" class="block-textarea" rows="4" placeholder="请详细描述你的工作/实习经历，包括公司、职位、时间、职责和成果" />
            <div class="block-hint">示例：字节跳动 数据分析实习生 2024.03-2024.09 | 负责用户行为分析，搭建数据看板，优化推荐算法，提升点击率15%</div>
          </div>

          <div class="resume-block">
            <h3 class="block-title">📖 项目经历</h3>
            <textarea v-model="formData.project" class="block-textarea" rows="4" placeholder="请详细描述你的项目经历，包括项目名称、角色、技术栈、成果" />
            <div class="block-hint">示例：智能推荐系统开发 | 核心开发 | 技术栈：Python、TensorFlow、MySQL | 实现用户个性化推荐，准确率提升20%</div>
          </div>

          <div class="resume-block">
            <h3 class="block-title">🔧 技能与证书</h3>
            <textarea v-model="formData.skills_certs" class="block-textarea" rows="2" placeholder="例如：Python、Java、SQL、CET-6、PMP证书" />
            <div class="block-hint">示例：Python（精通）、Java（熟练）、SQL（精通）、Vue.js（掌握）、CET-6、计算机二级、PMP项目管理师</div>
          </div>

          <div class="resume-block">
            <h3 class="block-title">📝 自我总结</h3>
            <textarea v-model="formData.summary" class="block-textarea" rows="3" placeholder="请简要总结你的优势、特长、职业规划等" />
            <div class="block-hint">示例：具备扎实的计算机基础和数据分析能力，熟悉机器学习算法，有2年大型互联网公司实习经验，擅长数据驱动的决策分析，职业目标是成为资深数据分析师</div>
          </div>

          <div class="submit-actions">
            <el-button type="primary" size="large" @click="submitManualForm" :loading="submitting">
              提交并生成能力画像
            </el-button>
          </div>
        </div>

        <div v-if="inputMode === 'upload'" class="upload-section">
          <div v-if="historyFiles.length > 0" class="history-file-section">
            <div class="history-file-card">
              <div class="file-info">
                <span class="file-label">上次上传：</span>
                <span class="file-name">{{ historyFiles[0].file_name }}</span>
                <span class="file-time">({{ formatTime(historyFiles[0].upload_time) }})</span>
              </div>
              <el-button type="info" @click="useHistoryFile">使用此文件</el-button>
            </div>
          </div>
          
          <div class="upload-area" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleFileDrop">
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" style="display: none" @change="handleFileSelect" />
            <div class="upload-icon">📂</div>
            <div class="upload-text">拖拽简历文件到此处或点击上传</div>
            <div class="upload-tip">支持 PDF、Word 格式，最大 10MB</div>
          </div>

          <div v-if="uploadedFile" class="file-info">
            <span class="file-name">{{ uploadedFile.name }}</span>
            <span class="file-size">{{ (uploadedFile.size / 1024).toFixed(1) }} KB</span>
            <el-button type="text" @click="removeFile">移除</el-button>
          </div>

          <div class="submit-actions" v-if="uploadedFile">
            <el-button type="primary" size="large" @click="submitUploadFile" :loading="uploading">
              上传并生成能力画像
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const router = useRouter()

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const isUserMenuOpen = ref(false)
const darkMode = ref(localStorage.getItem('darkMode') === 'true')

// 从 token 解析 userId
const getUserIdFromToken = () => {
  const token = localStorage.getItem('token')
  if (token && token.startsWith('mock-token-')) {
    const parts = token.split('-')
    return parseInt(parts[parts.length - 1])
  }
  return null
}

const userId = ref(getUserIdFromToken())
const historyProfiles = ref([])
const historyFiles = ref([])

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  timeout: 30000
})

// 添加请求拦截器，自动添加 token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const formData = reactive({
  name: '',
  phone: '',
  email: '',
  education: '',
  work: '',
  project: '',
  skills_certs: '',
  summary: ''
})

const inputMode = ref('manual')
const uploadedFile = ref(null)
const fileInput = ref(null)
const submitting = ref(false)
const uploading = ref(false)

const formatTime = (timeStr) => {
  if (!timeStr) return '未知时间'
  const date = new Date(timeStr)
  return `${date.getFullYear()}-${(date.getMonth()+1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const loadHistoryProfiles = async () => {}
const loadHistoryFiles = async () => {}

const useHistoryProfile = () => {
  ElMessage.info('请先提交信息生成能力画像')
}
const useHistoryFile = async () => {
  ElMessage.info('请先上传简历文件')
}

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const handleLogout = () => {
  localStorage.clear()
  isLogin.value = false
  router.push('/')
  ElMessage.success('退出登录成功')
}

const toggleTheme = () => {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
  document.body.classList.toggle('dark', darkMode.value)
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

const handleSearch = () => {}

const triggerFileUpload = () => {
  fileInput.value.click()
}

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) validateAndSetFile(file)
}

const handleFileDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file) validateAndSetFile(file)
}

const validateAndSetFile = (file) => {
  const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 PDF 或 Word 文档')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }
  uploadedFile.value = file
}

const removeFile = () => {
  uploadedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const submitManualForm = async () => {
  // 检查登录状态
  if (!userId.value) {
    ElMessage.error('请先登录')
    router.push('/login')
    return
  }
  
  if (!formData.name) {
    ElMessage.warning('请填写姓名')
    return
  }
  
  submitting.value = true
  try {
    const payload = {
      user_id: userId.value,
      name: formData.name,
      phone: formData.phone,
      email: formData.email,
      education: formData.education,
      work: formData.work,
      project: formData.project,
      skills_certs: formData.skills_certs,
      summary: formData.summary
    }
    
    console.log('手动提交参数:', payload)
    const res = await api.post('/profile/submit', payload)
    console.log('手动提交响应:', res.data)
    
    if (res.data && res.data.student_id) {
      localStorage.setItem('studentId', res.data.student_id)
      ElMessage.success('信息提交成功，正在生成能力画像...')
      // 跳转到能力画像页面
      router.push({
        path: '/ability-analysis',
        query: { studentId: res.data.student_id }
      })
    } else {
      ElMessage.error('提交失败：' + (res.data.error || '未返回学生ID'))
    }
  } catch (err) {
    console.error('手动提交错误:', err)
    const errorMsg = err.response?.data?.error || err.message || '提交失败'
    ElMessage.error('提交失败：' + errorMsg)
  } finally {
    submitting.value = false
  }
}

const submitUploadFile = async () => {
  if (!userId.value) {
    ElMessage.error('请先登录')
    router.push('/login')
    return
  }
  
  if (!uploadedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadedFile.value)
    fd.append('user_id', userId.value)
    
    const res = await api.post('/profile/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    console.log('文件上传响应:', res.data)
    
    if (res.data && res.data.student_id) {
      localStorage.setItem('studentId', res.data.student_id)
      ElMessage.success('简历上传成功，正在生成能力画像...')
      router.push({
        path: '/ability-analysis',
        query: { studentId: res.data.student_id }
      })
    } else {
      ElMessage.error('上传失败：' + (res.data.error || '未返回学生ID'))
    }
  } catch (err) {
    console.error('文件上传错误:', err)
    const errorMsg = err.response?.data?.error || err.message || '上传失败'
    ElMessage.error('上传失败：' + errorMsg)
  } finally {
    uploading.value = false
  }
}

// 获取当前用户信息，确保 userId 正确
const fetchCurrentUser = async () => {
  try {
    const res = await api.get('/user')
    if (res.data && res.data.id) {
      userId.value = res.data.id
      localStorage.setItem('userId', userId.value)
      console.log('获取到用户ID:', userId.value)
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
  }
}

onMounted(async () => {
  // 应用主题
  if (darkMode.value) {
    document.body.classList.add('dark')
  }
  
  // 检查登录状态
  if (!isLogin.value) {
    ElMessageBox.confirm('请先登录后再填写信息', '提示', {
      confirmButtonText: '去登录',
      cancelButtonText: '返回首页',
      type: 'warning'
    }).then(() => {
      router.push('/login')
    }).catch(() => {
      router.push('/')
    })
    return
  }
  
  // 如果 userId 为空，尝试从 /api/user 获取
  if (!userId.value) {
    await fetchCurrentUser()
  }
  
  console.log('当前用户ID:', userId.value)
})
</script>


<style scoped>
.student-ability-page {
  width: 100%;
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: linear-gradient(145deg, #f9fafc 0%, #f0f3f8 100%);
  margin: 0;
  padding: 60px 0 0 0;
  color: #1a2639;
}

.top-nav {
  height: 60px;
  background: #ffffff;
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
.nav-left { display: flex; align-items: center; }
.logo { display: flex; align-items: center; margin-right: 40px; font-size: 18px; font-weight: bold; color: #000; }
.logo-icon { font-size: 24px; margin-right: 8px; }
.nav-menu { display: flex; list-style: none; margin: 0; padding: 0; }
.menu-item { margin: 0 15px; font-size: 14px; cursor: pointer; padding: 0 5px; position: relative; height: 60px; line-height: 60px; color: #000; transition: color 0.3s ease; }
.menu-item:hover { color: #2f54eb; }
.menu-item.active { color: #2f54eb; }
.menu-item.active::after { content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: #2f54eb; border-radius: 3px 3px 0 0; }
.dropdown { position: relative; }
.dropdown-menu { position: absolute; top: 100%; left: 0; width: 200px; background: #fff; box-shadow: 0 4px 16px rgba(0,0,0,0.12); border-radius: 8px; list-style: none; padding: 8px 0; margin: 0; display: none; z-index: 9999; }
.dropdown:hover .dropdown-menu { display: block; animation: fadeIn 0.3s ease; }
.dropdown-item { padding: 12px 20px; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; height: auto; line-height: normal; color: #333; transition: background 0.3s ease; }
.dropdown-item:hover { background: #f0f7ff; }
.color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.color-dot.red { background: #ff7a45; }
.color-dot.orange { background: #faad14; }
.color-dot.green { background: #52c41a; }
.color-dot.blue { background: #1890ff; }
.nav-right { display: flex; gap: 15px; align-items: center; }
.nav-search-wrap { display: flex; width: 200px; height: 24px; border-radius: 12px; overflow: hidden; border: 1px solid #e8e8e8; transition: border 0.3s ease; }
.nav-search-wrap:focus-within { border-color: #2f54eb; }
.nav-search-input { flex: 1; height: 100%; padding: 0 12px; border: none; outline: none; font-size: 12px; background: transparent; }
.nav-search-btn { width: 53px; height: 100%; background: #2f54eb; color: #fff; border: none; cursor: pointer; font-size: 12px; transition: background 0.3s ease; }
.nav-search-btn:hover { background: #1d39c4; }
.btn-toggle-theme { padding: 6px 10px; border: none; background: #f5f7fa; border-radius: 4px; cursor: pointer; color: #000; transition: all 0.3s ease; }
.btn-toggle-theme:hover { background: #e8e8e8; }
.btn-login { padding: 6px 15px; border: 1px solid #2f54eb; color: #2f54eb; background: #fff; border-radius: 4px; cursor: pointer; transition: all 0.3s ease; }
.btn-login:hover { background: #f0f7ff; }
.btn-register { padding: 6px 15px; border: none; color: #fff; background: #2f54eb; border-radius: 4px; cursor: pointer; transition: all 0.3s ease; }
.btn-register:hover { background: #1d39c4; }
.user-profile { position: relative; display: flex; align-items: center; }
.avatar { width: 36px; height: 36px; border-radius: 50%; cursor: pointer; border: 2px solid #f0f0f0; transition: border 0.3s ease; }
.avatar:hover { border-color: #2f54eb; }
.user-menu { position: absolute; top: 50px; right: 0; width: 120px; background: #fff; box-shadow: 0 4px 16px rgba(0,0,0,0.12); border-radius: 8px; z-index: 9999; animation: fadeIn 0.3s ease; }
.user-menu .menu-item { padding: 10px 15px; font-size: 14px; cursor: pointer; height: auto; line-height: normal; margin: 0; color: #333; transition: background 0.3s ease; }
.user-menu .menu-item:hover { background: #f0f7ff; color: #333; }
.user-menu .logout { color: #ff4d4f; border-top: 1px solid #f0f0f0; }

.main-container {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 30px 20px;
}

.content-wrapper {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 32px;
  box-shadow: 0 25px 50 -12px rgba(0, 0, 0, 0.15), inset 0 1px 2px rgba(255,255,255,0.6);
  padding: 40px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 32px 0;
  padding-bottom: 16px;
  border-bottom: 2px solid rgba(37, 99, 235, 0.1);
}

.section-subtitle {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.history-profile-section {
  margin-bottom: 32px;
  padding: 16px;
  background: rgba(240, 249, 255, 0.7);
  border-radius: 16px;
  border: 1px solid #e0e7ff;
}

.history-profile-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-label {
  font-weight: 500;
  color: #4b5563;
}

.profile-value {
  color: #1e40af;
  font-weight: 500;
}

.history-file-section {
  margin-bottom: 20px;
}

.history-file-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.file-label {
  font-weight: 500;
  color: #4b5563;
  margin-right: 8px;
}

.file-time {
  color: #94a3b8;
  font-size: 13px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 32px;
}

.form-item {
  flex: 1;
}

:deep(.form-item .el-input__wrapper) {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.02);
  border: 1px solid #edf2f7;
  transition: all 0.2s;
}

:deep(.form-item .el-input__wrapper:hover) {
  border-color: #2563eb;
  box-shadow: 0 8px 16px -8px rgba(37,99,235,0.2);
}

.input-mode-switch {
  display: flex;
  gap: 16px;
  margin: 24px 0;
}

.mode-btn {
  flex: 1;
  padding: 14px 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  font-size: 16px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  backdrop-filter: blur(4px);
}

.mode-btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
  box-shadow: 0 12px 20px -10px #2563eb;
}

.mode-btn:hover:not(.active) {
  background: #f8fafc;
  border-color: #94a3b8;
}

.form-tip {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 24px;
  padding: 12px;
  background: rgba(37, 99, 235, 0.05);
  border-radius: 12px;
}

.resume-block {
  margin-bottom: 28px;
}

.block-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 10px 0;
}

.block-textarea {
  width: 100%;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 15px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
  background: white;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.block-textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 4px rgba(37,99,235,0.1);
}

.block-hint {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 8px;
  padding-left: 8px;
}

.upload-area {
  border: 2px dashed #cbd5e1;
  border-radius: 32px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(255,255,255,0.5);
  margin-bottom: 24px;
}

.upload-area:hover {
  border-color: #2563eb;
  background: rgba(37,99,235,0.02);
  transform: scale(1.01);
}

.upload-icon {
  font-size: 56px;
  color: #94a3b8;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 20px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 8px;
}

.upload-tip {
  font-size: 14px;
  color: #64748b;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-radius: 16px;
  margin-bottom: 24px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 13px;
  color: #64748b;
}

.submit-actions {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  border: none;
  border-radius: 40px;
  padding: 12px 48px;
  font-weight: 600;
  font-size: 16px;
  box-shadow: 0 10px 20px -8px #2563eb;
  transition: all 0.3s;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 20px 30px -10px #2563eb;
}

:deep(.el-button--info) {
  border-radius: 8px;
  padding: 8px 16px;
}

@media (max-width: 768px) {
  .nav-wrap {
    width: 95%;
  }
  .nav-menu {
    display: none;
  }
  .form-row {
    flex-direction: column;
    gap: 16px;
  }
  .content-wrapper {
    padding: 20px;
  }
  .page-title {
    font-size: 24px;
  }
  .history-profile-card, .history-file-card {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>