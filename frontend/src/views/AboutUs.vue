<template>
  <div class="about-us">
    <!-- 1. 页面头部 -->
    <header class="page-header">
      <div class="header-wrap">
        <div class="page-title">
          <span class="title-icon">ℹ️</span>
          <h1>关于我们</h1>
        </div>
        <div class="page-nav">
          <button class="back-btn" @click="$router.push('/')">← 返回首页</button>
        </div>
      </div>
    </header>

    <!-- 2. 系统介绍 -->
    <section class="system-intro">
      <div class="intro-wrap">
        <div class="intro-title">
          <span class="title-line"></span>
          <h2>大学生职业规划系统</h2>
          <span class="title-line"></span>
        </div>
        <div class="intro-content">
          <div class="intro-card">
            <div class="card-icon">🎯</div>
            <div class="card-content">
              <h3>系统定位</h3>
              <p>面向在校大学生的一站式职业规划服务平台，旨在帮助大学生清晰认知自我、了解职业方向、制定科学的职业规划，提升就业竞争力。</p>
            </div>
          </div>
          <div class="intro-card">
            <div class="card-icon">🌟</div>
            <div class="card-content">
              <h3>我们的愿景</h3>
              <p>让每一位大学生都能找到适合自己的职业方向，实现个人价值与职业发展的完美结合，为社会培养更多高素质、有规划的专业人才。</p>
            </div>
          </div>
          <div class="intro-card">
            <div class="card-icon">✨</div>
            <div class="card-content">
              <h3>核心功能</h3>
              <ul class="feature-list">
                <li>职业能力测评：多维度评估个人职业能力与兴趣倾向</li>
                <li>职业规划制定：生成个性化的职业规划方案</li>
                <li>职业画像分析：精准匹配适合的职业方向</li>
                <li>资源库查询：提供丰富的职业规划资料与求职资源</li>
                <li>报告生成：导出专业的职业规划分析报告</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. 开发团队 -->
    <section class="team-section">
      <div class="team-wrap">
        <div class="section-title">
          <h2>开发团队</h2>
          <p class="title-desc">一群热爱技术、专注教育的开发者</p>
        </div>
        <div class="team-cards">
          <div class="team-card" v-for="(member, index) in teamMembers" :key="index">
            <div class="member-avatar">{{ member.avatar }}</div>
            <div class="member-info">
              <h3 class="member-name">{{ member.name }}</h3>
              <p class="member-role">{{ member.role }}</p>
              <p class="member-desc">{{ member.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. 联系方式 -->
    <section class="contact-section">
      <div class="contact-wrap">
        <div class="section-title">
          <h2>联系我们</h2>
          <p class="title-desc">欢迎提出宝贵意见和建议</p>
        </div>
        <div class="contact-content">
          <div class="contact-info">
            <div class="contact-item">
              <span class="contact-icon">📧</span>
              <div class="contact-text">
                <h4>邮箱</h4>
                <p>support@career-plan.edu.cn</p>
              </div>
            </div>
            <div class="contact-item">
              <span class="contact-icon">📞</span>
              <div class="contact-text">
                <h4>电话</h4>
                <p>021-12345678</p>
              </div>
            </div>
            <div class="contact-item">
              <span class="contact-icon">📍</span>
              <div class="contact-text">
                <h4>地址</h4>
                <p>上海市浦东新区张江高科技园区博云路2号</p>
              </div>
            </div>
            <div class="contact-item">
              <span class="contact-icon">💬</span>
              <div class="contact-text">
                <h4>反馈渠道</h4>
                <p>可通过系统内的意见反馈功能提交建议</p>
              </div>
            </div>
          </div>
          
          <!-- 反馈表单 -->
          <div class="feedback-form">
            <h3>意见反馈</h3>
            <form @submit.prevent="submitFeedback">
              <div class="form-group">
                <label for="feedback-name">姓名</label>
                <input 
                  type="text" 
                  id="feedback-name" 
                  v-model="feedbackForm.name" 
                  placeholder="请输入您的姓名"
                  required
                >
              </div>
              <div class="form-group">
                <label for="feedback-email">邮箱</label>
                <input 
                  type="email" 
                  id="feedback-email" 
                  v-model="feedbackForm.email" 
                  placeholder="请输入您的邮箱"
                  required
                >
              </div>
              <div class="form-group">
                <label for="feedback-type">反馈类型</label>
                <select id="feedback-type" v-model="feedbackForm.type" required>
                  <option value="">请选择反馈类型</option>
                  <option value="suggestion">功能建议</option>
                  <option value="bug">问题反馈</option>
                  <option value="cooperation">合作洽谈</option>
                  <option value="other">其他</option>
                </select>
              </div>
              <div class="form-group">
                <label for="feedback-content">反馈内容</label>
                <textarea 
                  id="feedback-content" 
                  v-model="feedbackForm.content" 
                  placeholder="请详细描述您的意见或建议..."
                  rows="5"
                  required
                ></textarea>
              </div>
              <button type="submit" class="submit-btn">提交反馈</button>
            </form>
          </div>
        </div>
      </div>
    </section>

    <!-- 5. 合作伙伴 -->
    <section class="partner-section">
      <div class="partner-wrap">
        <div class="section-title">
          <h2>合作伙伴</h2>
          <p class="title-desc">感谢以下单位对本系统的支持</p>
        </div>
        <div class="partner-logos">
          <div class="partner-item" v-for="(partner, index) in partners" :key="index">
            <span class="partner-icon">{{ partner.icon }}</span>
            <p class="partner-name">{{ partner.name }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 6. 页脚 -->
    <footer class="page-footer">
      <div class="footer-wrap">
        <div class="footer-info">
          <p>© 2026 大学生职业规划系统 版权所有</p>
          <p>沪ICP备12345678号-1 | 技术支持：职业规划开发团队</p>
          <p>本系统仅用于教学与研究使用，严禁商用</p>
        </div>
        <div class="footer-links">
          <a @click="$router.push('/about')">关于我们</a>
          <a @click="$router.push('/privacy')">隐私政策</a>
          <a @click="$router.push('/terms')">使用条款</a>
        </div>
      </div>
    </footer>

    <!-- 提交成功弹窗 -->
    <div class="success-modal" v-if="showSuccessModal">
      <div class="modal-mask" @click="closeSuccessModal"></div>
      <div class="modal-content">
        <div class="success-icon">✅</div>
        <h3>提交成功！</h3>
        <p>感谢您的反馈，我们会尽快处理并回复您</p>
        <button class="confirm-btn" @click="closeSuccessModal">确定</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 团队成员数据
const teamMembers = ref([
  {
    avatar: '👨‍💻',
    name: '张明',
    role: '前端开发工程师',
    desc: '负责系统前端界面设计与交互开发，拥有3年Vue开发经验'
  },
  {
    avatar: '👩‍💻',
    name: '李丽',
    role: '后端开发工程师',
    desc: '负责系统后端接口开发与数据管理，精通Java/SpringBoot框架'
  },
  {
    avatar: '🧑‍🎨',
    name: '王浩',
    role: 'UI/UX设计师',
    desc: '负责系统界面设计与用户体验优化，注重交互细节与视觉效果'
  },
  {
    avatar: '🧑‍🏫',
    name: '赵静',
    role: '产品经理/职业规划顾问',
    desc: '负责系统需求分析与功能规划，拥有多年职业规划指导经验'
  },
  {
    avatar: '👨‍🔧',
    name: '陈杰',
    role: '测试工程师',
    desc: '负责系统功能测试与性能优化，保障系统稳定运行'
  }
])

// 合作伙伴数据
const partners = ref([
  { icon: '🏫', name: 'XX工业大学就业指导中心' },
  { icon: '💼', name: 'XX职业规划研究院' },
  { icon: '📚', name: 'XX教育出版社' },
  { icon: '💻', name: 'XX科技有限公司' },
  { icon: '🎓', name: 'XX大学生创业孵化基地' }
])

// 反馈表单数据
const feedbackForm = ref({
  name: '',
  email: '',
  type: '',
  content: ''
})

// 提交成功弹窗状态
const showSuccessModal = ref(false)

// 提交反馈
const submitFeedback = () => {
  // 模拟表单提交
  console.log('提交反馈：', feedbackForm.value)
  
  // 显示成功弹窗
  showSuccessModal.value = true
  
  // 重置表单
  feedbackForm.value = {
    name: '',
    email: '',
    type: '',
    content: ''
  }
}

// 关闭成功弹窗
const closeSuccessModal = () => {
  showSuccessModal.value = false
}
</script>

<style scoped>
/* 全局容器 */
.about-us {
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
.back-btn {
  padding: 6px 15px;
  border: 1px solid #2f54eb;
  color: #2f54eb;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}

/* 2. 系统介绍 */
.system-intro {
  padding: 50px 0;
  background: #fff;
}
.intro-wrap {
  width: 1200px;
  margin: 0 auto;
}
.intro-title {
  text-align: center;
  margin-bottom: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}
.intro-title h2 {
  font-size: 28px;
  color: #2f54eb;
  margin: 0;
}
.title-line {
  flex: 0 0 100px;
  height: 2px;
  background: #e8e8e8;
}
.intro-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}
.intro-card {
  display: flex;
  gap: 20px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 8px;
  align-items: flex-start;
}
.card-icon {
  font-size: 36px;
  margin-top: 5px;
}
.card-content {
  flex: 1;
}
.card-content h3 {
  font-size: 20px;
  color: #2f54eb;
  margin: 0 0 15px 0;
}
.card-content p {
  font-size: 16px;
  line-height: 1.8;
  color: #666;
  margin: 0;
}
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  line-height: 2;
  color: #666;
}
.feature-list li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 8px;
}
.feature-list li::before {
  content: "•";
  color: #2f54eb;
  position: absolute;
  left: 0;
  font-size: 20px;
  line-height: 1;
}

/* 3. 开发团队 */
.team-section {
  padding: 50px 0;
  background: #f8f9fa;
}
.team-wrap {
  width: 1200px;
  margin: 0 auto;
}
.section-title {
  text-align: center;
  margin-bottom: 40px;
}
.section-title h2 {
  font-size: 28px;
  color: #2f54eb;
  margin: 0 0 10px 0;
}
.title-desc {
  font-size: 16px;
  color: #999;
  margin: 0;
}
.team-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.team-card {
  background: #fff;
  border-radius: 8px;
  padding: 25px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}
.team-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}
.member-avatar {
  font-size: 60px;
  margin-bottom: 15px;
}
.member-name {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin: 0 0 5px 0;
}
.member-role {
  font-size: 14px;
  color: #2f54eb;
  margin: 0 0 10px 0;
}
.member-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

/* 4. 联系方式 */
.contact-section {
  padding: 50px 0;
  background: #fff;
}
.contact-wrap {
  width: 1200px;
  margin: 0 auto;
}
.contact-content {
  display: flex;
  gap: 40px;
}
.contact-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 25px;
}
.contact-item {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}
.contact-icon {
  font-size: 24px;
  margin-top: 5px;
}
.contact-text h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 5px 0;
}
.contact-text p {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.6;
}
.feedback-form {
  flex: 1;
  background: #f8f9fa;
  padding: 30px;
  border-radius: 8px;
}
.feedback-form h3 {
  font-size: 18px;
  color: #2f54eb;
  margin: 0 0 20px 0;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #2f54eb;
}
.submit-btn {
  width: 100%;
  padding: 12px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s;
}
.submit-btn:hover {
  background: #1d39c4;
}

/* 5. 合作伙伴 */
.partner-section {
  padding: 50px 0;
  background: #f8f9fa;
}
.partner-wrap {
  width: 1200px;
  margin: 0 auto;
}
.partner-logos {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  justify-content: center;
  margin-top: 30px;
}
.partner-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 30px;
  background: #fff;
  border-radius: 8px;
  min-width: 150px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.partner-icon {
  font-size: 40px;
}
.partner-name {
  font-size: 14px;
  color: #666;
  text-align: center;
  margin: 0;
}

/* 6. 页脚 */
.page-footer {
  background: #fff;
  padding: 40px 0;
  border-top: 1px solid #e8e8e8;
}
.footer-wrap {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.footer-info {
  text-align: center;
  font-size: 14px;
  color: #999;
  line-height: 1.8;
}
.footer-links {
  display: flex;
  gap: 20px;
}
.footer-links a {
  color: #2f54eb;
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
}
.footer-links a:hover {
  text-decoration: underline;
}

/* 提交成功弹窗 */
.success-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
}
.modal-content {
  position: relative;
  background: #fff;
  padding: 40px;
  border-radius: 8px;
  text-align: center;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.success-icon {
  font-size: 60px;
  margin-bottom: 20px;
}
.modal-content h3 {
  font-size: 20px;
  color: #333;
  margin: 0 0 10px 0;
}
.modal-content p {
  font-size: 16px;
  color: #666;
  margin: 0 0 30px 0;
}
.confirm-btn {
  padding: 10px 30px;
  background: #2f54eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .header-wrap,
  .intro-wrap,
  .team-wrap,
  .contact-wrap,
  .partner-wrap,
  .footer-wrap {
    width: 90%;
  }
}
@media (max-width: 768px) {
  .intro-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .contact-content {
    flex-direction: column;
  }
  .team-cards {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
  .partner-logos {
    gap: 20px;
  }
  .partner-item {
    min-width: 120px;
    padding: 15px 20px;
  }
}
@media (max-width: 480px) {
  .intro-title {
    gap: 10px;
  }
  .title-line {
    flex: 0 0 50px;
  }
  .intro-title h2 {
    font-size: 24px;
  }
  .section-title h2 {
    font-size: 24px;
  }
  .team-cards {
    grid-template-columns: 1fr;
  }
}
</style>