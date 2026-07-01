<template>
  <GlassCard class="auth-card">
    <h2>创建账号</h2>
    <p>创建你的 Starway 档案，从画像、测评和职业路径开始。</p>
    <el-form :model="form" label-position="top" @submit.prevent="submit">
      <el-form-item label="用户名">
        <el-input v-model="form.username" size="large" autocomplete="username" />
      </el-form-item>
      <el-form-item label="手机号">
        <el-input v-model="form.phone" size="large" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" size="large" type="password" show-password autocomplete="new-password" />
      </el-form-item>
      <el-form-item label="确认密码">
        <el-input v-model="confirm" size="large" type="password" show-password autocomplete="new-password" @keyup.enter="submit" />
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
      <el-button type="primary" size="large" class="full" :loading="loading" :disabled="captchaLoading" native-type="submit" @click="submit">注册</el-button>
    </el-form>
    <div class="switch">
      已有账号？
      <RouterLink to="/auth/login">去登录</RouterLink>
    </div>
  </GlassCard>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'

const router = useRouter()
const form = reactive({ username: '', phone: '', password: '', captcha: '', captcha_id: '' })
const confirm = ref('')
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
    phone: form.phone.trim(),
    password: form.password,
    captcha: form.captcha.trim(),
    captcha_id: form.captcha_id,
  }
  if (!payload.username || !payload.password || !payload.captcha) {
    ElMessage.warning('请填写用户名、密码和验证码')
    return
  }
  if (payload.password !== confirm.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await authApi.register(payload)
    ElMessage.success('注册成功，请登录')
    router.push('/auth/login')
  } catch (error) {
    const message = error?.response?.data?.error || error?.message || '注册失败，请检查填写内容'
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
  width: min(480px, 100%);
  position: relative;
  z-index: 3;
  color: #f8fff9;
  background: rgba(5,18,20,.94);
  border-color: rgba(255,255,255,.42);
  box-shadow: 0 38px 110px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.34);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

h2 {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 500;
}

p {
  margin: 0 0 22px;
  color: rgba(239,250,244,.86);
}

.auth-card :deep(.el-form-item__label) {
  color: rgba(239,250,244,.92);
  font-weight: 600;
}

.auth-card :deep(.el-input__wrapper) {
  background: rgba(255,255,255,.22);
  box-shadow: 0 0 0 1px rgba(255,255,255,.34) inset;
}

.auth-card :deep(.el-input__inner) {
  color: #f8fff9;
}

.auth-card :deep(.el-input__inner::placeholder) {
  color: rgba(239,250,244,.48);
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
  background: rgba(255,255,255,.26);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.34);
  color: rgba(239,250,244,.74);
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
  color: rgba(239,250,244,.76);
  font-size: 13px;
}

.full {
  width: 100%;
}

.switch {
  margin-top: 18px;
  text-align: center;
  color: rgba(239,250,244,.78);
}

.switch a {
  color: #dceadf;
  font-weight: 700;
}
</style>
