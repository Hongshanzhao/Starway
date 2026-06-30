<template>
  <GlassCard interactive class="report-card" @click="$emit('open', report)">
    <div>
      <el-tag effect="plain">{{ typeLabel }}</el-tag>
      <h3>{{ report.title || `${report.job_name || report.targetJob || '报告'} 详情` }}</h3>
      <p>{{ report.summary || report.result || report.suggestion || '暂无摘要' }}</p>
    </div>
    <div class="foot">
      <span>{{ report.createTime || report.created_at || report.created_at || '-' }}</span>
      <el-button text @click.stop="$emit('open', report)">查看</el-button>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from './GlassCard.vue'

const props = defineProps({
  report: { type: Object, required: true },
})
defineEmits(['open'])

const typeLabel = computed(() => {
  const type = props.report.type || props.report.format_type
  if (type === 'interest_test') return '兴趣测评'
  if (type === 'job_match') return '人岗匹配'
  if (type === 'career_plan') return '职业规划'
  return props.report.targetJob ? '匹配报告' : '报告'
})
</script>

<style scoped>
.report-card {
  min-height: 170px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
}

h3 {
  margin: 12px 0 8px;
  font-size: 18px;
  font-weight: 500;
}

p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18px;
  color: var(--muted);
  font-size: 13px;
}
</style>
