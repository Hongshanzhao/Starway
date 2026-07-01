<template>
  <section class="page-shell chat-page">
    <GlassCard class="assistant-head">
      <div class="head">
        <div>
          <h1 class="section-title">AI 助手</h1>
          <p class="muted">把目标岗位、简历片段或纠结点发来，系统会直接拆成方向、行动和可验证成果。</p>
        </div>
        <span class="live-chip">{{ statusText }}</span>
      </div>
    </GlassCard>
    <GlassCard>
      <div ref="messagesBox" class="messages">
        <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
          <pre>{{ msg.content }}</pre>
        </div>
        <div v-if="streaming" class="typing"><span></span><span></span><span></span></div>
      </div>
    </GlassCard>
    <GlassCard class="composer">
      <el-input v-model="input" type="textarea" :rows="3" placeholder="输入你的职业规划问题，Enter 发送，Shift+Enter 换行" @keydown.enter.exact.prevent="send" />
      <el-button type="primary" :loading="streaming" @click="send">发送</el-button>
    </GlassCard>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '@/api'
import { streamRequest } from '@/api/http'
import GlassCard from '@/components/GlassCard.vue'

const input = ref('')
const streaming = ref(false)
const messagesBox = ref(null)
const profileContext = ref(null)
const providerState = ref('AI API')
const usedFallback = ref(false)
let revealTimer = null
let pendingText = ''
const statusText = computed(() => {
  if (streaming.value) return '正在生成'
  return usedFallback.value ? '本地兜底' : providerState.value
})
const messages = ref([
  { role: 'assistant', content: '你好，我会把职业问题拆成方向、证据和行动。你可以把目标岗位、简历片段、纠结的选择都交给我。' },
])

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  const ai = { role: 'assistant', content: '' }
  messages.value.push(ai)
  streaming.value = true
  usedFallback.value = false
  try {
    await streamRequest('/api/assistant/chat', {
      message: text,
      provider: 'auto',
      stream: true,
      context: isGreeting(text) ? null : profileContext.value,
    }, (event) => {
      if (event.type === 'delta') queueReveal(ai, cleanText(event.content || event.chunk || ''))
      if (event.type === 'done') {
        providerState.value = event.provider || providerState.value
        usedFallback.value = Boolean(event.fallback)
      }
      nextTick(scrollBottom)
    })
  } catch (error) {
    ai.content = ai.content || '这次连接没有完成。你可以直接再发一次，或把目标岗位、已有技能和简历片段分开发给我。'
    ElMessage.error(error.message || 'AI 助手暂时没有响应')
  } finally {
    flushReveal(ai)
    streaming.value = false
  }
}

function queueReveal(message, text) {
  pendingText += text || ''
  if (revealTimer) return
  revealTimer = window.setInterval(() => {
    if (!pendingText) {
      clearInterval(revealTimer)
      revealTimer = null
      return
    }
    const step = pendingText.length > 120 ? 16 : 8
    message.content += pendingText.slice(0, step)
    pendingText = pendingText.slice(step)
    nextTick(scrollBottom)
  }, 14)
}

function flushReveal(message) {
  if (revealTimer) {
    clearInterval(revealTimer)
    revealTimer = null
  }
  if (pendingText) {
    message.content += cleanText(pendingText)
    pendingText = ''
  }
}

function cleanText(value) {
  return String(value || '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/您好/g, '你好')
    .replace(/您的/g, '你的')
    .replace(/您/g, '你')
}

function scrollBottom() {
  const el = messagesBox.value
  if (el) el.scrollTop = el.scrollHeight
}

onMounted(async () => {
  profileContext.value = await userApi.profile().catch(() => null)
})

function isGreeting(value) {
  const text = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[!！。。，,\s?？]/g, '')
  return ['你好', '您好', '嗨', '在吗', '在嘛', '哈喽', 'hello', 'hi'].includes(text)
}
</script>

<style scoped>
.chat-page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}

.assistant-head {
  overflow: hidden;
}

.assistant-head :deep(.muted),
.assistant-head .muted {
  color: #66716f;
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.live-chip {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  color: #486451;
  background: rgba(220, 234, 223, .72);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.62);
  white-space: nowrap;
}

.messages {
  min-height: 480px;
  max-height: 62vh;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 78%;
  padding: 14px 16px;
  border-radius: 16px;
  animation: popIn .28s ease both;
}

.message.user {
  align-self: flex-end;
  background: rgba(127, 143, 163, 0.16);
}

.message.assistant {
  align-self: flex-start;
  color: #3f474d;
  background: rgba(255, 255, 255, 0.66);
  box-shadow: 0 10px 28px rgba(79, 88, 102, 0.07);
}

pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.8;
  font-family: inherit;
  color: inherit;
}

.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 110px;
  gap: 14px;
}

.typing {
  width: 72px;
  padding: 12px 16px;
  border-radius: 18px;
  display: flex;
  gap: 5px;
  background: rgba(255,255,255,.62);
}

.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--mist-blue);
  animation: bounce .8s ease-in-out infinite;
}

.typing span:nth-child(2) { animation-delay: .12s; }
.typing span:nth-child(3) { animation-delay: .24s; }

@keyframes popIn {
  from { opacity: 0; transform: translateY(12px) scale(.98); }
}

@keyframes bounce {
  50% { transform: translateY(-5px); }
}

@media (max-width: 640px) {
  .composer {
    grid-template-columns: 1fr;
  }

  .message {
    max-width: 100%;
  }
}
</style>
