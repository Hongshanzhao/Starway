<template>
  <GlassCard class="auth-card">
    <h2>欢迎回来</h2>
    <p>登录后继续完善画像、生成报告和使用 AI 助手。</p>
    <el-form :model="form" label-position="top" @submit.prevent="submit">
      <el-form-item label="用户名或手机号">
        <el-input v-model="form.username" size="large" placeholder="student01" autocomplete="username" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" size="large" type="password" show-password autocomplete="current-password" @keyup.enter="submit" />
      </el-form-item>
      <el-form-item label="图形验证码">
        <div class="captcha-row">
          <el-input
            v-model.trim="form.captcha"
            size="large"
            maxlength="4"
            autocomplete="off"
            placeholder="输入图片字符"
            @keyup.enter="submit"
          />
          <button class="captcha-box" type="button" :disabled="captchaLoading" @click="refreshCaptcha">
            <img
              v-if="captchaUrl"
              :src="captchaUrl"
              alt="图形验证码"
              @load="captchaLoading = false"
              @error="captchaLoading = false"
            />
            <span v-if="captchaLoading">加载中</span>
          </button>
        </div>
        <div class="hint">不区分大小写，看不清可直接点击图片换一张。</div>
      </el-form-item>
      <el-button type="primary" size="large" class="full" :loading="loading" :disabled="captchaLoading" native-type="submit" @click="submit">登录</el-button>
    </el-form>
    <div class="switch">
      没有账号？
      <RouterLink to="/auth/register">去注册</RouterLink>
    </div>
  </GlassCard>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { loginWith } from '@/utils/auth'
import GlassCard from '@/components/GlassCard.vue'

const router = useRouter()
const route = useRoute()
const form = reactive({ username: '', password: '', captcha: '', captcha_id: '' })
const loading = ref(false)
const captchaLoading = ref(false)
const captchaUrl = ref('')

function createCaptchaId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function refreshCaptcha() {
  form.captcha = ''
  captchaLoading.value = true
  form.captcha_id = createCaptchaId()
  captchaUrl.value = authApi.captchaUrl(form.captcha_id)
}

function shouldRefreshCaptcha(message) {
  return /验证码|过期|刷新|captcha/i.test(message || '')
}

async function submit() {
  if (loading.value) return
  if (captchaLoading.value) {
    ElMessage.warning('验证码还在加载，请稍等一下')
    return
  }
  const payload = {
    username: form.username.trim(),
    password: form.password,
    captcha: form.captcha.trim(),
    captcha_id: form.captcha_id,
  }
  if (!payload.username || !payload.password || !payload.captcha) {
    ElMessage.warning('请填写用户名、密码和验证码')
    return
  }
  loading.value = true
  try {
    const data = await authApi.login(payload)
    loginWith(data.token, data.user)
    ElMessage.success('登录成功')
    router.push(route.query.redirect || '/')
  } catch (error) {
    const message = error?.response?.data?.error || error?.message || '登录失败，请检查账号、密码和验证码'
    ElMessage.error(message)
    if (shouldRefreshCaptcha(message)) refreshCaptcha()
  } finally {
    loading.value = false
  }
}

refreshCaptcha()
</script>

<style scoped>
.auth-card {
  width: min(440px, 100%);
  background: rgba(255,255,255,.68);
  box-shadow: 0 28px 70px rgba(79, 124, 99, .14);
}

h2 {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 500;
}

p {
  margin: 0 0 26px;
  color: var(--muted);
}

.captcha-row {
  display: grid;
  grid-template-columns: 1fr 126px;
  gap: 10px;
  width: 100%;
}

.captcha-box {
  position: relative;
  width: 126px;
  height: 40px;
  padding: 0;
  border: 0;
  border-radius: 12px;
  cursor: pointer;
  overflow: hidden;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.18);
  color: var(--muted);
}

.captcha-box:disabled {
  cursor: wait;
}

img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: rgba(255, 255, 255, .72);
}

.captcha-box span {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: 13px;
}

.hint {
  margin-top: 8px;
  color: var(--muted);
  font-size: 13px;
}

.full {
  width: 100%;
}

.switch {
  margin-top: 18px;
  text-align: center;
  color: var(--muted);
}

.switch a {
  color: var(--mist-blue);
}
</style>
