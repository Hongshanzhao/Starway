<template>
  <section class="page-shell page">
    <GlassCard>
      <h1 class="section-title">匹配历史</h1>
      <div class="toolbar">
        <el-input-number v-model="studentId" :min="1" :disabled="profileLoading" />
        <el-button type="primary" :loading="loading || profileLoading" @click="load">查询</el-button>
      </div>
    </GlassCard>
    <GlassCard>
      <el-table :data="rows" stripe>
        <el-table-column prop="job_name" label="岗位" />
        <el-table-column prop="match_score" label="匹配分" width="120" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </GlassCard>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { matchApi, userApi } from '@/api'
import { currentStudentId } from '@/utils/auth'
import GlassCard from '@/components/GlassCard.vue'

const router = useRouter()
const studentId = ref(null)
const profileLoading = ref(false)
const loading = ref(false)
const rows = ref([])

async function ensureStudentId() {
  if (studentId.value) return studentId.value
  profileLoading.value = true
  try {
    const profile = await userApi.profile()
    studentId.value = currentStudentId(profile)
  } finally {
    profileLoading.value = false
  }
  if (!studentId.value) {
    ElMessage.warning('还没有学生画像，请先完善画像')
    router.push('/profile/create')
    return null
  }
  return studentId.value
}

async function load() {
  const id = await ensureStudentId()
  if (!id) return
  loading.value = true
  try {
    const data = await matchApi.history(id)
    rows.value = data.history || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
  display: grid;
  gap: 18px;
}
</style>
