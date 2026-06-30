<template>
  <section class="page-shell quiz-page">
    <div class="quiz-stage">
      <div class="stage-bg">
        <span v-for="n in 9" :key="n"></span>
      </div>
      <div class="stage-head">
        <div>
          <el-tag effect="plain">Holland Interest</el-tag>
          <h1>兴趣测评 · 探索你的职业能量</h1>
          <p>跟着卡片节奏走，不用纠结完美答案，选择最接近当下真实感受的分值。</p>
        </div>
        <div class="progress-orb">
          <strong>{{ progress }}%</strong>
          <span>完成度</span>
        </div>
      </div>
      <el-progress :percentage="progress" :stroke-width="10" striped striped-flow />
    </div>

    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <transition name="question" mode="out-in">
        <div class="question-card" :key="activeQuestion?.id">
          <div class="question-index">{{ currentIndex + 1 }} / {{ questions.length }}</div>
          <h2>{{ activeQuestion.question }}</h2>
          <p>维度 {{ activeQuestion.dimension }} · 选择你的共鸣程度</p>
          <div class="choice-grid">
            <button
              v-for="option in options"
              :key="option.value"
              type="button"
              :class="{ active: answers[activeQuestion.id] === option.value }"
              @click="choose(option.value)"
            >
              <span>{{ option.icon }}</span>
              <strong>{{ option.label }}</strong>
              <small>{{ option.value }} 分</small>
            </button>
          </div>
        </div>
      </transition>

      <div class="quiz-actions glass-panel">
        <el-button :disabled="currentIndex === 0" @click="currentIndex -= 1">上一题</el-button>
        <el-button v-if="currentIndex < questions.length - 1" type="primary" :disabled="!answers[activeQuestion.id]" @click="currentIndex += 1">下一题</el-button>
        <el-button v-else type="primary" :loading="submitting" @click="submit">提交测评</el-button>
      </div>

      <div class="question-dots">
        <button
          v-for="(q, index) in questions"
          :key="q.id"
          type="button"
          :class="{ done: answers[q.id], active: index === currentIndex }"
          @click="currentIndex = index"
        ></button>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { assessmentApi } from '@/api'
import { authState } from '@/utils/auth'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const router = useRouter()
const loading = ref(true)
const submitting = ref(false)
const questions = ref([])
const answers = reactive({})
const currentIndex = ref(0)
const options = [
  { value: 1, label: '完全不像我', icon: '○' },
  { value: 2, label: '有一点点', icon: '◔' },
  { value: 3, label: '说不清', icon: '◐' },
  { value: 4, label: '挺像我的', icon: '◕' },
  { value: 5, label: '就是我', icon: '●' },
]

const activeQuestion = computed(() => questions.value[currentIndex.value] || {})
const progress = computed(() => {
  if (!questions.value.length) return 0
  const done = questions.value.filter((q) => answers[q.id]).length
  return Math.round((done / questions.value.length) * 100)
})

function choose(value) {
  answers[activeQuestion.value.id] = value
  if (currentIndex.value < questions.value.length - 1) {
    setTimeout(() => {
      if (answers[activeQuestion.value.id]) currentIndex.value += 1
    }, 220)
  }
}

async function submit() {
  const payload = questions.value.filter((q) => answers[q.id]).map((q) => ({ question_id: q.id, score: answers[q.id] }))
  if (payload.length < questions.value.length) {
    ElMessage.warning('还有题目没完成，点下面的小圆点可以快速跳转')
    return
  }
  submitting.value = true
  try {
    const data = await assessmentApi.submit({ user_id: authState.user?.id, session_id: 'web', answers: payload })
    sessionStorage.setItem(`assessment_result_${data.result_id}`, JSON.stringify(data))
    router.push(`/assessment/result/${data.result_id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    questions.value = await assessmentApi.questions()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.quiz-page {
  padding: 26px 0 60px;
  display: grid;
  gap: 20px;
}

.quiz-stage {
  position: relative;
  overflow: hidden;
  border-radius: 30px;
  padding: 34px;
  background: linear-gradient(135deg, rgba(127,143,163,.82), rgba(201,177,176,.72));
  color: white;
  box-shadow: 0 30px 74px rgba(79,88,102,.2);
}

.stage-bg span {
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 6px;
  background: rgba(255,255,255,.28);
  animation: drift 7s linear infinite;
}

.stage-bg span:nth-child(odd) { left: calc(var(--i, 1) * 11%); }
.stage-bg span:nth-child(1) { left: 12%; bottom: 8%; }
.stage-bg span:nth-child(2) { left: 24%; bottom: 18%; animation-delay: .5s; }
.stage-bg span:nth-child(3) { left: 38%; bottom: 10%; animation-delay: 1s; }
.stage-bg span:nth-child(4) { left: 52%; bottom: 22%; animation-delay: 1.5s; }
.stage-bg span:nth-child(5) { left: 66%; bottom: 9%; animation-delay: 2s; }
.stage-bg span:nth-child(6) { left: 78%; bottom: 17%; animation-delay: 2.5s; }
.stage-bg span:nth-child(7) { left: 88%; bottom: 12%; animation-delay: 3s; }

.stage-head {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: center;
}

h1 {
  margin: 16px 0;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.08;
  font-weight: 650;
}

.stage-head p {
  max-width: 620px;
  margin: 0;
  color: rgba(255,255,255,.86);
  line-height: 1.8;
}

.progress-orb {
  width: 128px;
  height: 128px;
  border-radius: 42px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.2);
  backdrop-filter: blur(16px);
}

.progress-orb strong {
  font-size: 34px;
}

.progress-orb span {
  margin-top: -34px;
  font-size: 13px;
}

.question-card {
  min-height: 420px;
  border-radius: 32px;
  padding: 34px;
  background: rgba(255,255,255,.66);
  box-shadow: 0 26px 70px rgba(79,88,102,.14);
  backdrop-filter: blur(18px);
}

.question-index {
  color: var(--amber);
  font-weight: 700;
}

.question-card h2 {
  max-width: 820px;
  margin: 18px 0 10px;
  font-size: clamp(28px, 4vw, 48px);
  line-height: 1.18;
  font-weight: 650;
}

.question-card p {
  color: var(--muted);
}

.choice-grid {
  margin-top: 30px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.choice-grid button {
  min-height: 150px;
  border: 1px solid rgba(127,143,163,.2);
  border-radius: 24px;
  display: grid;
  place-items: center;
  gap: 8px;
  background: rgba(255,255,255,.65);
  color: var(--ink);
  cursor: pointer;
  transition: transform .25s ease, background .25s ease, box-shadow .25s ease;
}

.choice-grid button:hover,
.choice-grid button.active {
  transform: translateY(-8px) rotate(-1deg);
  background: linear-gradient(180deg, rgba(255,255,255,.95), rgba(165,181,178,.24));
  box-shadow: 0 18px 42px rgba(79,88,102,.18);
}

.choice-grid span {
  font-size: 34px;
  color: var(--mist-blue);
}

.choice-grid strong {
  font-weight: 600;
}

.choice-grid small {
  color: var(--muted);
}

.quiz-actions {
  padding: 14px;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.question-dots {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.question-dots button {
  width: 12px;
  height: 12px;
  border: 0;
  border-radius: 99px;
  background: rgba(127,143,163,.24);
  cursor: pointer;
  transition: width .25s ease, background .25s ease;
}

.question-dots button.done {
  background: var(--sage);
}

.question-dots button.active {
  width: 34px;
  background: var(--amber);
}

.question-enter-active,
.question-leave-active {
  transition: opacity .3s ease, transform .3s ease;
}

.question-enter-from {
  opacity: 0;
  transform: translateX(36px) scale(.98);
}

.question-leave-to {
  opacity: 0;
  transform: translateX(-36px) scale(.98);
}

@keyframes drift {
  from { transform: translateY(0) rotate(0deg); opacity: .3; }
  to { transform: translateY(-360px) rotate(180deg); opacity: 0; }
}

@media (max-width: 900px) {
  .choice-grid {
    grid-template-columns: 1fr;
  }

  .stage-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
