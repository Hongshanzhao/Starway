<template>
  <div class="admin-shell">
    <aside class="admin-side">
      <div class="brand">
        <span>SW</span>
        <strong>Starway Admin</strong>
      </div>
      <nav>
        <RouterLink v-for="item in menu" :key="item.to" :to="item.to">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>
    <main class="admin-main">
      <header class="admin-top">
        <div>
          <strong>数据管理中心</strong>
          <span>用户、岗位、报告、图谱与 AI 任务监控</span>
        </div>
        <el-button class="logout-btn" plain @click="handleLogout">退出登录 / 切换账号</el-button>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { Bot, Boxes, ChartColumn, FileText, Gauge, Network, UsersRound } from 'lucide-vue-next'
import { logout } from '@/utils/auth'

const router = useRouter()

const menu = [
  { to: '/admin/dashboard', label: '数据总览', icon: Gauge },
  { to: '/admin/users', label: '用户管理', icon: UsersRound },
  { to: '/admin/jobs', label: '岗位管理', icon: Boxes },
  { to: '/admin/reports', label: '报告管理', icon: FileText },
  { to: '/admin/categories', label: '分类统计', icon: ChartColumn },
  { to: '/admin/graph', label: '图谱构建', icon: Network },
  { to: '/admin/ai-tools', label: 'AI 产出监控', icon: Bot },
]

function handleLogout() {
  logout()
  router.push('/auth/login')
}
</script>

<style scoped>
.admin-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  background:
    radial-gradient(circle at 52% 38%, rgba(255,255,255,.78), transparent 32%),
    linear-gradient(135deg, #eef2f7, #e7efe9 44%, #f2eeea);
}

.admin-side {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 24px 18px;
  border-right: 1px solid rgba(255,255,255,.72);
  background: rgba(255,255,255,.56);
  backdrop-filter: blur(28px);
  box-shadow: 16px 0 48px rgba(79,88,102,.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}

.brand span {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: white;
  background: linear-gradient(135deg, #7f8fa3, #a5b5b2);
  font-weight: 800;
}

.brand strong {
  font-size: 18px;
}

nav {
  display: grid;
  gap: 8px;
}

nav a {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  color: #687382;
}

nav a.router-link-active,
nav a:hover {
  color: #2f3640;
  background: rgba(127,143,163,.15);
}

.admin-main {
  min-width: 0;
  padding: 24px;
}

.admin-top {
  min-height: 72px;
  margin-bottom: 18px;
  padding: 16px 20px;
  border-radius: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,.66);
  box-shadow: 0 16px 46px rgba(79,88,102,.08);
  backdrop-filter: blur(22px);
}

.admin-top div {
  display: grid;
  gap: 4px;
}

.admin-top strong {
  font-size: 20px;
}

.admin-top span {
  color: var(--muted);
}

.logout-btn {
  border-radius: 14px;
}

@media (max-width: 860px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-side {
    position: static;
    height: auto;
  }

  .admin-top {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
