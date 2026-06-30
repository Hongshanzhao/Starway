<template>
  <button class="back-btn" type="button" @click="goBack" aria-label="返回上一页">
    <ArrowLeft :size="18" />
    <span>返回</span>
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

const router = useRouter()

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}
</script>

<style scoped>
.back-btn {
  position: fixed;
  right: max(18px, calc((100vw - 1180px) / 2));
  bottom: 24px;
  z-index: 40;
  border: 1px solid rgba(127, 143, 163, 0.24);
  border-radius: 999px;
  padding: 11px 15px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 14px 34px rgba(79, 88, 102, 0.14);
  backdrop-filter: blur(16px);
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.back-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 42px rgba(79, 88, 102, 0.2);
}

@media (max-width: 640px) {
  .back-btn {
    right: 14px;
    bottom: 14px;
    padding: 11px;
  }

  .back-btn span {
    display: none;
  }
}
</style>
