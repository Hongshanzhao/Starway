<template>
  <div class="ability-assessment">
    <!-- 1. 页面头部（保持项目统一风格） -->
    <header class="page-header">
      <div class="header-wrap">
        <div class="page-title">
          <span class="title-icon">📊</span>
          <h1>大学生核心能力测评中心</h1>
        </div>
        <div class="page-nav">
          <button class="back-btn" @click="$router.push('/')">← 返回首页</button>
          <button class="result-btn" @click="viewResult" :disabled="!hasFinished">查看测评报告</button>
        </div>
      </div>
    </header>

    <!-- 2. 测评引导区 -->
    <section class="guide-section">
      <div class="guide-wrap">
        <div class="guide-card">
          <div class="guide-icon">💡</div>
          <div class="guide-title">测评说明</div>
          <div class="guide-content">
            <ul>
              <li>本测评包含<strong>5个维度</strong>（学习能力、沟通能力、团队协作、专业技能、创新能力），共20道题目</li>
              <li>每道题目按「非常不符合(1分) - 非常符合(5分)」评分，如实作答即可</li>
              <li>测评完成后将生成专属能力分析报告，为职业规划提供数据支撑</li>
              <li>测评时长约5分钟，支持中途保存，退出后可继续作答</li>
            </ul>
          </div>
          <button class="start-btn" @click="startAssessment" v-show="!isAssessing && !hasFinished">开始测评</button>
        </div>
      </div>
    </section>

    <!-- 3. 测评答题区 -->
    <section class="assessment-section" v-show="isAssessing">
      <div class="assessment-wrap">
        <!-- 答题进度 -->
        <div class="progress-bar">
          <div class="progress-text">
            第 {{ currentQuestionIndex + 1 }} 题 / 共 {{ questionList.length }} 题
          </div>
          <div class="progress-bg">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
        </div>

        <!-- 题目内容 -->
        <div class="question-card">
          <div class="question-dimension">
            {{ currentQuestion.dimension }}
          </div>
          <div class="question-content">
            {{ currentQuestion.content }}
          </div>

          <!-- 评分选项 -->
          <div class="option-group">
            <label class="option-item" v-for="(option, index) in options" :key="index">
              <input 
                type="radio" 
                name="score" 
                :value="option.value" 
                v-model="currentAnswer"
                @change="selectAnswer"
              >
              <span class="option-text">{{ option.label }}</span>
            </label>
          </div>
        </div>

        <!-- 答题按钮 -->
        <div class="btn-group">
          <button class="prev-btn" @click="prevQuestion" :disabled="currentQuestionIndex === 0">上一题</button>
          <button class="save-btn" @click="saveAnswer">暂存答案</button>
          <button class="next-btn" @click="nextQuestion" :disabled="!currentAnswer">
            {{ currentQuestionIndex === questionList.length - 1 ? '完成测评' : '下一题' }}
          </button>
        </div>
      </div>
    </section>

    <!-- 4. 测评结果区 -->
    <section class="result-section" v-show="hasFinished">
      <div class="result-wrap">
        <div class="result-header">
          <h2>你的核心能力测评报告</h2>
          <div class="result-date">测评完成时间：{{ finishDate }}</div>
        </div>

        <!-- 能力雷达图 -->
        <div class="chart-container">
          <div class="chart-title">核心能力雷达图</div>
          <canvas id="abilityRadarChart" width="400" height="400"></canvas>
        </div>

        <!-- 能力分析 -->
        <div class="analysis-container">
          <div class="analysis-title">能力维度分析</div>
          <div class="analysis-list">
            <div class="analysis-item" v-for="(item, index) in abilityAnalysis" :key="index">
              <div class="analysis-dimension">{{ item.dimension }}</div>
              <div class="analysis-score">
                得分：{{ item.score }} / 20
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: (item.score / 20) * 100 + '%' }"></div>
                </div>
                <div class="score-level">{{ item.level }}</div>
              </div>
              <div class="analysis-suggestion">{{ item.suggestion }}</div>
            </div>
          </div>
        </div>

        <!-- 职业适配建议 -->
        <div class="suggestion-container">
          <div class="suggestion-title">职业适配建议</div>
          <div class="suggestion-content">
            {{ careerSuggestion }}
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="result-btn-group">
          <button class="export-btn" @click="exportReport">导出测评报告</button>
          <button class="restart-btn" @click="restartAssessment">重新测评</button>
        </div>
      </div>
    </section>

    <!-- 5. 页脚 -->
    <footer class="page-footer">
      <div class="footer-wrap">
        © 2026 大学生职业规划系统 | 科学测评 · 精准规划
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios' // 后续可对接后端，当前仅前端模拟

const router = useRouter()

// 核心状态管理
const isAssessing = ref(false) // 是否正在测评
const hasFinished = ref(false) // 是否完成测评
const currentQuestionIndex = ref(0) // 当前题目索引
const currentAnswer = ref('') // 当前题目的答案
const userAnswers = ref([]) // 用户所有答案
const finishDate = ref('') // 完成时间

// 测评题目库（5个维度，各4题）
const questionList = ref([
  // 学习能力维度
  {
    id: 1,
    dimension: '学习能力',
    content: '我能快速掌握新的知识和技能'
  },
  {
    id: 2,
    dimension: '学习能力',
    content: '我会制定详细的学习计划并严格执行'
  },
  {
    id: 3,
    dimension: '学习能力',
    content: '遇到学习难题时，我会主动寻找解决方法'
  },
  {
    id: 4,
    dimension: '学习能力',
    content: '我会定期复盘学习成果，调整学习方法'
  },
  // 沟通能力维度
  {
    id: 5,
    dimension: '沟通能力',
    content: '我能清晰表达自己的想法和观点'
  },
  {
    id: 6,
    dimension: '沟通能力',
    content: '我善于倾听他人的意见和建议'
  },
  {
    id: 7,
    dimension: '沟通能力',
    content: '遇到沟通矛盾时，我能理性解决'
  },
  {
    id: 8,
    dimension: '沟通能力',
    content: '我能根据不同的沟通对象调整表达方式'
  },
  // 团队协作维度
  {
    id: 9,
    dimension: '团队协作',
    content: '我乐于参与团队项目，配合队友完成任务'
  },
  {
    id: 10,
    dimension: '团队协作',
    content: '我能在团队中承担自己的责任，不推诿'
  },
  {
    id: 11,
    dimension: '团队协作',
    content: '我善于发现队友的优点，发挥团队优势'
  },
  {
    id: 12,
    dimension: '团队协作',
    content: '团队意见不一致时，我能积极协调沟通'
  },
  // 专业技能维度
  {
    id: 13,
    dimension: '专业技能',
    content: '我熟练掌握本专业的核心知识和技能'
  },
  {
    id: 14,
    dimension: '专业技能',
    content: '我会主动学习专业相关的前沿知识'
  },
  {
    id: 15,
    dimension: '专业技能',
    content: '我能将专业知识应用到实际问题解决中'
  },
  {
    id: 16,
    dimension: '专业技能',
    content: '我会通过实践/项目提升专业技能'
  },
  // 创新能力维度
  {
    id: 17,
    dimension: '创新能力',
    content: '我经常会有新的想法和解决方案'
  },
  {
    id: 18,
    dimension: '创新能力',
    content: '我敢于尝试新的方法和思路解决问题'
  },
  {
    id: 19,
    dimension: '创新能力',
    content: '我喜欢挑战传统模式，寻找优化空间'
  },
  {
    id: 20,
    dimension: '创新能力',
    content: '我能将不同领域的知识结合，产生新创意'
  }
])

// 评分选项
const options = ref([
  { label: '非常不符合', value: '1' },
  { label: '不太符合', value: '2' },
  { label: '一般', value: '3' },
  { label: '比较符合', value: '4' },
  { label: '非常符合', value: '5' }
])

// 当前题目
const currentQuestion = computed(() => {
  return questionList.value[currentQuestionIndex.value]
})

// 答题进度百分比
const progressPercent = computed(() => {
  return ((currentQuestionIndex.value + 1) / questionList.value.length) * 100
})

// 能力分析结果
const abilityAnalysis = ref([])

// 职业适配建议
const careerSuggestion = ref('')

// 后端返回的报告ID
const reportId = ref(null)

// 初始化：读取本地保存的测评数据
onMounted(() => {
  // 尝试读取本地存储的测评数据
  const savedAnswers = localStorage.getItem('abilityAssessmentAnswers')
  const savedFinishStatus = localStorage.getItem('abilityAssessmentFinished')
  
  if (savedAnswers) {
    userAnswers.value = JSON.parse(savedAnswers)
    // 恢复答题进度
    currentQuestionIndex.value = userAnswers.value.length
    // 如果有答案但未完成，显示继续答题按钮
    if (currentQuestionIndex.value > 0 && currentQuestionIndex.value < questionList.value.length) {
      isAssessing.value = true
    }
  }
  
  // 如果已完成测评，直接显示结果
  if (savedFinishStatus === 'true') {
    hasFinished.value = true
    finishDate.value = localStorage.getItem('abilityAssessmentFinishDate') || new Date().toLocaleString()
    calculateResult() // 重新计算结果
    initRadarChart() // 初始化雷达图
  }
})

// 销毁时保存答题状态
onUnmounted(() => {
  if (userAnswers.value.length > 0) {
    localStorage.setItem('abilityAssessmentAnswers', JSON.stringify(userAnswers.value))
  }
})

// 开始测评
const startAssessment = () => {
  isAssessing.value = true
  currentAnswer.value = ''
}

// 选择答案
const selectAnswer = () => {
  // 自动保存当前答案（可选，提升用户体验）
  saveAnswer()
}

// 保存当前答案
const saveAnswer = () => {
  if (!currentAnswer.value) {
    alert('请选择评分后再保存！')
    return
  }
  
  // 更新/添加当前题目的答案
  const existingIndex = userAnswers.value.findIndex(item => item.id === currentQuestion.value.id)
  if (existingIndex > -1) {
    userAnswers.value[existingIndex].score = currentAnswer.value
  } else {
    userAnswers.value.push({
      id: currentQuestion.value.id,
      dimension: currentQuestion.value.dimension,
      score: currentAnswer.value
    })
  }
  
  // 保存到本地存储
  localStorage.setItem('abilityAssessmentAnswers', JSON.stringify(userAnswers.value))
  alert('答案已保存！')
}

// 上一题
const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    // 恢复上一题的答案
    const prevAns = userAnswers.value.find(item => item.id === currentQuestion.value.id)
    currentAnswer.value = prevAns ? prevAns.score : ''
  }
}

// 下一题/完成测评
const nextQuestion = () => {
  if (!currentAnswer.value) {
    alert('请选择评分后再继续！')
    return
  }
  
  // 先保存当前答案
  saveAnswer()
  
  // 如果是最后一题，完成测评
  if (currentQuestionIndex.value === questionList.value.length - 1) {
    finishAssessment()
    return
  }
  
  // 下一题
  currentQuestionIndex.value++
  // 恢复下一题的答案（如果有）
  const nextAns = userAnswers.value.find(item => item.id === currentQuestion.value.id)
  currentAnswer.value = nextAns ? nextAns.score : ''
}

// 完成测评
const finishAssessment = async () => {
  isAssessing.value = false
  hasFinished.value = true
  
  // 记录完成时间
  finishDate.value = new Date().toLocaleString()
  
  // 保存完成状态
  localStorage.setItem('abilityAssessmentFinished', 'true')

  // 调用后端提交测评数据并获取报告ID
  try {
    const userId = localStorage.getItem('userId') || null
    const res = await axios.post('/api/assessment/submit', {
      user_id: userId,
      answers: userAnswers.value
    })
    if (res.data && res.data.report_id) {
      reportId.value = res.data.report_id
    }
  } catch (err) {
    console.error('提交测评失败', err)
  }
  
  // 计算测评结果
  calculateResult()
  
  // 初始化雷达图
  initRadarChart()
  
  alert('测评完成！已为你生成专属能力分析报告。')
}

// 计算测评结果
const calculateResult = () => {
  // 按维度汇总得分
  const dimensionScores = {
    '学习能力': 0,
    '沟通能力': 0,
    '团队协作': 0,
    '专业技能': 0,
    '创新能力': 0
  }
  
  // 统计每个维度的总分（每题5分，4题满分20）
  userAnswers.value.forEach(answer => {
    dimensionScores[answer.dimension] += Number(answer.score)
  })
  
  // 生成能力分析
  abilityAnalysis.value = Object.entries(dimensionScores).map(([dimension, score]) => {
    // 评定能力等级
    let level = ''
    let suggestion = ''
    
    if (score >= 16) {
      level = '优秀'
      suggestion = `你的${dimension}非常突出，可重点发挥该优势，在职业选择中优先考虑需要该能力的方向。`
    } else if (score >= 12) {
      level = '良好'
      suggestion = `你的${dimension}较好，可继续强化，在实践中进一步提升该能力。`
    } else if (score >= 8) {
      level = '一般'
      suggestion = `你的${dimension}处于中等水平，建议通过刻意练习（如参加培训/项目）提升。`
    } else {
      level = '待提升'
      suggestion = `你的${dimension}有待加强，可制定专项提升计划，从基础开始逐步改善。`
    }
    
    return {
      dimension,
      score,
      level,
      suggestion
    }
  })
  
  // 生成职业适配建议
  generateCareerSuggestion(dimensionScores)
}

// 生成职业适配建议
const generateCareerSuggestion = (scores) => {
  // 找出最高分和最低分的维度
  const sortedDimensions = Object.entries(scores).sort((a, b) => b[1] - a[1])
  const topDimension = sortedDimensions[0][0]
  const lowDimension = sortedDimensions[sortedDimensions.length - 1][0]
  
  // 基础建议模板
  const baseSuggestions = {
    '学习能力': '优先选择需要持续学习的职业方向（如研发、咨询、教育等），你的快速学习能力能帮助你快速适应行业变化。',
    '沟通能力': '优先选择需要高频沟通的职业方向（如销售、运营、人力资源、管理等），你的沟通优势能让你在工作中事半功倍。',
    '团队协作': '优先选择团队型工作模式的职业（如项目管理、产品、金融投行等），你能很好地融入团队并发挥协作价值。',
    '专业技能': '优先选择专业型职业方向（如技术研发、医生、律师、会计等），你的专业能力是核心竞争力。',
    '创新能力': '优先选择需要创意的职业方向（如设计、策划、创业、科研等），你的创新思维能带来独特价值。'
  }
  
  // 组合最终建议
  careerSuggestion.value = `
    基于你的测评结果，你的${topDimension}表现最佳，${lowDimension}需要重点提升。
    ${baseSuggestions[topDimension]}
    同时建议你针对性提升${lowDimension}，弥补能力短板，让职业发展更均衡。
    具体职业选择可结合你的专业背景和兴趣方向，优先选择能发挥${topDimension}优势的领域。
  `.replace(/\n/g, '').trim()
}

// 初始化雷达图（使用原生Canvas实现，无需额外依赖）
const initRadarChart = () => {
  const canvas = document.getElementById('abilityRadarChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const radius = 150 // 雷达图半径
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 1. 绘制雷达图背景
  const dimensions = ['学习能力', '沟通能力', '团队协作', '专业技能', '创新能力']
  const angleStep = (2 * Math.PI) / dimensions.length // 每个维度的角度间隔
  
  // 绘制网格线（5层）
  for (let i = 0; i < 5; i++) {
    const currentRadius = (radius / 4) * i
    ctx.beginPath()
    for (let j = 0; j < dimensions.length; j++) {
      const angle = j * angleStep - Math.PI / 2 // 从顶部开始
      const x = centerX + currentRadius * Math.cos(angle)
      const y = centerY + currentRadius * Math.sin(angle)
      j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    }
    ctx.closePath()
    ctx.strokeStyle = '#e8e8e8'
    ctx.stroke()
    ctx.fillStyle = i % 2 === 0 ? '#f8f9fa' : '#fff'
    ctx.fill()
  }
  
  // 2. 绘制维度轴线和标签
  dimensions.forEach((dimension, index) => {
    const angle = index * angleStep - Math.PI / 2
    // 绘制轴线
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.lineTo(
      centerX + radius * Math.cos(angle),
      centerY + radius * Math.sin(angle)
    )
    ctx.strokeStyle = '#2f54eb'
    ctx.stroke()
    
    // 绘制维度标签
    const labelX = centerX + (radius + 20) * Math.cos(angle)
    const labelY = centerY + (radius + 20) * Math.sin(angle)
    ctx.font = '14px Microsoft Yahei'
    ctx.fillStyle = '#333'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(dimension, labelX, labelY)
  })
  
  // 3. 绘制用户得分区域
  ctx.beginPath()
  abilityAnalysis.value.forEach((item, index) => {
    const angle = index * angleStep - Math.PI / 2
    // 得分转换为半径比例（满分20分对应最大半径）
    const scoreRadius = (item.score / 20) * radius
    const x = centerX + scoreRadius * Math.cos(angle)
    const y = centerY + scoreRadius * Math.sin(angle)
    index === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.closePath()
  ctx.fillStyle = 'rgba(47, 84, 235, 0.3)'
  ctx.fill()
  ctx.strokeStyle = '#2f54eb'
  ctx.stroke()
  
  // 4. 绘制中心点
  ctx.beginPath()
  ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI)
  ctx.fillStyle = '#2f54eb'
  ctx.fill()
}

// 查看测评报告（跳转到结果页）
const viewResult = () => {
  if (!hasFinished.value) {
    alert('请先完成测评后再查看报告！')
    return
  }
  // 滚动到结果区域
  document.querySelector('.result-section').scrollIntoView({ behavior: 'smooth' })
}

// 导出测评报告
const exportReport = () => {
  if (reportId.value) {
    // 调用后端下载
    window.open(`/api/assessment/export/${reportId.value}?format=html`, '_blank')
    return
  }
  // 如果没有reportId则保持原模拟逻辑
  alert('测评报告已导出为PDF格式！\n（实际项目中可集成jsPDF/后端导出实现真实导出功能）')
  
  // 示例：生成简单的文本报告
  const reportContent = `
    大学生核心能力测评报告
    测评完成时间：${finishDate.value}
    ======================================
    一、核心能力得分：
    ${abilityAnalysis.value.map(item => `${item.dimension}：${item.score}/20（${item.level}）`).join('\n    ')}
    
    二、能力维度分析：
    ${abilityAnalysis.value.map(item => `${item.dimension}：${item.suggestion}`).join('\n    ')}
    
    三、职业适配建议：
    ${careerSuggestion.value}
  `.trim()
  
  // 下载文本文件（简单版导出）
  const blob = new Blob([reportContent], { type: 'text/plain' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `能力测评报告_${new Date().getTime()}.txt`
  a.click()
  URL.revokeObjectURL(a.href)
}

// 重新测评
const restartAssessment = () => {
  // 清空本地存储
  localStorage.removeItem('abilityAssessmentAnswers')
  localStorage.removeItem('abilityAssessmentFinished')
  localStorage.removeItem('abilityAssessmentFinishDate')
  
  // 重置状态
  userAnswers.value = []
  currentQuestionIndex.value = 0
  currentAnswer.value = ''
  hasFinished.value = false
  isAssessing.value = true
  
  alert('已重置测评状态，可重新开始答题！')
}
</script>

<style scoped>
/* 全局容器 */
.ability-assessment {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  background: #f8f9fa;
  margin: 0;
  padding: 0;
}

/* 1. 页面头部 */
.page-header {
  height: 70px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  width: 100%;
}
.header-wrap {
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
.back-btn {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.result-btn {
  padding: 6px 15px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
}
.result-btn:disabled {
  background: #e8e8e8;
  color: #999;
  cursor: not-allowed;
}

/* 2. 测评引导区 */
.guide-section {
  padding: 40px 0;
}
.guide-wrap {
  width: 1200px;
  margin: 0 auto;
}
.guide-card {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  text-align: center;
}
.guide-icon {
  font-size: 36px;
  margin-bottom: 15px;
}
.guide-title {
  font-size: 20px;
  font-weight: bold;
  color: #2f54eb;
  margin-bottom: 20px;
}
.guide-content {
  text-align: left;
  max-width: 800px;
  margin: 0 auto 30px;
  line-height: 1.6;
}
.guide-content ul {
  padding-left: 20px;
  margin: 0;
}
.guide-content li {
  margin-bottom: 10px;
}
.start-btn {
  padding: 10px 30px;
  border: none;
  background: #2f54eb;
  color: #fff;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}
.start-btn:hover {
  background: #1d39c4;
}

/* 3. 测评答题区 */
.assessment-section {
  padding: 20px 0 40px;
}
.assessment-wrap {
  width: 1200px;
  margin: 0 auto;
}
.progress-bar {
  margin-bottom: 30px;
}
.progress-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}
.progress-bg {
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #2f54eb;
  transition: width 0.3s ease;
}
.question-card {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-bottom: 30px;
}
.question-dimension {
  font-size: 14px;
  color: #2f54eb;
  margin-bottom: 15px;
  font-weight: bold;
}
.question-content {
  font-size: 18px;
  margin-bottom: 30px;
  line-height: 1.6;
}
.option-group {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}
.option-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 10px 20px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  flex: 1;
  min-width: 120px;
  justify-content: center;
}
.option-item input {
  margin-right: 8px;
}
.option-item:has(input:checked) {
  border-color: #2f54eb;
  background: rgba(47, 84, 235, 0.1);
}
.btn-group {
  display: flex;
  justify-content: center;
  gap: 20px;
}
.prev-btn, .save-btn {
  padding: 8px 20px;
  border: 1px solid #e8e8e8;
  color: #666;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.next-btn {
  padding: 8px 20px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
}
.prev-btn:disabled, .next-btn:disabled {
  background: #e8e8e8;
  color: #999;
  cursor: not-allowed;
  border-color: #e8e8e8;
}

/* 4. 测评结果区 */
.result-section {
  padding: 20px 0 40px;
}
.result-wrap {
  width: 1200px;
  margin: 0 auto;
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.result-header {
  text-align: center;
  margin-bottom: 40px;
  border-bottom: 1px solid #e8e8e8;
  padding-bottom: 20px;
}
.result-header h2 {
  color: #2f54eb;
  margin: 0 0 10px 0;
}
.result-date {
  font-size: 14px;
  color: #999;
}
.chart-container {
  text-align: center;
  margin-bottom: 40px;
}
.chart-title {
  font-size: 18px;
  font-weight: bold;
  color: #2f54eb;
  margin-bottom: 20px;
}
.analysis-container {
  margin-bottom: 40px;
}
.analysis-title {
  font-size: 18px;
  font-weight: bold;
  color: #2f54eb;
  margin-bottom: 20px;
  border-left: 4px solid #2f54eb;
  padding-left: 10px;
}
.analysis-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.analysis-item {
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}
.analysis-dimension {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}
.analysis-score {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}
.score-bar {
  flex: 1;
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
}
.score-fill {
  height: 100%;
  background: #2f54eb;
  transition: width 0.5s ease;
}
.score-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.score-level:contains('优秀') {
  background: #f6ffed;
  color: #52c41a;
}
.score-level:contains('良好') {
  background: #e6f7ff;
  color: #1890ff;
}
.score-level:contains('一般') {
  background: #fffbe6;
  color: #faad14;
}
.score-level:contains('待提升') {
  background: #fff2e8;
  color: #ff7a45;
}
.analysis-suggestion {
  font-size: 14px;
  line-height: 1.6;
  color: #666;
}
.suggestion-container {
  margin-bottom: 40px;
}
.suggestion-title {
  font-size: 18px;
  font-weight: bold;
  color: #2f54eb;
  margin-bottom: 20px;
  border-left: 4px solid #2f54eb;
  padding-left: 10px;
}
.suggestion-content {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  line-height: 1.8;
  font-size: 14px;
}
.result-btn-group {
  display: flex;
  justify-content: center;
  gap: 20px;
}
.export-btn {
  padding: 8px 20px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
}
.restart-btn {
  padding: 8px 20px;
  border: 1px solid #e8e8e8;
  color: #666;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}

/* 5. 页脚 */
.page-footer {
  background: #fff;
  padding: 20px 0;
  border-top: 1px solid #e8e8e8;
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 20px;
}
.footer-wrap {
  width: 1200px;
  margin: 0 auto;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .header-wrap, .guide-wrap, .assessment-wrap, .result-wrap, .footer-wrap {
    width: 90%;
  }
  .option-group {
    flex-direction: column;
  }
}
@media (max-width: 768px) {
  .analysis-score {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  .score-bar {
    width: 100%;
  }
}
</style>