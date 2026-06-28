<template>
  <div class="resume-upload-container">
    <el-page-header content="简历上传与信息采集" @back="$router.push('/')"></el-page-header>

    <el-card class="upload-card">
      <template #header>
        <span>第一步：上传你的简历</span>
      </template>
      <el-upload
        class="upload-dragger"
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        accept=".pdf,.doc,.docx"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击上传</em>
        </div>
        <div class="el-upload__tip">
          支持 PDF / Word 格式，系统将自动解析你的信息
        </div>
      </el-upload>

      <div v-if="parsedInfo.name" class="parsed-info">
        <h4>📋 系统自动识别到以下信息：</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="姓名">{{ parsedInfo.name }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ parsedInfo.major }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ parsedInfo.education }}</el-descriptions-item>
          <el-descriptions-item label="技能">{{ parsedInfo.skills.join(', ') }}</el-descriptions-item>
        </el-descriptions>
        <p class="tip-text">请在下一步确认并补充信息</p>
      </div>

      <div class="btn-group">
        <el-button type="primary" @click="goToNextStep" :disabled="!parsedInfo.name">
          确认信息，进入下一步
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
// 注意：真实项目中，简历解析需要后端接口，这里用模拟数据演示
import * as pdfParse from 'pdf-parse' // 示例库，需安装

const router = useRouter()
const parsedInfo = ref({
  name: '',
  major: '',
  education: '本科',
  skills: []
})

// 处理文件上传
const handleFileChange = async (file) => {
  const rawFile = file.raw
  if (!rawFile.type.includes('pdf') && !rawFile.type.includes('word')) {
    ElMessage.error('仅支持上传 PDF 或 Word 文档！')
    return
  }

  // 模拟解析过程
  ElMessage.loading({
    message: '正在解析简历...',
    duration: 0
  })

  // --- 真实项目中，这里应调用后端接口 /api/resume/parse ---
  // 这里用 setTimeout 模拟异步请求
  setTimeout(() => {
    // 模拟解析结果
    parsedInfo.value = {
      name: '张三',
      major: '计算机科学与技术',
      education: '本科',
      skills: ['Python', 'SQL', 'Vue.js', '数据分析']
    }
    ElMessage.success('简历解析完成！')
  }, 2000)
}

// 跳转到基础信息确认页
const goToNextStep = () => {
  // 将解析出的信息存入本地，供下一页使用
  localStorage.setItem('resumeParsedInfo', JSON.stringify(parsedInfo.value))
  router.push('/student-ability')
}
</script>

<style scoped>
.resume-upload-container {
  padding: 20px;
  background-color: #fff;
  min-height: 100vh;
}
.upload-card {
  max-width: 600px;
  margin: 0 auto;
}
.parsed-info {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}
.tip-text {
  color: #666;
  font-size: 12px;
  margin-top: 10px;
  text-align: center;
}
.btn-group {
  text-align: center;
  margin-top: 20px;
}
</style>