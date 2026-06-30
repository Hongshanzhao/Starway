<template>
  <div>
    <AppNavbar />
    <div class="user-page page-shell">
      <aside class="glass-panel side">
        <RouterLink v-for="item in menu" :key="item.to" :to="item.to">
          <component :is="item.icon" :size="18" />
          {{ item.label }}
        </RouterLink>
      </aside>
      <section class="content">
        <RouterView />
      </section>
    </div>
    <BackButton />
    <AppFooter />
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { Clock, FileText, HeartPulse, IdCard, Target } from 'lucide-vue-next'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'
import BackButton from '@/components/BackButton.vue'

const menu = [
  { to: '/user/profile', label: '个人资料', icon: IdCard },
  { to: '/user/plans', label: '规划报告', icon: FileText },
  { to: '/user/interests', label: '兴趣报告', icon: HeartPulse },
  { to: '/user/matches', label: '匹配报告', icon: Target },
  { to: '/user/history', label: '浏览历史', icon: Clock },
]
</script>

<style scoped>
.user-page {
  display: grid;
  grid-template-columns: 230px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
  padding: 22px 0 42px;
}

.side {
  position: sticky;
  top: 96px;
  padding: 12px;
  display: grid;
  gap: 6px;
}

.side a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  color: var(--muted);
}

.side a.router-link-active,
.side a:hover {
  color: var(--ink);
  background: rgba(127, 143, 163, 0.13);
}

.content {
  min-width: 0;
}

@media (max-width: 840px) {
  .user-page {
    grid-template-columns: 1fr;
  }

  .side {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
