<template>
  <section class="page">
    <LoadingSkeleton v-if="loading" />
    <template v-else>
      <GlassCard>
        <div class="profile-head">
          <el-avatar :size="72" :src="avatarUrl">{{ profile.username?.[0] }}</el-avatar>
          <div>
            <h1>{{ profile.username }}</h1>
            <p>{{ profile.role }} · {{ profile.phone || '未绑定手机' }}</p>
          </div>
          <el-upload :show-file-list="false" :auto-upload="false" :on-change="uploadAvatar">
            <el-button>更换头像</el-button>
          </el-upload>
        </div>
      </GlassCard>
      <GlassCard>
        <h2>资料编辑</h2>
        <el-form :model="form" label-position="top" class="grid">
          <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
          <el-form-item label="教育背景"><el-input v-model="form.education_text" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="技能与工具"><el-input v-model="form.skills_certs_text" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        </el-form>
        <el-button type="primary" :loading="saving" @click="save">保存资料</el-button>
      </GlassCard>
      <div class="grid2">
        <GlassCard>
          <h2>修改密码</h2>
          <el-input v-model="pwd.oldPwd" type="password" show-password placeholder="旧密码" />
          <el-input v-model="pwd.newPwd" type="password" show-password placeholder="新密码" />
          <el-button :loading="changing" @click="changePwd">更新密码</el-button>
        </GlassCard>
        <GlassCard>
          <h2>绑定手机</h2>
          <el-input v-model="phone" placeholder="新手机号" />
          <el-button :loading="binding" @click="bindPhone">绑定</el-button>
        </GlassCard>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { API_BASE_URL } from '@/api/http'
import { userApi } from '@/api'
import { formatEducation } from '@/utils/format'
import GlassCard from '@/components/GlassCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const loading = ref(true)
const saving = ref(false)
const changing = ref(false)
const binding = ref(false)
const profile = ref({})
const phone = ref('')
const pwd = reactive({ oldPwd: '', newPwd: '' })
const form = reactive({ name: '', email: '', education_text: '', skills_certs_text: '', phone: '' })
const avatarUrl = computed(() => profile.value.avatar ? `${API_BASE_URL}${profile.value.avatar}` : '')

async function load() {
  profile.value = await userApi.profile()
  Object.assign(form, {
    name: profile.value.name,
    email: profile.value.email,
    education_text: profile.value.education_text || formatEducation(profile.value.education_json),
    skills_certs_text: profile.value.skills_certs_text || (Array.isArray(profile.value.skills) ? profile.value.skills.join('、') : ''),
    phone: profile.value.phone,
  })
  phone.value = profile.value.phone || ''
}

async function save() {
  saving.value = true
  try {
    await userApi.updateProfile(form)
    ElMessage.success('资料已保存')
    await load()
  } finally {
    saving.value = false
  }
}

async function uploadAvatar(file) {
  const data = new FormData()
  data.append('file', file.raw)
  const res = await userApi.uploadAvatar(data)
  profile.value.avatar = res.avatar
}

async function changePwd() {
  changing.value = true
  try {
    await userApi.changePassword(pwd)
    ElMessage.success('密码已更新')
    pwd.oldPwd = ''
    pwd.newPwd = ''
  } finally {
    changing.value = false
  }
}

async function bindPhone() {
  binding.value = true
  try {
    await userApi.bindPhone({ phone: phone.value })
    ElMessage.success('手机号已绑定')
    await load()
  } finally {
    binding.value = false
  }
}

onMounted(async () => {
  try {
    await load()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page {
  display: grid;
  gap: 18px;
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 18px;
}

.profile-head h1,
h2 {
  margin: 0 0 8px;
  font-weight: 500;
}

p {
  margin: 0;
  color: var(--muted);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.grid2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.grid2 :deep(.el-input) {
  margin-bottom: 12px;
}

@media (max-width: 760px) {
  .grid, .grid2 {
    grid-template-columns: 1fr;
  }
}
</style>
