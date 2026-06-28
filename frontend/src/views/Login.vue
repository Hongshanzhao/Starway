<template>
  <div class="login-page">
    <header class="login-header">
      <div class="logo">
        <span class="logo-icon">🎯</span>
        <span class="logo-text">大学生职业规划系统</span>
      </div>
    </header>

    <main class="login-main">
      <div class="login-card">
        <div class="login-title">用户登录</div>
        <form class="login-form" @submit.prevent="handleLogin">
          <!-- 账号 -->
          <div class="form-item">
            <label class="form-label">账号</label>
            <input 
              type="text" 
              class="form-input" 
              v-model="loginForm.username" 
              placeholder="请输入手机号/用户名"
              :class="{ error: formError.username }"
            >
            <span class="error-tip" v-if="formError.username">{{ formError.username }}</span>
          </div>

          <!-- 密码 -->
          <div class="form-item">
            <label class="form-label">密码</label>
            <input 
              type="password" 
              class="form-input" 
              v-model="loginForm.password" 
              placeholder="请输入密码"
              :class="{ error: formError.password }"
            >
            <span class="error-tip" v-if="formError.password">{{ formError.password }}</span>
          </div>

          <!-- 图形验证码 -->
          <div class="form-item">
            <label class="form-label">验证码</label>
            <div class="captcha-container">
              <input 
                type="text" 
                class="form-input captcha-input" 
                v-model="loginForm.captcha" 
                placeholder="请输入验证码"
                :class="{ error: formError.captcha }"
              >
              <img :src="captchaSrc" @click="refreshCaptcha" class="captcha-img" alt="验证码">
              <span class="refresh-link" @click="refreshCaptcha">换一张</span>
            </div>
            <span class="error-tip" v-if="formError.captcha">{{ formError.captcha }}</span>
          </div>

          <!-- 登录错误/成功提示 -->
          <div v-if="loginError" class="login-error">{{ loginError }}</div>
          <div v-if="loginSuccessMsg" class="login-success">{{ loginSuccessMsg }}</div>

          <!-- 记住密码 & 忘记密码 -->
          <div class="form-extra">
            <label class="checkbox-label">
              <input type="checkbox" v-model="loginForm.remember"> 记住密码
            </label>
            <a href="#" class="forgot-pwd">忘记密码？</a>
          </div>

          <!-- 登录按钮 -->
          <button type="submit" class="login-btn" :disabled="isLoading">
            <span v-if="!isLoading">登录</span>
            <span v-if="isLoading">登录中...</span>
          </button>

          <!-- 注册入口 -->
          <div class="register-link">
            还没有账号？<a href="/register" class="link-text">立即注册</a>
          </div>
        </form>
      </div>
    </main>

    <footer class="login-footer">
      © 2026 大学生职业规划系统 | 助力大学生精准规划职业方向
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 登录表单数据
const loginForm = ref({
  username: '',
  password: '',
  remember: false,
  captcha: ''
})

// 表单错误提示
const formError = ref({
  username: '',
  password: '',
  captcha: ''
})

// 全局提示信息
const loginError = ref('')
const loginSuccessMsg = ref('')
let successTimer = null

// 加载状态
const isLoading = ref(false)

// 图形验证码相关
const captchaTimestamp = ref(Date.now())
const captchaSrc = computed(() => `/api/captcha?t=${captchaTimestamp.value}`)

// 刷新验证码
const refreshCaptcha = () => {
  captchaTimestamp.value = Date.now()
  loginForm.value.captcha = ''
  formError.value.captcha = ''
}

// 表单验证
const validateForm = () => {
  let isValid = true
  formError.value = {}

  if (!loginForm.value.username.trim()) {
    formError.value.username = '请输入账号'
    isValid = false
  }
  if (!loginForm.value.password.trim()) {
    formError.value.password = '请输入密码'
    isValid = false
  } else if (loginForm.value.password.length < 6) {
    formError.value.password = '密码长度不能少于6位'
    isValid = false
  }
  if (!loginForm.value.captcha.trim()) {
    formError.value.captcha = '请输入验证码'
    isValid = false
  }

  return isValid
}

// 登录提交
const handleLogin = async () => {
  if (!validateForm()) return

  loginError.value = ''
  loginSuccessMsg.value = ''
  if (successTimer) clearTimeout(successTimer)

  try {
    isLoading.value = true
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: loginForm.value.username,
        password: loginForm.value.password,
        captcha: loginForm.value.captcha
      })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.error || '用户名或密码错误')
    }

    // 登录成功
    localStorage.setItem('token', data.token)
    localStorage.setItem('currentUser', JSON.stringify(data.user))
    localStorage.setItem('role', data.user.role) // 保存角色
    localStorage.setItem('user_id', data.user.id)

    // ====================== 关键修改：根据角色跳转 ======================
    if (data.user.role === 'admin') {
      loginSuccessMsg.value = '管理员登录成功！即将进入管理后台'
      setTimeout(() => router.push('/admin'), 1500)
    } else {
      loginSuccessMsg.value = '登录成功！即将跳转至首页'
      setTimeout(() => router.push('/'), 1500)
    }
    // ===================================================================

  } catch (error) {
    loginError.value = error.message
    refreshCaptcha() // 失败后刷新验证码
  } finally {
    isLoading.value = false
  }
}

// 组件卸载时清除定时器
onUnmounted(() => {
  if (successTimer) clearTimeout(successTimer)
})
</script>

<style scoped>
/* 原有样式保持不变，仅添加验证码相关样式 */
.login-page {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
}
.login-header {
  height: 80px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  padding: 0 40px;
}
.logo {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  color: #2f54eb;
}
.logo-icon {
  font-size: 28px;
  margin-right: 10px;
}
.login-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}
.login-card {
  width: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 30px;
}
.login-title {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 25px;
  color: #333;
}
.login-form {
  width: 100%;
}
.form-item {
  margin-bottom: 20px;
}
.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #333;
}
.form-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  outline: none;
}
.form-input.error {
  border-color: #ff4d4f;
}
.form-input:focus {
  border-color: #2f54eb;
}
.error-tip {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #ff4d4f;
}

/* 验证码容器 */
.captcha-container {
  display: flex;
  align-items: center;
  gap: 8px;
}
.captcha-input {
  flex: 1;
}
.captcha-img {
  width: 100px;
  height: 36px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: pointer;
}
.refresh-link {
  color: #2f54eb;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.refresh-link:hover {
  text-decoration: underline;
}

/* 登录错误/成功提示 */
.login-error {
  color: #ff4d4f;
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
  padding: 8px 0;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
}
.login-success {
  color: #52c41a;
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
  padding: 8px 0;
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
}

.form-extra {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 14px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #666;
}
.checkbox-label input {
  margin-right: 6px;
}
.forgot-pwd {
  color: #2f54eb;
  text-decoration: none;
}
.forgot-pwd:hover {
  text-decoration: underline;
}
.login-btn {
  width: 100%;
  height: 44px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s;
}
.login-btn:disabled {
  background: #85a5ff;
  cursor: not-allowed;
}
.login-btn:hover:not(:disabled) {
  background: #1d39c4;
}
.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}
.link-text {
  color: #2f54eb;
  text-decoration: none;
}
.link-text:hover {
  text-decoration: underline;
}
.login-footer {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 12px;
  color: #999;
  border-top: 1px solid #e8e8e8;
}
</style>