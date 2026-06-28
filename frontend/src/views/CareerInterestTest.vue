<template>
  <div class="career-test">
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

    <div class="test-subheader">
      <div class="subheader-wrap">
        <div class="page-title">
          <span class="title-icon">🧭</span>
          <h1>职业测评</h1>
        </div>
        <div class="page-nav">
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">加载中...</div>
    </div>

    <section class="test-intro" v-if="!loading && !testStarted && !testCompleted">
      <div class="intro-wrap">
        <div class="intro-card">
          <div class="intro-header">
            <h2>职业测评</h2>
            <p class="intro-subtitle">了解你的职业倾向，找到适合的职业方向</p>
          </div>
          <div class="intro-content">
            <div class="theory-desc">
              <h3>职业测评理论</h3>
              <p>
                职业测评基于霍兰德职业兴趣理论，从六个维度（现实型、研究型、艺术型、社会型、企业型、常规型）
                评估你的职业倾向、能力特点和人格特质，帮助人们找到与自身特质相匹配的职业方向。
              </p>
            </div>
            
            <div class="type-cards">
              <div class="type-card" v-for="type in interestTypes" :key="type.code">
                <div class="type-icon">{{ type.icon }}</div>
                <div class="type-info">
                  <h4>{{ type.name }}({{ type.code }})</h4>
                  <p>{{ type.desc }}</p>
                </div>
              </div>
            </div>
            
            <div class="test-rules">
              <h3>测评规则</h3>
              <ul>
                <li>本测评共{{ testQuestions.length }}道题目，预计耗时10-15分钟</li>
                <li>请根据自身实际情况选择符合程度，无需过度思考</li>
                <li>答案无对错之分，仅反映你的职业倾向</li>
                <li>完成后可查看详细的测评报告和职业推荐（得分范围：0-100分）</li>
              </ul>
            </div>
          </div>
          
          <div class="intro-footer">
            <button class="start-btn" @click="startTest">开始测评</button>
            <p class="tips">测评结果仅用于个人职业规划参考，我们将严格保护你的隐私</p>
          </div>
        </div>
      </div>
    </section>

    <section class="test-questions" v-if="!loading && testStarted && !testCompleted">
      <div class="questions-wrap">
        <div class="progress-bar">
          <div class="progress-info">
            <span>答题进度：{{ currentQuestionIndex + 1 }}/{{ testQuestions.length }}</span>
            <span>剩余时间：{{ remainingTime }}秒</span>
          </div>
          <div class="progress-container">
            <div 
              class="progress-fill" 
              :style="{ width: (currentQuestionIndex + 1) / testQuestions.length * 100 + '%' }"
            ></div>
          </div>
        </div>

        <div class="question-card">
          <div class="question-header">
            <h3>第 {{ currentQuestionIndex + 1 }} 题</h3>
          </div>
          <div class="question-content">
            <p class="question-text">{{ currentQuestion.question }}</p>
            <div class="options-list">
              <label 
                class="option-item" 
                v-for="(option, idx) in options" 
                :key="idx"
              >
                <input 
                  type="radio" 
                  name="answer" 
                  :value="idx + 1" 
                  v-model="currentAnswer"
                  @change="selectAnswerAndNext(idx + 1)"
                >
                <span class="option-text">{{ option.label }} - {{ option.desc }}</span>
              </label>
            </div>
          </div>
          <div class="question-footer">
            <button 
              class="prev-btn" 
              @click="prevQuestion" 
              :disabled="currentQuestionIndex === 0"
            >
              上一题
            </button>
            <button 
              class="next-btn" 
              @click="nextQuestion"
              :disabled="currentAnswer === 0"
            >
              {{ currentQuestionIndex === testQuestions.length - 1 ? '提交测评' : '下一题' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="test-result" v-if="!loading && testCompleted">
      <div class="result-wrap">
        <div class="result-header">
          <h2>你的职业测评结果</h2>
          <p class="result-subtitle">基于你的答题情况，生成专属职业分析</p>
        </div>

        <div class="result-chart">
          <h3>职业维度得分（0-100分）</h3>
          <div class="chart-container">
            <div class="radar-chart">
              <div class="radar-grid"></div>
              <div class="radar-axis" v-for="(axis, idx) in radarAxes" :key="idx" :style="getRadarAxisStyle(idx)">
                <div class="axis-label">{{ axis.label }}</div>
                <div class="axis-line"></div>
                <div 
                  class="axis-point" 
                  :style="{ 
                    bottom: `${axis.score}%`,
                    transform: 'translateX(-50%)'
                  }"
                ></div>
              </div>
              <div class="radar-fill" :style="getRadarFillStyle()"></div>
            </div>
          </div>
        </div>

        <div class="core-result">
          <div class="core-card">
            <div class="core-icon">{{ topType.icon }}</div>
            <div class="core-content">
              <h3>你的主导职业类型：{{ topType.name }}</h3>
              <p class="core-desc">{{ topType.detailDesc }}</p>
              <div class="core-tips">
                <h4>适合你的职业方向：</h4>
                <div class="career-tags">
                  <span class="career-tag" v-for="career in topType.careers" :key="career">{{ career }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="llm-recommendation" v-if="recommendation">
          <div class="recommendation-card">
            <h3>AI 生成的个性化职业推荐</h3>
            <div class="recommendation-content" v-html="formatRecommendation(recommendation)"></div>
          </div>
        </div>

        <div class="detail-analysis">
          <h3>各维度详细分析（0-100分）</h3>
          <div class="analysis-cards">
            <div 
              class="analysis-card" 
              v-for="type in interestTypes" 
              :key="type.code"
              :class="{ top: type.code === topType.code }"
            >
              <div class="analysis-header">
                <span class="type-icon">{{ type.icon }}</span>
                <h4>{{ type.name }}({{ type.code }})</h4>
                <span class="score-tag">{{ dimensionScores[type.code] || 0 }}分</span>
              </div>
              <div class="analysis-content">
                <p>{{ type.analysis }}</p>
                <div class="career-recommend" v-if="type.careers.length > 0">
                  <p class="recommend-title">推荐职业：</p>
                  <div class="recommend-list">
                    <span v-for="career in type.careers.slice(0, 5)" :key="career">{{ career }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <button class="restart-btn" @click="restartTest">重新测评</button>
          <!-- 这里改为：查看详情 -->
          <button class="export-btn" @click="exportReport">查看详情</button>
          <button class="career-plan-btn" @click="goToMatchResult">
            📋 进行人岗匹配分析
          </button>
        </div>
      </div>
    </section>

    <div class="report-modal" v-if="showReportModal">
      <div class="modal-mask" @click="showReportModal = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>职业测评报告</h3>
          <button class="close-btn" @click="showReportModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="report-header">
            <p class="report-date">测评时间：{{ testResultDate }}</p>
            <h2>职业测评报告</h2>
          </div>
          
          <div class="report-section">
            <h3>一、测评结果总览</h3>
            <p>你的主导职业类型：<strong>{{ topType.name }}({{ topType.code }})</strong></p>
            <p>各维度得分（0-100分）：</p>
            <div class="score-table">
              <div class="table-row header">
                <div class="table-cell">类型</div>
                <div class="table-cell">代码</div>
                <div class="table-cell">得分</div>
                <div class="table-cell">等级</div>
              </div>
              <div class="table-row" v-for="type in interestTypes" :key="type.code">
                <div class="table-cell">{{ type.name }}</div>
                <div class="table-cell">{{ type.code }}</div>
                <div class="table-cell">{{ dimensionScores[type.code] || 0 }}</div>
                <div class="table-cell">{{ getScoreLevel(dimensionScores[type.code] || 0) }}</div>
              </div>
            </div>
          </div>
          
          <div class="report-section">
            <h3>二、主导类型分析</h3>
            <p>{{ topType.detailDesc }}</p>
            <p>核心优势：{{ topType.advantages }}</p>
            <p>发展建议：{{ topType.suggestions }}</p>
          </div>
          
          <div class="report-section" v-if="recommendation">
            <h3>三、AI 个性化职业推荐</h3>
            <div v-html="formatRecommendation(recommendation)"></div>
          </div>
          
          <div class="report-section">
            <h3>四、职业推荐</h3>
            <div class="career-group">
              <h4>高度匹配职业：</h4>
              <div class="career-list">
                <span v-for="career in topType.careers.slice(0, 8)" :key="career">{{ career }}</span>
              </div>
            </div>
            <div class="career-group">
              <h4>较匹配职业：</h4>
              <div class="career-list">
                <span v-for="(type, idx) in interestTypes.filter(t => t.code !== topType.code).slice(0, 2)" :key="idx">
                  {{ type.name }}：{{ type.careers.slice(0, 3).join('、') }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="report-section">
            <h3>五、发展建议</h3>
            <ul class="suggestion-list">
              <li>根据职业倾向选择专业课程和实践活动</li>
              <li>多了解目标职业的发展前景和能力要求</li>
              <li>参加相关的实习和社会实践，积累经验</li>
              <li>持续提升自身能力，匹配目标职业要求</li>
              <li>定期重新测评，跟踪职业倾向变化</li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <!-- 已删除 打印报告、下载PDF 按钮，只保留关闭 -->
          <button class="close-btn" @click="showReportModal = false">关闭</button>
        </div>
      </div>
    </div>

    <footer class="page-footer">
      <div class="footer-wrap">
        © 2026 大学生职业规划系统 | 职业测评基于霍兰德职业兴趣理论开发
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const API_BASE_URL = '/api/assessment'
const loading = ref(true)

const isLogin = ref(!!localStorage.getItem('token'))
const userAvatar = ref(localStorage.getItem('avatar') || '')
const userId = ref(localStorage.getItem('user_id') || '')
const isUserMenuOpen = ref(false)

watch(
  () => route.path,
  () => {
    isLogin.value = !!localStorage.getItem('token')
    userAvatar.value = localStorage.getItem('avatar') || ''
    userId.value = localStorage.getItem('user_id') || ''
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
  localStorage.removeItem('user_id')
  isLogin.value = false
  isUserMenuOpen.value = false
  router.push('/')
  ElMessage.success('退出登录成功')
}

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
    ElMessage.success(`正在搜索：${keyword}`)
  } else {
    ElMessage.warning('请输入搜索关键词')
  }
}

const DRAFT_STORAGE_KEY = 'careerInterestTestDraft'
const RESULT_STORAGE_KEY = 'careerInterestTestResult'

const testStarted = ref(false)
const testCompleted = ref(false)
const currentQuestionIndex = ref(0)
const currentAnswer = ref(0)
const answers = ref({})
const showReportModal = ref(false)
const testResultDate = ref('')
const dimensionScores = ref({
  R: 0, I: 0, A: 0, S: 0, E: 0, C: 0
})      
const recommendation = ref('')

const totalTime = 900
const remainingTime = ref(totalTime)
let timer = null

const interestTypes = ref([
  {
    code: 'R', name: '现实型', icon: '🛠️',
    desc: '偏好与物体打交道，喜欢具体的、实际操作性的工作',
    detailDesc: '你属于现实型人格，偏好与物体打交道，喜欢具体的、实际操作性的工作。你动手能力强，做事踏实，喜欢使用工具和机械，偏好具体任务，不善言辞，做事保守，较为谦虚。喜欢独立做事，注重实际效果。',
    analysis: '你的现实型维度得分较高，说明你具备较强的动手能力和实操能力，喜欢具体、明确的任务，不喜欢抽象的理论思考。你适合从事需要实际操作的职业，能够在具体的工作中找到成就感。',
    careers: ['机械维修师', '电工', '土木工程师', '建筑工人', '厨师', '司机', '消防员', '园艺师', '飞行员', '机械设计师'],
    advantages: '动手能力强、务实、细心、有耐心、执行力强',
    suggestions: '可以重点关注工程技术、手工操作、技术维修等领域的职业发展，注重专业技能的提升和实践经验的积累。'
  },
  {
    code: 'I', name: '研究型', icon: '🔬',
    desc: '喜欢智力活动和抽象推理，乐于探索和解决复杂问题',
    detailDesc: '你属于研究型人格，喜欢智力活动和抽象推理，乐于探索和解决复杂问题。你好奇心强，追求知识，喜欢独立思考和研究，逻辑思维能力强，做事严谨，注重分析和推理。不喜欢繁琐的行政事务和重复性工作。',
    analysis: '你的研究型维度得分较高，说明你具备较强的逻辑思维和分析能力，喜欢探索未知领域，善于发现问题和解决问题。你适合从事需要深度思考和研究的职业，能够在学术研究和技术研发中找到价值。',
    careers: ['科研人员', '数据分析师', '软件工程师', '医生', '大学教师', '心理学家', '化学家', '生物学家', '数学家', '统计学家'],
    advantages: '逻辑思维强、好奇心重、善于分析、学习能力强、追求真理',
    suggestions: '适合从事科研、数据分析、学术研究、技术研发等领域的工作，建议继续深造提升专业水平，保持对新知识的探索精神。'
  },
  {
    code: 'A', name: '艺术型', icon: '🎨',
    desc: '喜欢创造性的表达，追求美感和独特性，富有想象力',
    detailDesc: '你属于艺术型人格，喜欢创造性的表达，追求美感和独特性，富有想象力。你情感丰富，直觉敏锐，喜欢通过各种艺术形式表达自己，不拘小节，喜欢自由的工作环境，不喜欢受规则束缚。',
    analysis: '你的艺术型维度得分较高，说明你具备较强的创造力和想象力，对美有独特的追求，善于用艺术的方式表达自己。你适合从事需要创意和表达的职业，能够在艺术创作和审美设计中实现自我价值。',
    careers: ['设计师', '摄影师', '音乐家', '作家', '画家', '演员', '导演', '广告创意', '时尚编辑', '室内设计师'],
    advantages: '创造力强、想象力丰富、审美能力高、情感细腻、表达能力强',
    suggestions: '适合从事设计、艺术创作、文化创意等领域的工作，保持创作热情，不断提升审美水平和创意能力。'
  },
  {
    code: 'S', name: '社会型', icon: '🤝',
    desc: '喜欢与人交往，乐于助人，关心社会问题，渴望发挥社会作用',
    detailDesc: '你属于社会型人格，喜欢与人交往，乐于助人，关心社会问题，渴望发挥社会作用。你善于沟通，有同理心，喜欢帮助他人解决问题，乐于从事教育、咨询、公益等工作，具有较强的社会责任感。',
    analysis: '你的社会型维度得分较高，说明你具备良好的沟通能力和人际交往能力，乐于助人，有较强的同理心和社会责任感。你适合从事与人打交道的职业，能够在帮助他人和服务社会中获得满足感。',
    careers: ['教师', '心理咨询师', '社会工作者', '医生', '护士', '人力资源专员', '培训师', '公益志愿者', '客服主管', '职业规划师'],
    advantages: '沟通能力强、有同理心、乐于助人、有耐心、善于倾听',
    suggestions: '适合从事教育、医疗、咨询、公益、人力资源等领域的工作，注重沟通技巧和服务意识的提升。'
  },
  {
    code: 'E', name: '企业型', icon: '💼',
    desc: '喜欢影响、说服和领导他人，追求成功和成就感',
    detailDesc: '你属于企业型人格，喜欢影响、说服和领导他人，追求成功和成就感。你自信果断，有领导才能，喜欢竞争和挑战，目标明确，注重效率和结果，乐于从事管理和销售类工作。',
    analysis: '你的企业型维度得分较高，说明你具备较强的领导能力和决策能力，有进取心，喜欢挑战和竞争，追求成功和成就感。你适合从事管理、销售、创业等职业，能够在带领团队和实现目标中体现价值。',
    careers: ['企业家', '销售经理', '市场营销总监', '人力资源总监', '项目经理', '律师', '公关经理', '行政主管', '投资顾问', '职业经理人'],
    advantages: '领导力强、决策果断、目标导向、沟通能力强、抗压能力强',
    suggestions: '适合从事管理、销售、创业、商务等领域的工作，注重领导力和商业思维的培养，积累管理经验。'
  },
  {
    code: 'C', name: '常规型', icon: '📋',
    desc: '喜欢有规则的、有序的工作，注重细节和准确性',
    detailDesc: '你属于常规型人格，喜欢有规则的、有序的工作，注重细节和准确性。你做事认真细致，有责任心，喜欢按部就班地完成任务，善于处理数据和文书工作，注重秩序和规范。',
    analysis: '你的常规型维度得分较高，说明你具备较强的细心和耐心，做事认真负责，注重规则和秩序，善于处理细节性的工作。你适合从事需要细心和规范的职业，能够在有序的工作环境中发挥优势。',
    careers: ['会计', '出纳', '行政文员', '档案管理员', '图书管理员', '数据录入员', '银行柜员', '秘书', '统计员', '审计员'],
    advantages: '细心认真、有耐心、责任心强、遵守规则、执行力强',
    suggestions: '适合从事财务、行政、档案管理、数据处理等领域的工作，注重专业技能和细致程度的提升。'
  }
])

const testQuestions = ref([])
const options = ref([
  { label: '非常不符合', desc: '完全不符合我的情况', score: 20 },
  { label: '不太符合', desc: '不太符合我的情况', score: 40 },
  { label: '一般', desc: '不确定是否符合', score: 60 },
  { label: '比较符合', desc: '比较符合我的情况', score: 80 },
  { label: '非常符合', desc: '完全符合我的情况', score: 100 }
])

const fetchAssessmentQuestions = async () => {
  try {
    loading.value = true
    const token = localStorage.getItem('token')
    const headers = {}
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    const response = await axios.get(`${API_BASE_URL}/questions`, { headers })
    if (response.data && response.data.length > 0) {
      testQuestions.value = response.data
      ElMessage.success(`成功加载 ${testQuestions.value.length} 道测评题目`)
    } else {
      ElMessage.error('未获取到测评题目，请检查后端数据库')
      testQuestions.value = []
    }
  } catch (error) {
    console.error('获取题目失败：', error)
    ElMessage.error('连接后端失败，无法加载题目')
    testQuestions.value = []
  } finally {
    loading.value = false
  }
}

const submitAssessmentResult = async () => {
  try {
    loading.value = true
    const answersArray = []
    
    for (const qid of Object.keys(answers.value)) {
      const score = answers.value[qid]
      const q = testQuestions.value.find(item => item.id == qid)
      if (q) {
        answersArray.push({
          question_id: q.id,
          score: score
        })
      }
    }
    
    const submitData = {
      answers: answersArray,
      user_id: userId.value || null,
      session_id: localStorage.getItem('session_id') || `guest_${Date.now()}`,
      test_mode: false
    }
    
    const token = localStorage.getItem('token')
    const headers = {}
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await axios.post(`${API_BASE_URL}/submit`, submitData, { headers })
    
    if (response.data.success) {
      const scores = response.data.dimension_scores
      Object.keys(scores).forEach(type => {
        dimensionScores.value[type] = Math.round(scores[type] * 20)
      })
      recommendation.value = response.data.recommendation
      ElMessage.success('测评提交成功，报告已保存至当前用户账号！')
      return response.data
    }
  } catch (error) {
    console.error('提交失败：', error)
    ElMessage.error('提交失败，使用本地计算')
    calculateLocalScores()
  } finally {
    loading.value = false
  }
}

const calculateLocalScores = () => {
  const total = { R:0, I:0, A:0, S:0, E:0, C:0 }
  const count = { R:0, I:0, A:0, S:0, E:0, C:0 }
  
  for (const qid of Object.keys(answers.value)) {
    const scoreVal = answers.value[qid]
    const q = testQuestions.value.find(item => item.id == qid)
    if (!q) continue
    const s = options.value[scoreVal - 1]?.score || 60
    total[q.dimension] += s
    count[q.dimension]++
  }
  
  Object.keys(total).forEach(k => {
    dimensionScores.value[k] = count[k] ? Math.round(total[k]/count[k]) : 60
  })
}

const currentQuestion = computed(() => testQuestions.value[currentQuestionIndex.value] || {})

const radarAxes = computed(() => [
  { label: '现实型(R)', score: dimensionScores.value.R },
  { label: '研究型(I)', score: dimensionScores.value.I },
  { label: '艺术型(A)', score: dimensionScores.value.A },
  { label: '社会型(S)', score: dimensionScores.value.S },
  { label: '企业型(E)', score: dimensionScores.value.E },
  { label: '常规型(C)', score: dimensionScores.value.C }
])

const topType = computed(() => {
  let max = 0, code = 'R'
  Object.entries(dimensionScores.value).forEach(([c, s]) => {
    if (s > max) { max = s; code = c }
  })
  return interestTypes.value.find(t => t.code === code) || interestTypes.value[0]
})

const formatRecommendation = (c) => c || ''
  .replace(/#{2,3} (.*)/g, '<h3>$1</h3>')
  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  .replace(/\n/g, '<br>')

const loadTestDraft = () => {
  const d = localStorage.getItem(DRAFT_STORAGE_KEY)
  if (!d) return
  try {
    const data = JSON.parse(d)
    currentQuestionIndex.value = data.currentIndex || 0
    answers.value = data.answers || {}
    testStarted.value = data.testStarted || false
    testCompleted.value = data.testCompleted || false
  } catch (e) {}
}

const saveTestDraft = () => {
  localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({
    currentIndex: currentQuestionIndex.value,
    answers: answers.value,
    testStarted: testStarted.value,
    testCompleted: testCompleted.value
  }))
}

const saveTestResult = () => {
  localStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify({
    dimensionScores: dimensionScores.value,
    recommendation: recommendation.value,
    topType: topType.value,
    testResultDate: testResultDate.value
  }))
}

const startTest = () => {
  testStarted.value = true
  testCompleted.value = false
  currentQuestionIndex.value = 0
  currentAnswer.value = 0
  answers.value = {}
  startTimer()
  saveTestDraft()
}

const startTimer = () => {
  clearInterval(timer)
  remainingTime.value = totalTime
  timer = setInterval(() => {
    if (--remainingTime.value <= 0) completeTest()
  }, 1000)
}

const selectAnswerAndNext = (v) => {
  const q = currentQuestion.value
  answers.value[q.id] = v
  currentAnswer.value = v
  saveTestDraft()
  setTimeout(() => {
    if (currentQuestionIndex.value < testQuestions.value.length - 1) {
      currentQuestionIndex.value++
      const nextQ = currentQuestion.value
      currentAnswer.value = answers.value[nextQ.id] || 0
    } else completeTest()
  }, 300)
}

const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    const q = currentQuestion.value
    currentAnswer.value = answers.value[q.id] || 0
  }
}

const nextQuestion = () => {
  const q = currentQuestion.value
  answers.value[q.id] = currentAnswer.value
  if (currentQuestionIndex.value < testQuestions.value.length - 1) {
    currentQuestionIndex.value++
    const nextQ = currentQuestion.value
    currentAnswer.value = answers.value[nextQ.id] || 0
  } else completeTest()
}

const completeTest = async () => {
  clearInterval(timer)
  testResultDate.value = new Date().toLocaleString()
  
  testQuestions.value.forEach(q => {
    if (!answers.value[q.id]) {
      answers.value[q.id] = 3
    }
  })
  
  await submitAssessmentResult()
  
  testCompleted.value = true
  testStarted.value = false
  saveTestDraft()
  saveTestResult()
}

const restartTest = () => {
  clearInterval(timer)
  testCompleted.value = false
  testStarted.value = false
  currentQuestionIndex.value = 0
  currentAnswer.value = 0
  answers.value = {}
  dimensionScores.value = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 }
  recommendation.value = ''
  showReportModal.value = false
  
  localStorage.removeItem(DRAFT_STORAGE_KEY)
  localStorage.removeItem(RESULT_STORAGE_KEY)
  
  ElMessage.success('已重置测评，可重新开始')
}

const exportReport = () => showReportModal.value = true
const goToMatchResult = () => router.push('/jobmatch-analysis')

const getRadarAxisStyle = (i) => ({
  transform: `rotate(${i*60-30}deg)`, transformOrigin: 'bottom'
})

const getRadarFillStyle = () => {
  const pts = radarAxes.value.map((a, i) => {
    const ang = (i*60-30) * Math.PI/180
    const r = a.score / 2
    return `${50 + r*Math.cos(ang)}% ${50 + r*Math.sin(ang)}%`
  })
  return { clipPath: `polygon(${pts.join(',')})` }
}

const getScoreLevel = s => s>=80?'极高':s>=60?'较高':s>=40?'中等':s>=20?'较低':'极低'

onMounted(async () => {
  await fetchAssessmentQuestions()
  loadTestDraft()
  applyTheme()
})

onUnmounted(() => {
  saveTestDraft()
  clearInterval(timer)
})
</script>

<style scoped>
.career-test {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  background: #f8f9fa;
  margin: 0;
  padding: 60px 0 0 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 500px;
}
.loading-spinner {
  font-size: 18px;
  color: #2f54eb;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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

.test-intro {
  padding: 40px 0;
}
.intro-wrap {
  width: 1200px;
  margin: 0 auto;
}
.intro-card {
  background: #fff;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.intro-header {
  text-align: center;
  margin-bottom: 30px;
}
.intro-header h2 {
  font-size: 28px;
  color: #2f54eb;
  margin: 0 0 10px 0;
}
.intro-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}
.intro-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}
.theory-desc h3, .test-rules h3 {
  font-size: 20px;
  color: #333;
  margin: 0 0 15px 0;
}
.theory-desc p, .test-rules p {
  font-size: 16px;
  line-height: 1.8;
  color: #666;
  margin: 0;
}
.test-rules ul {
  list-style: none;
  padding: 0;
  margin: 0;
  line-height: 2;
}
.test-rules li {
  position: relative;
  padding-left: 25px;
  margin-bottom: 8px;
}
.test-rules li::before {
  content: "✓";
  color: #2f54eb;
  position: absolute;
  left: 0;
}
.type-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 20px;
}
.type-card {
  display: flex;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  align-items: flex-start;
}
.type-icon {
  font-size: 30px;
}
.type-info h4 {
  font-size: 16px;
  margin: 0 0 8px 0;
  color: #2f54eb;
}
.type-info p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}
.intro-footer {
  text-align: center;
  margin-top: 40px;
}
.start-btn {
  padding: 12px 40px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.3s;
}
.start-btn:hover {
  background: #1d39c4;
}
.tips {
  font-size: 14px;
  color: #999;
  margin-top: 15px;
}

.test-questions {
  padding: 40px 0;
}
.questions-wrap {
  width: 1200px;
  margin: 0 auto;
}
.progress-bar {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 16px;
}
.progress-container {
  width: 100%;
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #2f54eb;
  border-radius: 4px;
  transition: width 0.3s;
}
.question-card {
  background: #fff;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.question-header h3 {
  font-size: 20px;
  color: #2f54eb;
  margin: 0 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid #e8e8e8;
}
.question-text {
  font-size: 18px;
  line-height: 1.8;
  margin: 0 0 30px 0;
}
.options-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 40px;
}
.option-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}
.option-item:hover {
  border-color: #2f54eb;
  background: #f0f2ff;
}
.option-item input {
  margin-right: 15px;
  width: 20px;
  height: 20px;
  accent-color: #2f54eb;
}
.option-text {
  font-size: 16px;
  color: #666;
}
.question-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}
.prev-btn, .next-btn {
  padding: 10px 30px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}
.prev-btn {
  border: 1px solid #e8e8e8;
  color: #666;
  background: #fff;
}
.next-btn {
  border: none;
  background: #2f54eb;
  color: #fff;
}
.prev-btn:disabled, .next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result {
  padding: 40px 0;
}
.result-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 40px;
}
.result-header {
  text-align: center;
}
.result-header h2 {
  font-size: 28px;
  color: #2f54eb;
  margin: 0 0 10px 0;
}
.result-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}
.result-chart {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  text-align: center;
}
.result-chart h3 {
  font-size: 20px;
  color: #333;
  margin: 0 0 30px 0;
}
.chart-container {
  width: 100%;
  max-width: 600px;
  height: 400px;
  margin: 0 auto;
  position: relative;
}
.radar-chart {
  width: 100%;
  height: 100%;
  position: relative;
}
.radar-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center, 
    rgba(47, 84, 235, 0.05) 0%, 
    rgba(47, 84, 235, 0.05) 20%, 
    rgba(47, 84, 235, 0.03) 20%,
    rgba(47, 84, 235, 0.03) 40%,
    rgba(47, 84, 235, 0.02) 40%,
    rgba(47, 84, 235, 0.02) 60%,
    rgba(47, 84, 235, 0.01) 60%,
    rgba(47, 84, 235, 0.01) 80%,
    transparent 80%);
  border-radius: 50%;
}
.radar-axis {
  position: absolute;
  bottom: 50%;
  left: 50%;
  width: 100px;
  height: 50%;
  transform-origin: bottom center;
}
.axis-label {
  position: absolute;
  top: -30px;
  left: 0;
  transform: translateX(-50%);
  font-size: 12px;
  white-space: nowrap;
  z-index: 10;
}
.axis-line {
  width: 2px;
  height: 100%;
  background: #e8e8e8;
  margin: 0 auto;
}
.axis-point {
  position: absolute;
  left: 50%;
  width: 8px;
  height: 8px;
  background: #2f54eb;
  border-radius: 50%;
  z-index: 20;
}
.radar-fill {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(47, 84, 235, 0.2);
  pointer-events: none;
  z-index: 5;
}
.core-result {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.core-card {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.core-icon {
  font-size: 60px;
}
.core-content h3 {
  font-size: 22px;
  color: #2f54eb;
  margin: 0 0 15px 0;
}
.core-desc {
  font-size: 16px;
  line-height: 1.8;
  color: #666;
  margin: 0 0 20px 0;
}
.core-tips h4 {
  font-size: 18px;
  color: #333;
  margin: 0 0 15px 0;
}
.career-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.career-tag {
  padding: 6px 15px;
  background: #f0f2ff;
  color: #2f54eb;
  border-radius: 20px;
  font-size: 14px;
}
.detail-analysis {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8 rgba(0,0,0,0.05);
}
.detail-analysis h3 {
  font-size: 20px;
  color: #333;
  margin: 0 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid #e8e8e8;
}
.analysis-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
.analysis-card {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #e8e8e8;
}
.analysis-card.top {
  border-left-color: #2f54eb;
  background: #f0f2ff;
}
.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.analysis-header .type-icon {
  font-size: 24px;
}
.analysis-header h4 {
  font-size: 16px;
  margin: 0;
  flex: 1;
  margin-left: 10px;
}
.score-tag {
  padding: 2px 8px;
  background: #2f54eb;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
}
.analysis-content p {
  font-size: 14px;
  line-height: 1.6;
  color: #666;
  margin: 0 0 15px 0;
}
.recommend-title {
  font-weight: bold;
  margin-bottom: 8px;
}
.recommend-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.recommend-list span {
  padding: 4px 10px;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}
.result-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}
.restart-btn, .export-btn, .career-plan-btn {
  padding: 10px 30px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}
.restart-btn {
  border: 1px solid #e8e8e8;
  color: #666;
  background: #fff;
}
.export-btn {
  border: none;
  background: #2f54eb;
  color: #fff;
}
.career-plan-btn {
  border: none;
  background: #1d39c4;
  color: #fff;
  font-weight: bold;
}
.career-plan-btn:hover {
  background: #0f2699;
}

.report-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
}
.modal-mask {
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
}
.modal-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  margin: 0;
  color: #2f54eb;
}
.close-btn {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}
.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}
.report-header {
  text-align: center;
  margin-bottom: 30px;
}
.report-date {
  font-size: 14px;
  color: #999;
  margin: 0 0 10px 0;
}
.report-header h2 {
  font-size: 24px;
  color: #2f54eb;
  margin: 0;
}
.report-section {
  margin-bottom: 30px;
}
.report-section h3 {
  font-size: 18px;
  color: #333;
  margin: 0 0 15px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}
.report-section p {
  font-size: 16px;
  line-height: 1.8;
  color: #666;
  margin: 0 0 15px 0;
}
.score-table {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
}
.table-row {
  display: flex;
  border-bottom: 1px solid #e8e8e8;
}
.table-row.header {
  background: #f8f9fa;
  font-weight: bold;
}
.table-cell {
  flex: 1;
  padding: 10px;
  text-align: center;
}
.career-group {
  margin-bottom: 15px;
}
.career-group h4 {
  font-size: 16px;
  margin: 0 0 10px 0;
}
.career-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.career-list span {
  padding: 4px 12px;
  background: #f0f2ff;
  color: #2f54eb;
  border-radius: 4px;
  font-size: 14px;
}
.suggestion-list {
  list-style: none;
  padding: 0;
  margin: 0;
  line-height: 2;
}
.suggestion-list li {
  position: relative;
  padding-left: 25px;
  margin-bottom: 8px;
}
.suggestion-list li::before {
  content: "•";
  color: #2f54eb;
  position: absolute;
  left: 0;
  font-size: 20px;
  line-height: 1;
}
.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

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

@media (max-width: 1200px) {
  .nav-wrap, .intro-wrap, .questions-wrap, .result-wrap, .footer-wrap {
    width: 90%;
  }
  .type-cards, .analysis-cards {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px) {
  .core-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .chart-container {
    height: 300px;
  }
  .question-card {
    padding: 20px;
  }
  .result-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>