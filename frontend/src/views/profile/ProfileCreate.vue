<template>
  <section class="page-shell page">
    <GlassCard>
      <h1 class="section-title">学生画像</h1>
      <p class="muted">手动填写或上传简历，后端会抽取技能、证书与软能力画像。</p>
      <el-tabs v-model="mode">
        <el-tab-pane label="手动填写" name="manual">
          <el-form :model="form" label-position="top" class="form-grid">
            <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
            <el-form-item label="专业"><el-input v-model="form.major" /></el-form-item>
            <el-form-item label="年级"><el-input v-model="form.grade" /></el-form-item>
            <el-form-item label="教育经历"><el-input v-model="form.education" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="实习经历"><el-input v-model="form.work" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="项目经历"><el-input v-model="form.project" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="技能证书"><el-input v-model="form.skills_certs" placeholder="Python, SQL, CET-6" /></el-form-item>
            <el-form-item label="自我总结"><el-input v-model="form.summary" type="textarea" :rows="4" /></el-form-item>
          </el-form>
          <el-button type="primary" :loading="loading" @click="submit">生成画像</el-button>
        </el-tab-pane>
        <el-tab-pane label="上传简历" name="upload">
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
            :accept="acceptTypes"
          >
            <UploadCloud :size="38" />
            <div>拖拽或点击上传 PDF、Word、TXT、Markdown</div>
            <template #tip>
              <div class="upload-tip">建议优先上传 DOCX 或 TXT。复杂 PDF、扫描件和加密 PDF 可能无法抽取文本。</div>
            </template>
          </el-upload>
          <el-button type="primary" class="upload-btn" :loading="uploading" @click="upload">解析简历</el-button>
        </el-tab-pane>
      </el-tabs>
      <div v-if="errorMessage" class="inline-error">
        <CircleAlert :size="18" />
        <span>{{ errorMessage }}</span>
      </div>
      <div v-if="parsed.text || parsed.parse_warning" class="parsed glass-panel">
        <div class="parsed-head">
          <div>
            <h3>{{ parsed.text ? '解析结果' : '需要换一种方式解析' }}</h3>
            <p>{{ parsed.text ? '已抽取技能、经历和软能力，并回填到表单。确认无误后可保存为新的学生画像。' : parsed.parse_warning }}</p>
          </div>
          <el-button v-if="parsed.text" type="primary" :loading="loading" @click="submit">保存为学生画像</el-button>
        </div>
        <div v-if="parsed.text" class="parsed-grid">
          <section class="summary-card">
            <span>教育背景</span>
            <strong>{{ parsedEducation || '未识别到教育背景' }}</strong>
          </section>
          <section class="summary-card">
            <span>实践经历</span>
            <p>{{ parsedWork || '未识别到实践经历' }}</p>
          </section>
          <section class="summary-card">
            <span>项目作品</span>
            <p>{{ parsedProject || '未识别到项目经历' }}</p>
          </section>
        </div>
        <div v-if="safeParsedSkills.length || safeParsedCertificates.length" class="tag-list">
          <el-tag v-for="skill in safeParsedSkills" :key="skill">{{ skill }}</el-tag>
          <el-tag v-for="cert in safeParsedCertificates" :key="cert" type="warning">{{ cert }}</el-tag>
        </div>
        <details v-if="parsed.text" class="resume-details">
          <summary>查看原文预览</summary>
          <p class="resume-text">{{ parsed.text }}</p>
        </details>
      </div>
    </GlassCard>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleAlert, UploadCloud } from 'lucide-vue-next'
import { profileApi } from '@/api'
import { authState } from '@/utils/auth'
import { formatEducation, formatExperience, plainTextFromMarkdown } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'

const route = useRoute()
const router = useRouter()
const mode = ref('manual')
const loading = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const parsed = ref({})
const errorMessage = ref('')
const acceptTypes = '.pdf,.doc,.docx,.txt,.md'
const safeParsedSkills = computed(() => toList(parsed.value.skills))
const safeParsedCertificates = computed(() => toList(parsed.value.certificates))
const parsedEducation = computed(() => formatEducation(parsed.value.education_json))
const parsedWork = computed(() => formatExperience(parsed.value.work_json))
const parsedProject = computed(() => formatExperience(parsed.value.project_json))
const form = reactive({
  user_id: authState.user?.id,
  name: '',
  major: '',
  grade: '',
  education: '',
  work: '',
  project: '',
  skills_certs: '',
  summary: '',
})

function onFileChange(file) {
  selectedFile.value = file.raw
  parsed.value = {}
  errorMessage.value = ''
}

function onFileRemove() {
  selectedFile.value = null
}

function toList(value) {
  if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean)
  if (typeof value === 'string') return value.split(/[,，、\n]/).map((item) => item.trim()).filter(Boolean)
  return []
}

function toText(value, fallback = '') {
  if (typeof value === 'string') return value
  if (value == null) return fallback
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return fallback
  }
}

function messageOf(error, fallback) {
  const serverMessage = error?.response?.data?.error || error?.response?.data?.parse_warning
  if (serverMessage) return serverMessage
  if (error?.response?.status >= 500) return fallback
  if (error?.code === 'ERR_NETWORK') return '无法连接后端服务，请确认后端已启动'
  return error?.message && !/^Request failed/i.test(error.message) ? error.message : fallback
}

async function submit() {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await profileApi.submit({ ...form, user_id: authState.user?.id })
    ElMessage.success('画像生成成功')
    router.push(`/profile/${data.student_id}`)
  } catch (error) {
    errorMessage.value = messageOf(error, '画像保存失败，请检查填写内容后重试')
  } finally {
    loading.value = false
  }
}

async function upload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  errorMessage.value = ''
  try {
    const data = new FormData()
    data.append('file', selectedFile.value)
    const result = await profileApi.upload(data)
    parsed.value = {
      ...result,
      text: toText(result?.text),
      parse_warning: toText(result?.parse_warning),
      skills: toList(result?.skills),
      certificates: toList(result?.certificates),
    }
    form.skills_certs = [...safeParsedSkills.value, ...safeParsedCertificates.value].join(', ')
    form.education = formatEducation(result?.education_json)
    form.work = formatExperience(result?.work_json)
    form.project = formatExperience(result?.project_json)
    form.summary = plainTextFromMarkdown(toText(result?.text)).slice(0, 600)
    if (parsed.value.parse_warning && !parsed.value.text) {
      ElMessage.warning(parsed.value.parse_warning)
    } else {
      ElMessage.success('解析完成，已回填表单')
    }
  } catch (error) {
    errorMessage.value = messageOf(error, '简历解析没有完成，请换成 DOCX/TXT，或复制简历内容到手动填写')
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  if (route.meta.uploadOnly) mode.value = 'upload'
})
</script>

<style scoped>
.page {
  padding: 26px 0 46px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.form-grid :deep(.el-form-item:nth-child(n + 4)) {
  grid-column: span 2;
}

.upload-btn {
  margin-top: 16px;
}

.upload-tip {
  margin-top: 8px;
  color: var(--muted);
  font-size: 13px;
}

.inline-error {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  color: #8b4d4d;
  background: rgba(201, 177, 176, .22);
  box-shadow: inset 0 0 0 1px rgba(201, 177, 176, .26);
}

.parsed {
  margin-top: 18px;
  padding: 22px;
}

.parsed-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}

.parsed-head h3 {
  margin: 0 0 8px;
}

.parsed-head p {
  margin: 0;
  color: var(--muted);
}

.tag-list {
  margin: 16px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.parsed-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.summary-card {
  min-height: 150px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 0 0 1px rgba(127,143,163,.12);
}

.summary-card span {
  display: block;
  margin-bottom: 10px;
  color: var(--amber);
  font-weight: 700;
}

.summary-card strong,
.summary-card p {
  margin: 0;
  color: #59616b;
  line-height: 1.75;
  white-space: pre-wrap;
}

.resume-details {
  margin-top: 14px;
  color: var(--muted);
}

.resume-details summary {
  cursor: pointer;
  font-weight: 600;
  color: #59616b;
}

.resume-text {
  max-height: 360px;
  overflow: auto;
  white-space: pre-wrap;
  color: var(--muted);
  line-height: 1.7;
}

@media (max-width: 720px) {
  .form-grid,
  .form-grid :deep(.el-form-item:nth-child(n + 4)),
  .parsed-grid {
    display: block;
  }
}
</style>
