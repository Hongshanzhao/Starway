<template>
  <div class="admin-login container">
    <h2>管理员登录</h2>
    <form @submit.prevent="submit">
      <div>
        <label>用户名</label>
        <input v-model="username" required />
      </div>
      <div>
        <label>密码</label>
        <input type="password" v-model="password" required />
      </div>
      <button type="submit">登录</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'AdminLogin',
  data() {
    return { username: '', password: '', error: null }
  },
  methods: {
    async submit() {
      this.error = null
      try {
        const res = await axios.post('/api/admin/login', { username: this.username, password: this.password })
        const token = res.data.token
        localStorage.setItem('admin_token', token)
        // 跳转到后台管理首页（暂用首页代替）
        this.$router.push({ name: 'Home' })
      } catch (e) {
        this.error = e.response?.data?.error || '登录失败'
      }
    }
  }
}
</script>

<style scoped>
.admin-login{max-width:420px;margin:40px auto;padding:24px;background:var(--card-bg, #fff);border-radius:8px}
.admin-login input{width:100%;padding:8px;margin:8px 0}
.error{color:#c00}
</style>
