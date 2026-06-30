<template>
  <section class="page-shell jobs-page">
    <div class="hero-card">
      <div class="hero-copy">
        <el-tag effect="plain">Job Galaxy</el-tag>
        <h1>岗位探索星图</h1>
        <p>从一枚关键词出发，穿过行业、城市、技能与薪酬的坐标，找到那些真正与你的能力、兴趣和下一段成长有关的岗位。</p>
      </div>
      <div class="orbital">
        <span v-for="n in 5" :key="n"></span>
      </div>
    </div>

    <div class="glass-panel filter-dock">
      <el-input v-model="query.keyword" placeholder="搜索岗位、公司、技能" clearable @keyup.enter="restart" />
      <el-select v-model="group" placeholder="岗位方向" clearable>
        <el-option v-for="item in categoryOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="query.company_size" placeholder="公司规模" clearable>
        <el-option v-for="item in sizes" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="query.order" placeholder="排序">
        <el-option label="默认探索" value="asc" />
        <el-option label="最新优先" value="desc" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="restart">开始探索</el-button>
    </div>

    <div class="result-meta">
      <span>已展示 {{ jobs.length }} / {{ total }} 个岗位</span>
      <span v-if="categoryLabel">当前方向：{{ categoryLabel }}</span>
    </div>

    <LoadingSkeleton v-if="loading && !jobs.length" />
    <transition-group v-else name="job" tag="div" class="job-stream">
      <JobCard v-for="(job, index) in jobs" :key="job.id" :job="job" :style="{ '--delay': `${Math.min(index, 12) * 40}ms` }" @open="openJob" />
    </transition-group>

    <div ref="sentinel" class="sentinel">
      <el-button v-if="hasMore" :loading="loadingMore" @click="loadMore">继续加载</el-button>
      <span v-else>这片方向暂时浏览完了，换个关键词，也许会遇见另一条路。</span>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { jobsApi } from '@/api'
import JobCard from '@/components/JobCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const loadingMore = ref(false)
const jobs = ref([])
const total = ref(0)
const sentinel = ref(null)
const group = ref(String(route.query.group || ''))
const sizes = ['20-99人', '100-499人', '500-999人', '1000-9999人', '10000人以上']
const categoryOptions = [
  { label: '技术研发', value: 'tech' },
  { label: '产品策划', value: 'product' },
  { label: '数据智能', value: 'data' },
  { label: '运营增长', value: 'operation' },
  { label: '市场商务', value: 'business' },
]
const query = reactive({
  page: Number(route.query.page || 1),
  size: 12,
  keyword: String(route.query.keyword || ''),
  industry: '',
  company_size: String(route.query.company_size || ''),
  order: String(route.query.order || 'asc'),
})
let observer

const hasMore = computed(() => jobs.value.length < total.value)
const categoryLabel = computed(() => categoryOptions.find((item) => item.value === group.value)?.label || '')

async function fetchPage({ append = false } = {}) {
  if (append) loadingMore.value = true
  else loading.value = true
  try {
    const params = { ...query, group: group.value }
    syncRoute(params)
    const data = await jobsApi.search(params)
    total.value = data.total || 0
    jobs.value = append ? [...jobs.value, ...(data.items || [])] : (data.items || [])
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function restart() {
  query.page = 1
  fetchPage()
}

function loadMore() {
  if (!hasMore.value || loadingMore.value || loading.value) return
  query.page += 1
  fetchPage({ append: true })
}

function syncRoute(params) {
  const nextQuery = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== '' && value !== null && value !== undefined && !(key === 'page' && value === 1)) {
      nextQuery[key] = String(value)
    }
  }
  const same = JSON.stringify(route.query) === JSON.stringify(nextQuery)
  if (!same) router.replace({ path: route.path, query: nextQuery })
}

function openJob(job) {
  router.push(`/jobs/${job.id}`)
}

watch(group, restart)

onMounted(() => {
  fetchPage()
  observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) loadMore()
  }, { rootMargin: '260px' })
  if (sentinel.value) observer.observe(sentinel.value)
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<style scoped>
.jobs-page {
  padding: 26px 0 112px;
}

.hero-card {
  min-height: 260px;
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  padding: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background:
    linear-gradient(135deg, rgba(127, 143, 163, 0.72), rgba(165, 181, 178, 0.62)),
    radial-gradient(circle at 78% 18%, rgba(212, 163, 115, 0.42), transparent 30%);
  box-shadow: 0 28px 68px rgba(79, 88, 102, 0.18);
}

.hero-copy {
  max-width: 620px;
  color: white;
  position: relative;
  z-index: 1;
}

.hero-copy h1 {
  margin: 16px 0;
  font-size: clamp(36px, 6vw, 66px);
  font-weight: 600;
  letter-spacing: 0;
}

.hero-copy p {
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.86);
}

.orbital {
  position: relative;
  width: 230px;
  height: 230px;
  flex: 0 0 230px;
}

.orbital span {
  position: absolute;
  width: 42px;
  height: 42px;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(12px);
  animation: floaty 4.6s ease-in-out infinite;
}

.orbital span:nth-child(1) { left: 40px; top: 20px; }
.orbital span:nth-child(2) { right: 28px; top: 52px; animation-delay: .4s; }
.orbital span:nth-child(3) { left: 88px; top: 112px; animation-delay: .8s; }
.orbital span:nth-child(4) { left: 22px; bottom: 24px; animation-delay: 1.2s; }
.orbital span:nth-child(5) { right: 40px; bottom: 22px; animation-delay: 1.6s; }

.filter-dock {
  position: sticky;
  top: 92px;
  z-index: 20;
  margin: -28px auto 20px;
  padding: 14px;
  display: grid;
  grid-template-columns: 1.3fr repeat(3, minmax(140px, 0.55fr)) auto;
  gap: 12px;
  box-shadow: 0 18px 42px rgba(79, 88, 102, 0.13);
}

.result-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin: 16px 4px;
  color: var(--muted);
}

.job-stream {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
}

.job-enter-active {
  transition: opacity .45s ease, transform .45s ease;
  transition-delay: var(--delay);
}

.job-enter-from {
  opacity: 0;
  transform: translateY(22px) scale(.98);
}

.sentinel {
  min-height: 86px;
  display: grid;
  place-items: center;
  color: var(--muted);
}

@keyframes floaty {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-18px) rotate(12deg); }
}

@media (max-width: 920px) {
  .filter-dock {
    position: static;
    grid-template-columns: 1fr 1fr;
  }

  .orbital {
    display: none;
  }
}

@media (max-width: 620px) {
  .filter-dock {
    grid-template-columns: 1fr;
  }

  .hero-card {
    padding: 26px;
  }
}
</style>
