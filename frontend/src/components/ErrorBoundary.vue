<template>
  <slot v-if="!error" />
  <GlassCard v-else>
    <div class="error-box">
      <CircleAlert :size="32" />
      <div>
        <h3>这个模块暂时没有加载完成</h3>
        <p>可以刷新页面，或回到上一页继续操作。你的登录状态和已填写内容会保留。</p>
      </div>
      <el-button type="primary" @click="reset">重新加载</el-button>
    </div>
  </GlassCard>
</template>

<script setup>
import { onErrorCaptured, ref } from 'vue'
import { CircleAlert } from 'lucide-vue-next'
import GlassCard from './GlassCard.vue'

const error = ref(null)

onErrorCaptured((err, instance, info) => {
  console.error('[Starway module error]', err, info, instance)
  error.value = err
  return false
})

function reset() {
  error.value = null
  location.reload()
}
</script>

<style scoped>
.error-box {
  display: flex;
  align-items: center;
  gap: 16px;
}

h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

p {
  margin: 0;
  color: var(--muted);
}
</style>
