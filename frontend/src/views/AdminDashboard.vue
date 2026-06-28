<template>
  <div class="admin-layout">
    <div class="sidebar">
      <div class="sidebar-logo">🎯 职业规划管理</div>
      <div class="menu-list">
        <div class="menu-item" :class="{ active: activeMenu === 'users' }" @click="activeMenu = 'users'">👥 用户管理</div>
        <div class="menu-item" :class="{ active: activeMenu === 'categories' }" @click="activeMenu = 'categories'">📂 岗位大类管理</div>
        <div class="menu-item" :class="{ active: activeMenu === 'jobs' }" @click="activeMenu = 'jobs'">💼 岗位数据管理</div>
        <div class="menu-item" :class="{ active: activeMenu === 'careerData' }" @click="activeMenu = 'careerData'">📊 用户生涯数据管理</div>
      </div>
    </div>

    <div class="main-content">
      <div class="content-header">
        <h2>{{ menuTitle }}</h2>
        <button @click="logout" class="btn btn-logout">退出登录</button>
      </div>

      <div class="content-body">
        <!-- 用户管理 -->
        <div v-show="activeMenu === 'users'">
          <div class="toolbar">
            <button @click="fetchUsers" class="btn btn-primary">刷新用户列表</button>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>手机号</th>
                <th>角色</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td>{{ u.id }}</td>
                <td>{{ u.username }}</td>
                <td>{{ u.phone || '-' }}</td>
                <td>
                  <span :class="['role-tag', u.role === 'admin' ? 'admin-tag' : 'user-tag']">
                    {{ u.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </td>
                <td>{{ u.is_active ? '正常' : '禁用' }}</td>
                <td class="action-btns">
                  <button @click="toggleRole(u.id, u.role)" class="btn btn-sm">切换角色</button>
                  <button @click="delUser(u.id)" class="btn btn-sm btn-danger">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 岗位大类 -->
        <div v-show="activeMenu === 'categories'">
          <div class="toolbar">
            <button @click="fetchCategories" class="btn btn-primary">刷新大类</button>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>大类名称</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in categories" :key="c.id">
                <td>{{ c.id }}</td>
                <td>{{ c.name }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 岗位数据 -->
        <div v-show="activeMenu === 'jobs'">
          <div class="toolbar">
            <button @click="fetchAllJobs" class="btn btn-primary">刷新全部岗位</button>
            <button @click="showAddJob = true" class="btn btn-success">➕ 新增岗位</button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>岗位名称</th>
                  <th>地址</th>
                  <th>薪资</th>
                  <th>公司</th>
                  <th>行业</th>
                  <th>规模</th>
                  <th>类型</th>
                  <th>岗位编码</th>
                  <th>更新日期</th>
                  <th>所属大类</th>
                  <th>来源地址</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="j in jobs" :key="j.id">
                  <td>{{ j.id }}</td>
                  <td>{{ j.job_name }}</td>
                  <td>{{ j.location || '-' }}</td>
                  <td>{{ j.salary_range || '-' }}</td>
                  <td>{{ j.company || '-' }}</td>
                  <td>{{ j.industry || '-' }}</td>
                  <td>{{ j.company_size || '-' }}</td>
                  <td>{{ j.company_type || '-' }}</td>
                  <td>{{ j.job_code || '-' }}</td>
                  <td>{{ j.updated_at || '-' }}</td>
                  <td>{{ getCategoryName(j.category_id) }}</td>
                  <td class="source-url">{{ j.source_url || '-' }}</td>
                  <td class="action-btns">
                    <button @click="openEditJob(j)" class="btn btn-sm">编辑</button>
                    <button @click="viewJobProfile(j.id)" class="btn btn-sm btn-primary">查看画像</button>
                    <button @click="deleteJob(j.id)" class="btn btn-sm btn-danger">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 🔥 用户生涯数据管理（与报告导出接口完全打通） -->
        <div v-show="activeMenu === 'careerData'">
          <div class="toolbar" style="display: flex; gap: 12px; align-items: center;">
            <button @click="fetchCareerData()" class="btn btn-primary">刷新生涯数据</button>
            <select v-model="selectedUserId" class="input" style="width: 200px;">
              <option value="">全部用户</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}（ID:{{ u.id }}）</option>
            </select>
            <select v-model="selectedDataType" class="input" style="width: 160px;">
              <option value="">全部类型</option>
              <option value="interest_test">兴趣测试报告</option>
              <option value="job_match">人岗匹配报告</option>
              <option value="career_plan">职业规划报告</option>
            </select>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>数据ID</th>
                  <th>所属用户</th>
                  <th>报告类型</th>
                  <th>报告标题</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="data in careerDataList" :key="data.id">
                  <td>{{ data.id }}</td>
                  <td>{{ getUserUsername(data.user_id) || '未知用户' }}</td>
                  <td>
                    <span :class="getDataTypeTagClass(data.data_type)">
                      {{ getDataTypeText(data.data_type) }}
                    </span>
                  </td>
                  <td>{{ data.title || '无标题' }}</td>
                  <td>{{ data.created_at || '-' }}</td>
                  <td class="action-btns">
                    <button @click="viewCareerDataDetail(data)" class="btn btn-sm btn-primary">查看详情</button>
                    <button @click="deleteCareerData(data.id)" class="btn btn-sm btn-danger">删除</button>
                  </td>
                </tr>
                <tr v-if="careerDataList.length === 0">
                  <td colspan="6" style="text-align: center; padding: 20px;">暂无生涯报告数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增/编辑岗位 -->
    <div v-show="showAddJob" class="modal-overlay">
      <div class="modal job-modal">
        <h3>{{ editJobId ? '编辑岗位' : '新增岗位' }}</h3>
        <input v-model="jobForm.job_name" placeholder="岗位名称" class="input" />
        <input v-model="jobForm.location" placeholder="地址" class="input" />
        <input v-model="jobForm.salary_range" placeholder="薪资范围" class="input" />
        <input v-model="jobForm.company" placeholder="公司名称" class="input" />
        <input v-model="jobForm.industry" placeholder="所属行业" class="input" />
        <input v-model="jobForm.company_size" placeholder="公司规模" class="input" />
        <input v-model="jobForm.company_type" placeholder="公司类型" class="input" />
        <input v-model="jobForm.job_code" placeholder="岗位编码" class="input" />

        <select v-model="jobForm.category_id" class="input">
          <option value="">请选择岗位大类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <textarea v-model="jobForm.job_description" placeholder="岗位详情" class="input"></textarea>
        <textarea v-model="jobForm.company_info" placeholder="公司详情" class="input"></textarea>
        <input v-model="jobForm.source_url" placeholder="岗位来源地址" class="input" />
        <input v-model="jobForm.updated_at" placeholder="更新日期" class="input" />
        <div class="modal-btns">
          <button @click="editJobId ? updateJob() : addJob()" class="btn btn-primary">{{ editJobId ? '确认修改' : '确认创建' }}</button>
          <button @click="closeJobModal" class="btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 岗位画像弹窗 -->
    <div v-show="showProfileModal" class="modal-overlay">
      <div class="modal profile-modal">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3>📊 岗位能力画像</h3>
          <button @click="closeProfileModal" class="btn btn-sm">关闭</button>
        </div>
        <div style="margin-top:10px;">
          <p><strong>岗位名称：</strong> {{ currentProfile.job_name }}</p>
        </div>
        <div style="margin-top:15px;">
          <h4>🧠 专业技能</h4>
          <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;">
            <span v-for="(s,i) in currentProfile.skills" :key="i" class="tag skill">{{ s }}</span>
          </div>
        </div>
        <div style="margin-top:15px;">
          <h4>🎓 相关证书</h4>
          <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;">
            <span v-for="(c,i) in currentProfile.certificates" :key="i" class="tag cert">{{ c }}</span>
          </div>
        </div>
        <div style="margin-top:15px;">
          <h4>💼 软实力要求</h4>
          <div style="margin-top:8px;">
            <div v-for="(val, key) in currentProfile.soft_abilities" :key="key" class="soft-item">
              <label>{{ key }}：</label>
              <div class="progress-bar">
                <div class="progress" :style="{ width: val*10 + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 生涯报告详情弹窗（与导出页完全一致） -->
    <div v-show="showCareerDataDetail" class="modal-overlay">
      <div class="modal profile-modal">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3>📋 {{ getDataTypeText(currentCareerData.data_type) }} - 详情</h3>
          <button @click="closeCareerDataDetail()" class="btn btn-sm">关闭</button>
        </div>
        <div style="margin-top:15px; text-align: left;">
          <p><strong>数据ID：</strong> {{ currentCareerData.id }}</p>
          <p><strong>所属用户：</strong> {{ getUserUsername(currentCareerData.user_id) || '未知用户' }}</p>
          <p><strong>报告标题：</strong> {{ currentCareerData.title || '无标题' }}</p>
          <p><strong>创建时间：</strong> {{ currentCareerData.created_at || '暂无' }}</p>
          <div style="margin-top:20px;">
            <h4>报告内容：</h4>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px; white-space: pre-wrap; word-break: break-all; max-height: 400px; overflow-y: auto;">
              {{ formatCareerDataContent(currentCareerData.content) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeMenu = ref('users')
const users = ref([])
const categories = ref([])
const jobs = ref([])

// 岗位相关
const showAddJob = ref(false)
const editJobId = ref(null)
const jobForm = ref({
  job_name: '', location: '', salary_range: '', company: '', industry: '',
  company_size: '', company_type: '', job_code: '', job_description: '',
  company_info: '', source_url: '', updated_at: '', category_id: ''
})

// 岗位画像相关
const showProfileModal = ref(false)
const currentProfile = ref({ job_name: '', skills: [], certificates: [], soft_abilities: {} })

// 🔥 生涯数据管理（与报告导出接口完全打通）
const careerDataList = ref([])
const selectedUserId = ref('')
const selectedDataType = ref('')
const showCareerDataDetail = ref(false)
const currentCareerData = ref({})

// 请求配置
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token'),
    'Content-Type': 'application/json',
  }
})

// 权限校验
const checkAdmin = () => {
  const role = localStorage.getItem('role')
  if (role !== 'admin') router.push('/')
  return role === 'admin'
}
const logout = () => { localStorage.clear(); router.push('/login') }

// 菜单标题
const menuTitle = computed(() => {
  const map = {
    users: '👥 用户管理',
    categories: '📂 岗位大类管理',
    jobs: '💼 岗位数据管理',
    careerData: '📊 用户生涯报告管理'
  }
  return map[activeMenu.value] || '管理面板'
})

// ====================== 通用工具 ======================
const getCategoryName = (cid) => {
  const cat = categories.value.find(c => c.id == cid)
  return cat ? cat.name : "未分类"
}

const getUserUsername = (userId) => {
  const user = users.value.find(u => u.id == userId)
  return user ? user.username : ''
}

// 🔥 与报告导出页完全一致的类型映射
const getDataTypeText = (type) => {
  const map = {
    'interest_test': '兴趣测试报告',
    'job_match': '人岗匹配报告',
    'career_plan': '职业规划报告'
  }
  return map[type] || '未知类型'
}

const getDataTypeTagClass = (type) => {
  const map = {
    'interest_test': 'tag interest-tag',
    'job_match': 'tag match-tag',
    'career_plan': 'tag plan-tag'
  }
  return map[type] || 'tag'
}

const formatCareerDataContent = (content) => {
  if (!content) return '暂无报告内容'
  try {
    if (typeof content === 'string') {
      return content
    }
    return JSON.stringify(content, null, 2)
  } catch (e) {
    return content
  }
}

// ====================== 用户管理 ======================
const fetchUsers = async () => {
  if (!checkAdmin()) return
  try { const res = await api.get('/admin/users'); users.value = res.data.users } catch (e) {}
}
const toggleRole = async (id, role) => {
  try { await api.put('/admin/users/'+id, { role: role === 'admin' ? 'user' : 'admin' }); fetchUsers() } catch (e) {}
}
const delUser = async (id) => {
  try { await api.delete('/admin/users/'+id); fetchUsers() } catch (e) {}
}

// ====================== 岗位大类 ======================
const fetchCategories = async () => {
  try { const res = await api.get('/admin/categories'); categories.value = res.data.list || [] } catch (e) {}
}

// ====================== 岗位管理 ======================
const fetchAllJobs = async () => {
  try { const res = await api.get('/admin/jobs'); jobs.value = res.data.list || [] } catch (e) {}
}
const closeJobModal = () => {
  showAddJob.value = false; editJobId.value = null
  jobForm.value = { job_name: '', location: '', salary_range: '', company: '', industry: '', company_size: '', company_type: '', job_code: '', job_description: '', company_info: '', source_url: '', updated_at: '', category_id: '' }
}
const addJob = async () => {
  try { await api.post('/admin/jobs', jobForm.value); closeJobModal(); fetchAllJobs() } catch (e) {}
}
const openEditJob = (j) => {
  editJobId.value = j.id; jobForm.value = { ...j }; showAddJob.value = true
}
const updateJob = async () => {
  try { await api.put('/admin/jobs/'+editJobId.value, jobForm.value); closeJobModal(); fetchAllJobs() } catch (e) {}
}
const deleteJob = async (id) => {
  try { await api.delete('/admin/jobs/'+id); fetchAllJobs() } catch (e) {}
}

const viewJobProfile = async (jobId) => {
  try {
    const res = await api.get('/jobs/'+jobId+'/profile')
    currentProfile.value = res.data
    showProfileModal.value = true
  } catch(e) {
    alert("暂无画像数据")
  }
}
const closeProfileModal = () => { showProfileModal.value = false }

// ====================== 🔥 生涯数据管理（修复404最终版） ======================
const fetchCareerData = async () => {
  try {
    careerDataList.value = []
    const userId = selectedUserId.value

    if (!userId) {
      alert("请先选择一个用户再刷新！")
      return
    }

    // 1. 兴趣测评
    let interest = []
    try {
      const { data } = await api.get(`/assessment/history/${userId}`)
      interest = (Array.isArray(data) ? data : []).map(item => ({
        id: 'interest_' + item.id,
        user_id: userId,
        data_type: 'interest_test',
        title: `霍兰德测评报告 #${item.id}`,
        created_at: item.created_at,
        content: item
      }))
    } catch {}

    // 2. 人岗匹配
    let match = []
    try {
      const { data } = await api.get(`/match/history/${userId}`)
      match = (data.history || []).map(item => ({
        id: 'match_' + item.id,
        user_id: userId,
        data_type: 'job_match',
        title: `${item.job_name} 匹配报告`,
        created_at: new Date(item.created_at * 1000).toLocaleString(),
        content: item
      }))
    } catch {}

    // 3. 职业规划报告
    let plan = []
    try {
      const { data } = await api.get(`/report/history/${userId}`)
      plan = (Array.isArray(data) ? data : []).map(item => ({
        id: 'plan_' + item.id,
        user_id: userId,
        data_type: 'career_plan',
        title: `${item.job_name} 职业生涯规划报告`,
        created_at: item.created_at,
        content: item.content
      }))
    } catch {}

    let all = [...interest, ...match, ...plan]
    if (selectedDataType.value) {
      all = all.filter(i => i.data_type === selectedDataType.value)
    }
    careerDataList.value = all
  } catch (e) {
    console.error("获取生涯报告失败", e)
    careerDataList.value = []
  }
}

const viewCareerDataDetail = (data) => {
  currentCareerData.value = { ...data }
  showCareerDataDetail.value = true
}

const closeCareerDataDetail = () => {
  showCareerDataDetail.value = false
  currentCareerData.value = {}
}

const deleteCareerData = async (dataId) => {
  if (!confirm('确定删除这条报告？')) return
  try {
    const type = dataId.split('_')[0]
    const realId = dataId.split('_')[1]

    if (type === 'interest') await api.delete(`/assessment/${realId}`)
    if (type === 'match') await api.delete(`/match/${realId}`)
    if (type === 'plan') await api.delete(`/report/${realId}`)

    fetchCareerData()
    alert("删除成功！")
  } catch (e) {
    alert("删除失败：后端未实现该删除接口")
  }
}

onMounted(() => {
  checkAdmin()
  fetchUsers()
  fetchCategories()
  fetchAllJobs()
})
</script>

<style scoped>
.admin-layout { display: flex; width: 100vw; height: 100vh; overflow: hidden; background: #f5f7fa; }
.sidebar { width: 240px; background: #2f54eb; color: #fff; display: flex; flex-direction: column; }
.sidebar-logo { padding: 24px 20px; font-size: 18px; font-weight: bold; background: #1d39c4; }
.menu-list { flex: 1; padding-top: 20px; }
.menu-item { padding: 14px 20px; font-size: 15px; cursor: pointer; }
.menu-item:hover { background: #4065f7; }
.menu-item.active { background: #fff; color: #2f54eb; font-weight: bold; }
.main-content { flex: 1; display: flex; flex-direction: column; overflow: auto; }
.content-header { background: #fff; padding: 20px 30px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.content-body { padding: 25px 30px; }
.toolbar { margin-bottom: 18px; }

.table-container { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.data-table th, .data-table td {
  white-space: nowrap;
  border: 1px solid #eee;
  padding: 10px 12px;
  font-size: 14px;
  text-align: left;
}
.data-table th { background: #f8f9fa; }

.source-url {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.admin-tag { background: #e6f7ff; color: #1890ff; }
.user-tag { background: #f6ffed; color: #52c41a; }

/* 🔥 报告类型标签（与导出页一致） */
.tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.interest-tag { background: #e8f4f8; color: #4299e1; }
.match-tag { background: #f6ffed; color: #00b42a; }
.plan-tag { background: #fff7e6; color: #fa8c16; }

.action-btns { display: flex; gap: 6px; white-space: nowrap; }
.btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-sm { padding: 4px 8px; font-size: 12px; }
.btn-primary { background: #2f54eb; color: #fff; }
.btn-danger { background: #ff4d4f; color: #fff; }
.btn-success { background: #00b42a; color: #fff; }
.btn-logout { background: #999; color: #fff; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.modal { background: #fff; width: 500px; padding: 30px; border-radius: 10px; max-height: 90vh; overflow-y: auto; }
.job-modal { width: 750px; }
.profile-modal { width: 750px; }
.input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; }
.modal-btns { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }

.skill { background: #e6f7ff; color: #1890ff; border-radius: 20px; padding: 4px 10px; font-size: 12px; }
.cert { background: #f6ffed; color: #00b42a; border-radius: 20px; padding: 4px 10px; font-size: 12px; }
.soft-item { margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
.soft-item label { width: 100px; }
.progress-bar { width: 100%; height: 10px; background: #eee; border-radius: 5px; overflow: hidden; }
.progress { height: 100%; background: #2f54eb; }
</style>