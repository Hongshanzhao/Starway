<template>
  <header class="nav-wrap">
    <nav class="page-shell nav glass-panel">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">S</span>
        <span>Starway</span>
      </RouterLink>
      <div class="links">
        <RouterLink v-for="item in links" :key="item.to" :to="item.to">{{ item.label }}</RouterLink>
      </div>
      <div class="actions">
        <template v-if="authState.user">
          <el-dropdown>
            <button class="avatar-btn" type="button">
              <UserRound :size="18" />
              <span>{{ authState.user.username }}</span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/user/profile')">个人中心</el-dropdown-item>
                <el-dropdown-item v-if="authState.user.role === 'admin'" @click="router.push('/admin/dashboard')">管理端</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button text @click="router.push('/auth/login')">登录</el-button>
          <el-button type="primary" @click="router.push('/auth/register')">注册</el-button>
        </template>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { UserRound } from 'lucide-vue-next'
import { authState, logout } from '@/utils/auth'

const router = useRouter()
const links = [
  { to: '/jobs/search', label: '岗位中心' },
  { to: '/assessment', label: '测评中心' },
  { to: '/match/recommend', label: '人岗匹配' },
  { to: '/assistant/chat', label: 'AI 助手' },
]

function handleLogout() {
  logout()
  router.push('/')
}
</script>

<style scoped>
.nav-wrap {
  position: sticky;
  top: 0;
  z-index: 30;
  padding: 14px 0;
  backdrop-filter: blur(10px);
}

.nav {
  min-height: 64px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 500;
}

.brand-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: white;
  background: linear-gradient(135deg, var(--mist-blue), var(--sage));
}

.links {
  display: flex;
  gap: 18px;
  color: var(--muted);
  font-size: 15px;
}

.links a.router-link-active,
.links a:hover {
  color: var(--ink);
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.avatar-btn {
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.55);
  border-radius: 12px;
  padding: 9px 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink);
  cursor: pointer;
}

@media (max-width: 820px) {
  .links {
    display: none;
  }

  .nav {
    min-height: 58px;
  }
}
</style>
