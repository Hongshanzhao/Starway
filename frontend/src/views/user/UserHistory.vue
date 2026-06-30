<template>
  <section class="page">
    <GlassCard>
      <div class="head">
        <h1 class="section-title">浏览历史</h1>
        <el-button type="danger" plain @click="clear">清空</el-button>
      </div>
    </GlassCard>
    <GlassCard>
      <el-table :data="rows" stripe>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="desc" label="描述" />
        <el-table-column prop="browseTime" label="时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button text type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </GlassCard>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { userApi } from '@/api'
import GlassCard from '@/components/GlassCard.vue'

const rows = ref([])

async function load() {
  rows.value = await userApi.history()
}

async function remove(id) {
  await userApi.deleteHistory(id)
  load()
}

async function clear() {
  await userApi.clearHistory()
  load()
}

onMounted(load)
</script>

<style scoped>
.page {
  display: grid;
  gap: 18px;
}

.head {
  display: flex;
  justify-content: space-between;
}
</style>
