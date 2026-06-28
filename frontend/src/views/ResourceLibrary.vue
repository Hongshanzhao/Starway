<template>
  <div class="resource-library">
    <!-- 1. 页面头部（保持项目统一风格） -->
    <header class="page-header">
      <div class="header-wrap">
        <div class="page-title">
          <span class="title-icon">📚</span>
          <h1>职业规划资源库</h1>
        </div>
        <div class="page-nav">
          <button class="back-btn" @click="$router.push('/')">← 返回首页</button>
          <button class="search-btn" @click="showSearch = !showSearch">🔍 搜索资源</button>
        </div>
      </div>

      <!-- 搜索框 -->
      <div class="search-box" v-show="showSearch">
        <div class="search-wrap">
          <input 
            type="text" 
            class="search-input" 
            v-model="searchKeyword" 
            placeholder="搜索资源名称/关键词..."
            @keyup.enter="searchResources"
          >
          <button class="do-search-btn" @click="searchResources">搜索</button>
          <button class="reset-search-btn" @click="resetSearch">重置</button>
        </div>
      </div>
    </header>

    <!-- 2. 资源分类导航 -->
    <section class="category-nav">
      <div class="nav-wrap">
        <div 
          class="category-item" 
          v-for="category in categories" 
          :key="category.key"
          :class="{ active: activeCategory === category.key }"
          @click="switchCategory(category.key)"
        >
          <span class="category-icon">{{ category.icon }}</span>
          <span class="category-name">{{ category.name }}</span>
        </div>
      </div>
    </section>

    <!-- 3. 资源列表区 -->
    <section class="resource-section">
      <div class="resource-wrap">
        <!-- 筛选器 -->
        <div class="filter-bar">
          <div class="filter-left">
            <span class="filter-title">筛选：</span>
            <select class="filter-select" v-model="sortType" @change="sortResources">
              <option value="hot">按热度</option>
              <option value="new">按最新</option>
              <option value="download">按下载量</option>
            </select>
            <select class="filter-select" v-model="resourceLevel" @change="filterResources">
              <option value="all">全部难度</option>
              <option value="beginner">入门级</option>
              <option value="intermediate">进阶级</option>
              <option value="advanced">高级</option>
            </select>
          </div>
          <div class="filter-right">
            <span class="resource-count">共 {{ filteredResources.length }} 个资源</span>
          </div>
        </div>

        <!-- 资源列表 -->
        <div class="resource-list" v-if="filteredResources.length > 0">
          <div class="resource-card" v-for="(resource, index) in filteredResources" :key="index">
            <div class="resource-header">
              <div class="resource-title">{{ resource.title }}</div>
              <div class="resource-tag-group">
                <span class="resource-tag level-tag" :class="resource.level">{{ getLevelText(resource.level) }}</span>
                <span class="resource-tag type-tag">{{ resource.fileType }}</span>
                <span class="resource-tag hot-tag" v-if="resource.hot">热门</span>
              </div>
            </div>
            <div class="resource-body">
              <div class="resource-desc">{{ resource.description }}</div>
              <div class="resource-meta">
                <span class="meta-item">📅 {{ resource.uploadTime }}</span>
                <span class="meta-item">📥 {{ resource.downloadCount }}次下载</span>
                <span class="meta-item">⭐ {{ resource.score }}分</span>
              </div>
            </div>
            <div class="resource-footer">
              <button class="preview-btn" @click="previewResource(resource)">预览</button>
              <button class="download-btn" @click="downloadResource(resource)">
                <span class="download-icon">⬇️</span>
                下载
              </button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="empty-state" v-else>
          <div class="empty-icon">📂</div>
          <div class="empty-text">
            {{ searchKeyword ? '未找到相关资源，请更换关键词重试' : '该分类下暂无资源，敬请期待' }}
          </div>
          <button class="empty-btn" @click="resetSearch" v-if="searchKeyword">清空搜索</button>
        </div>

        <!-- 分页 -->
        <div class="pagination" v-if="filteredResources.length > 0">
          <button class="page-btn" @click="currentPage--" :disabled="currentPage === 1">上一页</button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="page-btn" @click="currentPage++" :disabled="currentPage === totalPages">下一页</button>
        </div>
      </div>
    </section>

    <!-- 资源预览弹窗 - 核心修复：v-if 替代 v-show，避免空值解析 -->
    <div class="preview-modal" v-if="previewResourceData">
      <div class="modal-mask" @click="closePreview"></div>
      <div class="modal-content">
        <div class="modal-header">
          <!-- 增加空值保护 -->
          <h3>{{ previewResourceData?.title || '资源预览' }}</h3>
          <button class="close-btn" @click="closePreview">×</button>
        </div>
        <div class="modal-body">
          <!-- 文档预览 - 增加空值保护 -->
          <div class="doc-preview" v-if="previewResourceData && ['PDF', 'DOC', 'TXT'].includes(previewResourceData.fileType)">
            <div class="preview-tip" v-if="previewResourceData.fileType !== 'TXT'">
              以下为文档内容预览（完整内容请下载查看）
            </div>
            <div class="preview-content">
              {{ previewResourceData?.previewContent || '暂无预览内容，可直接下载查看' }}
            </div>
          </div>

          <!-- 视频预览 - 增加空值保护 -->
          <div class="video-preview" v-if="previewResourceData && previewResourceData.fileType === '视频'">
            <video class="preview-video" controls :src="previewResourceData?.url || ''">
              你的浏览器不支持视频播放
            </video>
          </div>

          <!-- 链接类资源 - 增加空值保护 -->
          <div class="link-preview" v-if="previewResourceData && previewResourceData.fileType === '链接'">
            <div class="link-tip">点击下方链接访问资源：</div>
            <a :href="previewResourceData?.url || '#'" target="_blank" class="resource-link">{{ previewResourceData?.url || '暂无链接' }}</a>
          </div>

          <!-- 工具类资源 - 增加空值保护 -->
          <div class="tool-preview" v-if="previewResourceData && previewResourceData.fileType === '工具'">
            <div class="tool-desc">{{ previewResourceData?.description || '暂无工具描述' }}</div>
            <a :href="previewResourceData?.url || '#'" target="_blank" class="tool-link">前往使用</a>
          </div>
        </div>
        <div class="modal-footer">
          <button class="download-btn" @click="downloadResource(previewResourceData)">下载/访问资源</button>
          <button class="close-btn" @click="closePreview">关闭</button>
        </div>
      </div>
    </div>

    <!-- 4. 页脚 -->
    <footer class="page-footer">
      <div class="footer-wrap">
        © 2026 大学生职业规划系统 | 优质资源 · 助力成长
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 核心状态
const showSearch = ref(false) // 显示搜索框
const searchKeyword = ref('') // 搜索关键词
const activeCategory = ref('all') // 激活的分类
const sortType = ref('hot') // 排序类型：hot/new/download
const resourceLevel = ref('all') // 难度筛选
const currentPage = ref(1) // 当前页码
const pageSize = ref(8) // 每页数量
const previewResourceData = ref(null) // 预览的资源数据

// 资源分类
const categories = ref([
  { key: 'all', name: '全部资源', icon: '📁' },
  { key: 'careerPlan', name: '职业规划文档', icon: '📄' },
  { key: 'ability', name: '能力提升资料', icon: '📖' },
  { key: 'video', name: '教学视频', icon: '🎬' },
  { key: 'tool', name: '实用工具', icon: '🔧' },
  { key: 'experience', name: '求职经验', icon: '💡' }
])

// 模拟资源数据（实际项目可从后端获取）
const resourceList = ref([
  // 职业规划文档
  {
    id: 1,
    title: '大学生职业规划书模板（完整版）',
    category: 'careerPlan',
    description: '包含自我认知、职业分析、规划实施、评估调整等完整模块的职业规划书模板，可直接填写使用',
    fileType: 'DOC',
    level: 'beginner',
    uploadTime: '2026-01-15',
    downloadCount: 1258,
    score: 4.8,
    hot: true,
    url: '/resources/career-plan-template.doc',
    previewContent: '【大学生职业规划书】\n\n一、自我认知\n1. 个人基本情况：\n   姓名：\n   专业：\n   年级：\n   性格特点：\n\n2. 职业兴趣：\n   通过霍兰德职业兴趣测试，我的职业兴趣类型为：\n\n3. 能力评估：\n   优势能力：\n   待提升能力：\n\n二、职业环境分析\n1. 行业发展现状：\n2. 目标职业要求：\n3. 竞争分析：\n\n（完整内容请下载查看）'
  },
  {
    id: 2,
    title: '不同专业职业规划方向指南',
    category: 'careerPlan',
    description: '涵盖计算机、金融、教育、医学等热门专业的职业规划方向分析和发展建议',
    fileType: 'PDF',
    level: 'intermediate',
    uploadTime: '2026-01-10',
    downloadCount: 896,
    score: 4.7,
    hot: true,
    url: '/resources/major-career-guide.pdf',
    previewContent: '【不同专业职业规划方向指南】\n\n1. 计算机专业\n   主流方向：软件开发、算法工程师、产品经理、测试工程师\n   发展路径：大一打基础，大二学框架，大三找实习，大四冲刺校招\n   必备技能：编程语言、数据结构、项目经验\n\n2. 金融专业\n   主流方向：银行、证券、基金、保险、投行\n   发展路径：考证（证券从业、CFA）、实习、校招\n\n（完整内容请下载查看）'
  },
  // 能力提升资料
  {
    id: 3,
    title: '通用能力提升训练手册',
    category: 'ability',
    description: '包含学习能力、沟通能力、团队协作等通用能力的提升方法和训练计划',
    fileType: 'PDF',
    level: 'beginner',
    uploadTime: '2026-01-20',
    downloadCount: 753,
    score: 4.6,
    hot: false,
    url: '/resources/ability-training.pdf',
    previewContent: '【通用能力提升训练手册】\n\n第一章 学习能力提升\n1. 高效学习方法：\n   - 费曼学习法：把学到的知识讲给别人听\n   - 番茄工作法：25分钟专注+5分钟休息\n   - 思维导图：梳理知识体系\n\n2. 每日训练计划：\n   - 每天阅读30分钟专业书籍\n   - 每周总结学习收获\n\n（完整内容请下载查看）'
  },
  {
    id: 4,
    title: '求职面试技巧大全',
    category: 'ability',
    description: '涵盖简历制作、自我介绍、常见面试问题回答技巧、薪资谈判等全流程指导',
    fileType: 'DOC',
    level: 'intermediate',
    uploadTime: '2026-01-18',
    downloadCount: 987,
    score: 4.9,
    hot: true,
    url: '/resources/interview-skills.doc',
    previewContent: '【求职面试技巧大全】\n\n一、简历制作\n1. 简历结构：个人信息、教育背景、项目经验、技能证书、自我评价\n2. 突出重点：用数据说话，量化成果\n3. 避坑指南：避免冗长、虚假信息、格式混乱\n\n二、面试准备\n1. 自我介绍：30秒版本、2分钟版本\n2. 常见问题：\n   - 为什么选择我们公司？\n   - 你的优缺点是什么？\n   - 未来3-5年的职业规划？\n\n（完整内容请下载查看）'
  },
  // 教学视频
  {
    id: 5,
    title: '职业规划基础课程',
    category: 'video',
    description: '从零开始学习职业规划的核心方法和步骤，共8课时',
    fileType: '视频',
    level: 'beginner',
    uploadTime: '2026-01-05',
    downloadCount: 642,
    score: 4.7,
    hot: false,
    url: '/videos/career-plan-basic.mp4',
    previewContent: ''
  },
  {
    id: 6,
    title: '简历制作与面试技巧实战课',
    category: 'video',
    description: '实战教学如何制作高分简历，掌握面试核心技巧',
    fileType: '视频',
    level: 'intermediate',
    uploadTime: '2026-01-12',
    downloadCount: 789,
    score: 4.8,
    hot: true,
    url: '/videos/resume-interview.mp4',
    previewContent: ''
  },
  // 实用工具
  {
    id: 7,
    title: '职业兴趣测评工具',
    category: 'tool',
    description: '霍兰德职业兴趣测评在线工具，帮助了解自身职业兴趣倾向',
    fileType: '工具',
    level: 'beginner',
    uploadTime: '2026-01-22',
    downloadCount: 543,
    score: 4.5,
    hot: false,
    url: 'https://tools.example.com/career-interest-test',
    previewContent: ''
  },
  {
    id: 8,
    title: '简历制作在线工具',
    category: 'tool',
    description: '提供多种简历模板，支持在线编辑、导出PDF/Word格式',
    fileType: '工具',
    level: 'beginner',
    uploadTime: '2026-01-25',
    downloadCount: 678,
    score: 4.7,
    hot: false,
    url: 'https://tools.example.com/resume-maker',
    previewContent: ''
  },
  // 求职经验
  {
    id: 9,
    title: '大厂校招经验分享合集',
    category: 'experience',
    description: '包含阿里、腾讯、字节、华为等大厂校招的真实经验分享和避坑指南',
    fileType: 'PDF',
    level: 'advanced',
    uploadTime: '2026-01-08',
    downloadCount: 1024,
    score: 4.9,
    hot: true,
    url: '/resources/company-recruitment.pdf',
    previewContent: '【大厂校招经验分享合集】\n\n1. 阿里巴巴校招经验\n   - 招聘流程：网申→笔试→面试（3轮技术+1轮HR）→Offer\n   - 重点考察：基础扎实、项目经验、学习能力\n   - 准备建议：提前刷题、熟悉开源项目\n\n2. 腾讯校招经验\n   - 招聘流程：网申→在线笔试→群面→技术面→HR面\n   - 重点考察：算法能力、沟通表达、团队协作\n\n（完整内容请下载查看）'
  },
  {
    id: 10,
    title: '考研VS就业选择指南',
    category: 'experience',
    description: '详细分析考研和就业的利弊，帮助做出适合自己的选择',
    fileType: 'DOC',
    level: 'intermediate',
    uploadTime: '2026-01-16',
    downloadCount: 876,
    score: 4.6,
    hot: false,
    url: '/resources/study-or-work.doc',
    previewContent: '【考研VS就业选择指南】\n\n一、考研的优势与劣势\n优势：\n1. 提升学历，增加就业竞争力\n2. 延缓就业压力，有更多时间思考职业方向\n3. 深入学习专业知识，适合学术型人才\n\n劣势：\n1. 时间成本高（3年）\n2. 经济成本高\n3. 就业市场变化快，3年后形势未知\n\n二、就业的优势与劣势\n（完整内容请下载查看）'
  },
  {
    id: 11,
    title: '留学生职业规划特殊指南',
    category: 'experience',
    description: '针对留学生的职业规划特点和回国就业/海外就业的建议',
    fileType: 'PDF',
    level: 'advanced',
    uploadTime: '2026-01-19',
    downloadCount: 321,
    score: 4.7,
    hot: false,
    url: '/resources/overseas-career.pdf',
    previewContent: '【留学生职业规划特殊指南】\n\n一、回国就业优势\n1. 语言优势\n2. 国际化视野\n3. 跨文化沟通能力\n\n二、回国就业挑战\n1. 国内就业市场不熟悉\n2. 校招时间不匹配\n3. 学历认证问题\n\n（完整内容请下载查看）'
  },
  {
    id: 12,
    title: '自由职业者职业规划指南',
    category: 'experience',
    description: '适合想做自由职业的大学生的规划建议，包含技能准备、客户获取、风险控制等',
    fileType: 'DOC',
    level: 'advanced',
    uploadTime: '2026-01-21',
    downloadCount: 289,
    score: 4.5,
    hot: false,
    url: '/resources/freelance-career.doc',
    previewContent: '【自由职业者职业规划指南】\n\n一、自由职业适合人群\n1. 具备专业技能（设计、编程、写作、翻译等）\n2. 自律性强，时间管理能力好\n3. 抗压能力强，能接受收入波动\n\n二、核心技能准备\n1. 专业技能：达到商业化水平\n2. 营销技能：自我推广、客户沟通\n3. 管理技能：时间管理、财务管理\n\n（完整内容请下载查看）'
  }
])

// 筛选后的资源列表
const filteredResources = computed(() => {
  let result = resourceList.value

  // 分类筛选
  if (activeCategory.value !== 'all') {
    result = result.filter(item => item.category === activeCategory.value)
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item => 
      item.title.toLowerCase().includes(keyword) || 
      item.description.toLowerCase().includes(keyword)
    )
  }

  // 难度筛选
  if (resourceLevel.value !== 'all') {
    result = result.filter(item => item.level === resourceLevel.value)
  }

  // 排序
  switch (sortType.value) {
    case 'hot':
      result = result.sort((a, b) => {
        // 热门优先，然后按下载量
        if (a.hot && !b.hot) return -1
        if (!a.hot && b.hot) return 1
        return b.downloadCount - a.downloadCount
      })
      break
    case 'new':
      result = result.sort((a, b) => new Date(b.uploadTime) - new Date(a.uploadTime))
      break
    case 'download':
      result = result.sort((a, b) => b.downloadCount - a.downloadCount)
      break
  }

  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

// 总页数
const totalPages = computed(() => {
  let total = resourceList.value.length
  
  // 应用筛选条件计算总数
  if (activeCategory.value !== 'all') {
    total = resourceList.value.filter(item => item.category === activeCategory.value).length
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    total = resourceList.value.filter(item => 
      item.title.toLowerCase().includes(keyword) || 
      item.description.toLowerCase().includes(keyword)
    ).length
  }
  if (resourceLevel.value !== 'all') {
    total = resourceList.value.filter(item => item.level === resourceLevel.value).length
  }

  return Math.ceil(total / pageSize.value)
})

// 初始化
onMounted(() => {
  // 可在这里从后端加载资源数据
})

// 切换分类
const switchCategory = (categoryKey) => {
  activeCategory.value = categoryKey
  currentPage.value = 1 // 切换分类重置页码
}

// 搜索资源
const searchResources = () => {
  currentPage.value = 1 // 搜索重置页码
}

// 重置搜索
const resetSearch = () => {
  searchKeyword.value = ''
  sortType.value = 'hot'
  resourceLevel.value = 'all'
  currentPage.value = 1
}

// 排序资源
const sortResources = () => {
  currentPage.value = 1 // 排序重置页码
}

// 筛选资源
const filterResources = () => {
  currentPage.value = 1 // 筛选重置页码
}

// 获取难度文本
const getLevelText = (level) => {
  const levelMap = {
    'beginner': '入门级',
    'intermediate': '进阶级',
    'advanced': '高级'
  }
  return levelMap[level] || '未知'
}

// 预览资源 - 增加空值检查
const previewResource = (resource) => {
  if (resource && resource.id) {
    previewResourceData.value = resource
  }
}

// 关闭预览 - 安全重置为null
const closePreview = () => {
  previewResourceData.value = null
}

// 下载资源 - 增加空值保护
const downloadResource = (resource) => {
  if (!resource) return
  
  // 模拟下载/跳转
  if (resource.fileType === '工具' || resource.fileType === '链接') {
    if (resource.url) {
      window.open(resource.url, '_blank')
      alert(`已为你打开【${resource.title}】的访问链接！`)
    } else {
      alert('该资源暂无有效链接！')
    }
  } else {
    // 模拟文件下载
    const link = document.createElement('a')
    link.href = resource.url || '#'
    link.download = resource.title + '.' + (resource.fileType || 'txt').toLowerCase()
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 更新下载量（模拟）
    if (resource.downloadCount !== undefined) {
      resource.downloadCount += 1
    }
    alert(`开始下载【${resource.title}】，请稍候...`)
  }
}
</script>

<style scoped>
/* 全局容器 */
.resource-library {
  width: 100%;
  min-height: 100vh;
  font-family: "Microsoft Yahei", sans-serif;
  color: #333;
  background: #f8f9fa;
  margin: 0;
  padding: 0;
}

/* 1. 页面头部 */
.page-header {
  height: 70px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  width: 100%;
  position: relative;
}
.header-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}
.page-title {
  display: flex;
  align-items: center;
  color: #2f54eb;
}
.title-icon {
  font-size: 24px;
  margin-right: 8px;
}
.page-title h1 {
  font-size: 20px;
  margin: 0;
}
.page-nav {
  display: flex;
  gap: 10px;
}
.back-btn, .search-btn {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}

/* 搜索框 */
.search-box {
  position: absolute;
  top: 70px;
  left: 0;
  width: 100%;
  background: #fff;
  padding: 15px 0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  z-index: 10;
}
.search-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 10px;
}
.search-input {
  flex: 1;
  height: 40px;
  padding: 0 15px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  outline: none;
  font-size: 14px;
}
.do-search-btn {
  padding: 0 20px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.reset-search-btn {
  padding: 0 20px;
  background: #fff;
  color: #666;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: pointer;
}

/* 2. 资源分类导航 */
.category-nav {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 10px 0;
}
.nav-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 5px;
  overflow-x: auto;
  padding: 5px 0;
}
.nav-wrap::-webkit-scrollbar {
  height: 4px;
}
.nav-wrap::-webkit-scrollbar-thumb {
  background: #e8e8e8;
  border-radius: 2px;
}
.category-item {
  padding: 8px 20px;
  border-radius: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  transition: all 0.3s;
}
.category-item.active {
  background: #2f54eb;
  color: #fff;
}
.category-item:hover:not(.active) {
  background: #f0f2ff;
}
.category-icon {
  font-size: 16px;
}

/* 3. 资源列表区 */
.resource-section {
  padding: 30px 0;
}
.resource-wrap {
  width: 1200px;
  margin: 0 auto;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px 15px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.filter-left {
  display: flex;
  align-items: center;
  gap: 15px;
}
.filter-title {
  font-weight: bold;
  color: #666;
}
.filter-select {
  padding: 5px 10px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  outline: none;
}
.resource-count {
  color: #666;
  font-size: 14px;
}

/* 资源列表 */
.resource-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}
.resource-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 15px;
  transition: transform 0.3s, box-shadow 0.3s;
}
.resource-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}
.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}
.resource-title {
  font-size: 16px;
  font-weight: bold;
  color: #2f54eb;
  flex: 1;
}
.resource-tag-group {
  display: flex;
  gap: 8px;
}
.resource-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.level-tag {
  background: #f0f2ff;
  color: #2f54eb;
}
.level-tag.beginner {
  background: #e6f7ff;
  color: #1890ff;
}
.level-tag.intermediate {
  background: #f0f2ff;
  color: #2f54eb;
}
.level-tag.advanced {
  background: #fff1f0;
  color: #f5222d;
}
.type-tag {
  background: #f6ffed;
  color: #52c41a;
}
.hot-tag {
  background: #fff7e6;
  color: #fa8c16;
}
.resource-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}
.resource-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3; /* 修复兼容性警告 */
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.resource-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #999;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.resource-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}
.preview-btn {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.download-btn {
  padding: 6px 15px;
  border: none;
  color: #fff;
  background: #2f54eb;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 0;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 30px;
}
.empty-icon {
  font-size: 60px;
  color: #e8e8e8;
  margin-bottom: 20px;
}
.empty-text {
  font-size: 16px;
  color: #999;
  margin-bottom: 20px;
}
.empty-btn {
  padding: 8px 20px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
}
.page-btn {
  padding: 8px 15px;
  border: 1px solid #e8e8e8;
  color: #666;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.page-info {
  color: #666;
}

/* 资源预览弹窗 */
.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
}
.modal-mask {
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
}
.modal-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  max-width: 90%;
  max-height: 90vh;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  margin: 0;
  color: #2f54eb;
}
.close-btn {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}
.close-btn:hover {
  color: #333;
}
.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}
.preview-tip {
  color: #999;
  font-size: 14px;
  margin-bottom: 15px;
}
.preview-content {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
}
.preview-video {
  width: 100%;
  height: 400px;
  border-radius: 4px;
}
.link-tip {
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}
.resource-link, .tool-link {
  display: block;
  padding: 10px 15px;
  background: #f0f2ff;
  color: #2f54eb;
  border-radius: 4px;
  text-decoration: none;
  word-break: break-all;
  margin-bottom: 15px;
}
.tool-desc {
  margin-bottom: 20px;
  line-height: 1.6;
}
.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 4. 页脚 */
.page-footer {
  background: #fff;
  padding: 20px 0;
  border-top: 1px solid #e8e8e8;
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 20px;
}
.footer-wrap {
  width: 1200px;
  margin: 0 auto;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .header-wrap, .search-wrap, .nav-wrap, .resource-wrap, .footer-wrap {
    width: 90%;
  }
  .resource-list {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .filter-left {
    width: 100%;
  }
  .preview-video {
    height: 250px;
  }
}
</style>