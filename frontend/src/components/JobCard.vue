<template>
  <GlassCard interactive class="job-card" :class="{ selected }" @click="$emit('open', job)">
    <div class="glow"></div>
    <div class="top">
      <h3>{{ job.job_name || job.job_title || '未命名岗位' }}</h3>
      <span v-if="job.industry || job.job_category" class="category-pill">{{ job.industry || job.job_category }}</span>
    </div>
    <p class="company">{{ job.company || job.company_name || '未知公司' }}</p>
    <div class="meta">
      <span><MapPin :size="15" />{{ job.location || job.city || '-' }}</span>
      <span><BadgeDollarSign :size="15" />{{ job.salary_range || salaryText || '薪资面议' }}</span>
      <span v-if="job.company_size"><Building2 :size="15" />{{ job.company_size }}</span>
    </div>
    <div v-if="skillItems.length" class="skills">
      <span v-for="skill in skillItems" :key="skill">{{ skill }}</span>
    </div>
    <p v-if="job.why_similar" class="why">{{ job.why_similar }}</p>
    <div v-if="job.similarity || job.overall_score" class="score">
      <el-progress :percentage="Math.round((job.overall_score ?? job.similarity * 100) || 0)" :stroke-width="8" />
    </div>
    <div class="foot">
      <span v-if="job.company_type">{{ job.company_type }}</span>
      <span v-if="job.education">{{ job.education }}</span>
      <span v-if="job.experience">{{ job.experience }}</span>
      <span v-if="job.views">浏览 {{ job.views }}</span>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { BadgeDollarSign, Building2, MapPin } from 'lucide-vue-next'
import GlassCard from './GlassCard.vue'

const props = defineProps({
  job: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['open'])

const salaryText = computed(() => {
  if (props.job.salary_min || props.job.salary_max) return `${props.job.salary_min || ''}-${props.job.salary_max || ''}`
  return ''
})

const skillItems = computed(() => {
  const raw = Array.isArray(props.job.skills) ? props.job.skills : String(props.job.skills || '').split(/[,，、\s/|]+/)
  return raw.map((item) => String(item).trim()).filter(Boolean).slice(0, 4)
})
</script>

<style scoped>
.job-card {
  cursor: pointer;
  min-height: 232px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  overflow: hidden;
}

.job-card.selected {
  box-shadow: 0 24px 58px rgba(64, 158, 255, .18), inset 0 0 0 2px rgba(64, 158, 255, .42);
  background: rgba(255,255,255,.78);
}

.glow {
  position: absolute;
  right: -40px;
  top: -40px;
  width: 120px;
  height: 120px;
  border-radius: 44px;
  background: linear-gradient(135deg, rgba(201,177,176,.38), rgba(165,181,178,.28));
  transform: rotate(18deg);
  transition: transform .35s ease;
}

.job-card:hover .glow {
  transform: rotate(34deg) scale(1.1);
}

.top {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  justify-content: space-between;
}

.category-pill {
  flex: 0 0 auto;
  max-width: 72px;
  padding: 4px 9px;
  border-radius: 999px;
  color: #5d6874;
  font-size: 12px;
  background: rgba(255,255,255,.72);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.16);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

h3 {
  margin: 0;
  font-size: 19px;
  font-weight: 500;
  line-height: 1.35;
}

.company {
  position: relative;
  z-index: 1;
  margin: 0;
  color: var(--muted);
}

.meta {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  color: #59616b;
}

.meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.skills {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skills span {
  max-width: 120px;
  padding: 5px 9px;
  border-radius: 999px;
  color: #59616b;
  font-size: 12px;
  background: rgba(127,143,163,.12);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.why {
  position: relative;
  z-index: 1;
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.score {
  margin-top: auto;
}

.foot {
  position: relative;
  z-index: 1;
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid rgba(127,143,163,.14);
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  color: var(--muted);
  font-size: 12px;
}
</style>
