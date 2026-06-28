<template>
  <div class="career-home">
    <!-- 1. 顶部导航（整合搜索框）- 固定在顶部 -->
    <header class="top-nav">
      <div class="nav-wrap">
        <div class="nav-left">
          <div class="logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <ul class="nav-menu">
            <li class="menu-item active" @click="$router.push('/')">首页</li>
            <li class="menu-item" @click="$router.push('/job-portrait')">岗位画像</li>
            <li class="menu-item" @click="$router.push('/career-planning')">职业规划</li>
            <li class="menu-item" @click="$router.push('/resource-library')">资源库</li>
            <li class="menu-item" @click="$router.push('/about-us')">关于我们</li>
            <li class="menu-item dropdown">
              核心功能 ▼
              <ul class="dropdown-menu">
                <li class="dropdown-item" @click="goToFeature('测评')">
                  <span class="color-dot red"></span> 职业兴趣测评
                </li>
                <li class="dropdown-item" @click="goToFeature('分析')">
                  <span class="color-dot orange"></span> 能力短板分析
                </li>
                <li class="dropdown-item" @click="goToFeature('规划')">
                  <span class="color-dot green"></span> 发展路径规划
                </li>
                <li class="dropdown-item" @click="goToFeature('导出')">
                  <span class="color-dot blue"></span> 规划报告导出
                </li>
              </ul>
            </li>
          </ul>
        </div>

        <!-- 导航栏右侧：搜索框 + 原有功能 -->
        <div class="nav-right">
          <!-- 导航栏内的搜索框 -->
          <div class="nav-search-wrap">
            <input 
              type="text" 
              class="nav-search-input" 
              placeholder="搜索职业方向、专业、院校、岗位类型"
              v-model="searchKeyword"
              @keyup.enter="handleSearch"
            >
            <button class="nav-search-btn" @click="handleSearch">搜索</button>
          </div>

          <button class="btn-toggle-theme" @click="toggleTheme">🌙</button>
          
          <!-- 未登录：显示登录/注册按钮 -->
          <button class="btn-login" @click="$router.push('/login')" v-if="!isLogin">登录</button>
          <button class="btn-register" @click="$router.push('/register')" v-if="!isLogin">注册</button>
          
          <!-- 已登录：显示用户头像 + 下拉菜单 -->
          <div class="user-profile" v-if="isLogin">
            <img 
              :src="userAvatar" 
              alt="用户头像" 
              class="avatar"
              @click="toggleUserMenu"
            >
            <ul class="user-menu" v-show="showUserMenu">
              <li @click="$router.push('/profile')">个人中心</li>
              <li @click="$router.push('/my-plan')">我的规划</li>
              <li @click="logout">退出登录</li>
            </ul>
          </div>
        </div>
      </div>
    </header>

    <!-- 2. 首页核心内容区 -->
    <main class="home-content">
      <!-- 2.1 英雄区（Banner） -->
      <section class="hero-section">
        <div class="hero-bg"></div>
        <div class="hero-content">
          <h1 class="hero-title">
            精准规划<span class="highlight">职业方向</span>，<br>
            开启<span class="highlight">未来无限</span>可能
          </h1>
          <p class="hero-desc">
            基于大数据和AI的大学生职业规划平台，为你匹配最适合的职业路径
          </p>
          <div class="hero-actions">
            <button class="btn-primary" @click="$router.push('/career-assessment')">
              立即测评
            </button>
            <button class="btn-secondary" @click="$router.push('/job-library')">
              浏览岗位库
            </button>
          </div>
        </div>
      </section>

      <!-- 2.2 核心功能区 -->
      <section class="features-section">
        <div class="section-header">
          <h2 class="section-title">核心功能</h2>
          <p class="section-desc">全方位助力你的职业规划</p>
        </div>
        <div class="features-grid">
          <div class="feature-card" @click="$router.push('/career-assessment')">
            <div class="feature-icon">📊</div>
            <h3 class="feature-title">职业兴趣测评</h3>
            <p class="feature-desc">基于MBTI、霍兰德等理论，精准定位你的职业兴趣</p>
          </div>
          <div class="feature-card" @click="$router.push('/job-portrait')">
            <div class="feature-icon">👤</div>
            <h3 class="feature-title">岗位画像分析</h3>
            <p class="feature-desc">深入了解岗位要求、技能需求、发展前景</p>
          </div>
          <div class="feature-card" @click="$router.push('/career-planning')">
            <div class="feature-icon">🗺️</div>
            <h3 class="feature-title">职业路径规划</h3>
            <p class="feature-desc">定制个性化的职业发展路径，明确成长方向</p>
          </div>
          <div class="feature-card" @click="$router.push('/resource-library')">
            <div class="feature-icon">📚</div>
            <h3 class="feature-title">学习资源库</h3>
            <p class="feature-desc">提供岗位相关的学习资料、证书指南、技能课程</p>
          </div>
        </div>
      </section>

      <!-- 2.3 热门岗位区 -->
      <section class="hot-jobs-section">
        <div class="section-header">
          <h2 class="section-title">热门岗位</h2>
          <p class="section-desc">当前最受关注的职业方向</p>
          <button class="btn-more" @click="$router.push('/job-library')">查看更多</button>
        </div>
        <div class="jobs-grid" v-if="hotJobs.length > 0">
          <div 
            class="job-card" 
            v-for="job in hotJobs" 
            :key="job.id"
            @click="$router.push(`/job-detail/${job.id}`)"
          >
            <div class="job-header">
              <h3 class="job-name">{{ job.job_name }}</h3>
              <span class="salary-range">{{ job.salary_range }}</span>
            </div>
            <div class="job-info">
              <span class="company">{{ job.company }}</span>
              <span class="location">{{ job.location }}</span>
              <span class="industry">{{ job.industry }}</span>
            </div>
            <div class="job-tags">
              <span class="tag" v-for="tag in getJobTags(job)" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
        <div class="empty-state" v-else>
          <p>暂无热门岗位数据</p>
        </div>
      </section>

      <!-- 2.4 行业趋势区 -->
      <section class="trends-section">
        <div class="section-header">
          <h2 class="section-title">行业趋势</h2>
          <p class="section-desc">了解最新的行业发展动态</p>
        </div>
        <div class="trends-content">
          <div class="chart-container">
            <canvas id="industryChart"></canvas>
          </div>
          <div class="trends-list">
            <div class="trend-item" v-for="trend in industryTrends" :key="trend.industry">
              <div class="trend-icon">{{ getIndustryIcon(trend.industry) }}</div>
              <div class="trend-info">
                <h4 class="industry-name">{{ trend.industry }}</h4>
                <p class="trend-desc">{{ trend.description }}</p>
                <span class="growth-rate">{{ trend.growth_rate }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 3. 页脚 -->
    <footer class="home-footer">
      <div class="footer-content">
        <div class="footer-left">
          <div class="logo footer-logo">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">大学生职业规划系统</span>
          </div>
          <p class="copyright">© 2026 大学生职业规划系统 版权所有</p>
        </div>
        <div class="footer-right">
          <ul class="footer-links">
            <li><a href="/about-us">关于我们</a></li>
            <li><a href="/contact">联系我们</a></li>
            <li><a href="/privacy">隐私政策</a></li>
            <li><a href="/terms">使用条款</a></li>
          </ul>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import Chart from 'chart.js/auto';

// 全局取消axios的token参数（避免自动拼接）
axios.interceptors.request.use(config => {
  // 移除所有token相关参数
  if (config.params && config.params.token) {
    delete config.params.token;
  }
  // 移除Authorization头（如果有）
  if (config.headers && config.headers.Authorization) {
    delete config.headers.Authorization;
  }
  return config;
});

export default {
  name: 'Home',
  setup() {
    const router = useRouter();
    
    // 响应式数据
    const isLogin = ref(true); // 模拟已登录
    const userAvatar = ref('https://picsum.photos/200/200?random=1');
    const showUserMenu = ref(false);
    const searchKeyword = ref('');
    const hotJobs = ref([]);
    const industryTrends = ref([]);
    const industryChart = ref(null);
    const theme = ref('light');

    // 模拟行业趋势数据（如果接口调用失败则使用）
    const mockIndustryTrends = [
      { industry: '人工智能', description: '人才需求持续增长，算法工程师缺口最大', growth_rate: '+25%' },
      { industry: '大数据', description: '数据分析师、数据工程师需求激增', growth_rate: '+20%' },
      { industry: '云计算', description: '云原生工程师成为热门岗位', growth_rate: '+18%' },
      { industry: '新能源', description: '光伏、储能领域人才需求翻倍', growth_rate: '+30%' },
      { industry: '生物医药', description: '研发岗位需求持续上升', growth_rate: '+15%' }
    ];

    // 模拟热门岗位数据（如果接口调用失败则使用）
    const mockHotJobs = [
      { id: 1, job_name: '算法工程师', salary_range: '20K-40K', company: '字节跳动', location: '北京', industry: '人工智能', company_size: '10000+' },
      { id: 2, job_name: '数据分析师', salary_range: '15K-25K', company: '阿里巴巴', location: '杭州', industry: '大数据', company_size: '10000+' },
      { id: 3, job_name: '前端开发工程师', salary_range: '18K-30K', company: '腾讯', location: '深圳', industry: '互联网', company_size: '10000+' },
      { id: 4, job_name: '新能源工程师', salary_range: '16K-28K', company: '宁德时代', location: '宁德', industry: '新能源', company_size: '10000+' },
      { id: 5, job_name: '产品经理', salary_range: '18K-35K', company: '美团', location: '北京', industry: '互联网', company_size: '10000+' },
      { id: 6, job_name: '生物医药研发', salary_range: '15K-30K', company: '恒瑞医药', location: '上海', industry: '生物医药', company_size: '5000-10000' }
    ];

    // 方法：获取热门岗位（彻底移除token参数）
    const fetchHotJobs = async () => {
      try {
        console.log('开始请求热门岗位数据，路径：/api/jobs/simple_search');
        // 纯请求，不带任何token参数
        const response = await axios.get('http://localhost:5000/api/jobs/simple_search', {
          params: {
            page: 1,
            size: 6
          }
        });
        hotJobs.value = response.data;
        console.log('热门岗位数据获取成功:', hotJobs.value);
      } catch (error) {
        console.error('获取热门岗位失败:', error.message);
        // 强制使用模拟数据，避免接口错误影响页面
        hotJobs.value = mockHotJobs;
      }
    };

    // 方法：获取行业趋势（彻底移除token参数）
    const fetchIndustryTrends = async () => {
      try {
        console.log('开始请求行业数据，路径：/api/jobs/industries');
        const response = await axios.get('http://localhost:5000/api/jobs/industries');
        const industries = response.data;
        
        // 生成趋势数据
        industryTrends.value = industries.slice(0, 5).map(industry => ({
          industry,
          description: `${industry}行业人才需求持续增长`,
          growth_rate: `+${Math.floor(Math.random() * 20 + 10)}%`
        }));
      } catch (error) {
        console.error('获取行业趋势失败:', error.message);
        // 强制使用模拟数据
        industryTrends.value = mockIndustryTrends;
      }
    };

    // 方法：初始化行业图表
    const initIndustryChart = () => {
      const ctx = document.getElementById('industryChart');
      if (ctx) {
        const labels = industryTrends.value.map(item => item.industry);
        const growthRates = industryTrends.value.map(item => 
          parseInt(item.growth_rate.replace(/\+|%/g, ''))
        );

        // 销毁旧图表（避免重复初始化）
        if (industryChart.value) {
          industryChart.value.destroy();
        }

        industryChart.value = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: '行业增长率',
              data: growthRates,
              backgroundColor: [
                'rgba(255, 99, 132, 0.7)',
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 206, 86, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(153, 102, 255, 0.7)'
              ],
              borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function(value) {
                    return value + '%';
                  }
                }
              }
            }
          }
        });
      }
    };

    // 方法：处理搜索（调用你的 /api/jobs/search 接口）
    const handleSearch = () => {
      if (!searchKeyword.value.trim()) {
        alert('请输入搜索关键词');
        return;
      }
      // 跳转到搜索结果页并传递参数（不带token）
      router.push({
        path: '/job-search',
        query: {
          keyword: searchKeyword.value
        }
      });
    };

    // 辅助方法：获取岗位标签
    const getJobTags = (job) => {
      const tags = [];
      if (job.company_size) tags.push(job.company_size);
      if (job.industry) tags.push(job.industry);
      return tags;
    };

    // 辅助方法：获取行业图标
    const getIndustryIcon = (industry) => {
      const icons = {
        '人工智能': '🤖',
        '大数据': '📊',
        '云计算': '☁️',
        '新能源': '⚡',
        '生物医药': '💊',
        '互联网': '🌐'
      };
      return icons[industry] || '🏢';
    };

    // 方法：切换用户菜单
    const toggleUserMenu = () => {
      showUserMenu.value = !showUserMenu.value;
    };

    // 方法：退出登录
    const logout = () => {
      isLogin.value = false;
      showUserMenu.value = false;
      // 清空本地存储
      localStorage.removeItem('token');
      router.push('/login');
    };

    // 方法：切换主题
    const toggleTheme = () => {
      theme.value = theme.value === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme.value);
      // 更新按钮图标
      const btn = document.querySelector('.btn-toggle-theme');
      btn.textContent = theme.value === 'light' ? '🌙' : '☀️';
    };

    // 方法：跳转到功能页面
    const goToFeature = (feature) => {
      const routes = {
        '测评': '/career-assessment',
        '分析': '/job-portrait',
        '规划': '/career-planning',
        '导出': '/report-export'
      };
      router.push(routes[feature] || '/');
    };

    // 生命周期：挂载时
    onMounted(async () => {
      // 初始化主题
      document.documentElement.setAttribute('data-theme', theme.value);
      
      // 获取数据（使用Promise.all确保并行请求）
      await Promise.all([
        fetchHotJobs(),
        fetchIndustryTrends()
      ]);
      
      // 初始化图表
      initIndustryChart();

      // 点击外部关闭用户菜单
      document.addEventListener('click', (e) => {
        const profile = document.querySelector('.user-profile');
        if (profile && !profile.contains(e.target)) {
          showUserMenu.value = false;
        }
      });
    });

    // 生命周期：卸载时
    onUnmounted(() => {
      // 销毁图表
      if (industryChart.value) {
        industryChart.value.destroy();
      }
    });

    return {
      isLogin,
      userAvatar,
      showUserMenu,
      searchKeyword,
      hotJobs,
      industryTrends,
      handleSearch,
      getJobTags,
      getIndustryIcon,
      toggleUserMenu,
      logout,
      toggleTheme,
      goToFeature
    };
  }
};
</script>

<style scoped>
/* 基础样式 */
.career-home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color, #f8f9fa);
  color: var(--text-color, #333);
  transition: background-color 0.3s, color 0.3s;
}

/* 顶部导航 */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background-color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  background-color: var(--nav-bg, #ffffff);
}

.nav-wrap {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.nav-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 1.2rem;
  font-weight: bold;
  margin-right: 40px;
}

.logo-icon {
  font-size: 1.5rem;
  margin-right: 8px;
}

.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

.menu-item {
  margin: 0 15px;
  padding: 8px 0;
  cursor: pointer;
  position: relative;
  font-size: 0.95rem;
}

.menu-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #4096ff;
}

.menu-item.dropdown:hover .dropdown-menu {
  display: block;
}

.dropdown-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background-color: white;
  min-width: 200px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  padding: 10px 0;
  z-index: 1001;
  list-style: none;
  margin: 0;
}

.dropdown-item {
  padding: 8px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.dropdown-item:hover {
  background-color: #f5f7fa;
}

.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  display: inline-block;
}

.color-dot.red { background-color: #ff4d4f; }
.color-dot.orange { background-color: #fa8c16; }
.color-dot.green { background-color: #52c41a; }
.color-dot.blue { background-color: #1890ff; }

/* 导航右侧 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* 导航栏搜索框样式 */
.nav-search-wrap {
  display: flex;
  align-items: center;
  background-color: #f5f7fa;
  border-radius: 20px;
  padding: 0 15px;
  height: 36px;
  width: 300px;
}

.nav-search-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.9rem;
  padding: 0 5px;
}

.nav-search-btn {
  border: none;
  background: transparent;
  color: #4096ff;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-toggle-theme {
  border: none;
  background: transparent;
  font-size: 1.2rem;
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.btn-toggle-theme:hover {
  background-color: #f5f7fa;
}

.btn-login, .btn-register {
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-login {
  border: 1px solid #4096ff;
  background-color: transparent;
  color: #4096ff;
}

.btn-login:hover {
  background-color: #e6f7ff;
}

.btn-register {
  border: 1px solid #4096ff;
  background-color: #4096ff;
  color: white;
}

.btn-register:hover {
  background-color: #1890ff;
}

.user-profile {
  position: relative;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  object-fit: cover;
}

.user-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background-color: white;
  min-width: 120px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  padding: 8px 0;
  z-index: 1001;
  list-style: none;
  margin: 0;
}

.user-menu li {
  padding: 8px 16px;
  cursor: pointer;
}

.user-menu li:hover {
  background-color: #f5f7fa;
}

/* 主内容区 */
.home-content {
  flex: 1;
  margin-top: 70px;
  padding-bottom: 60px;
}

/* 英雄区 */
.hero-section {
  position: relative;
  height: 500px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f8fb 100%);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero-title {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 20px;
  line-height: 1.3;
}

.highlight {
  color: #4096ff;
}

.hero-desc {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 40px;
  max-width: 600px;
}

.hero-actions {
  display: flex;
  gap: 20px;
}

.btn-primary, .btn-secondary {
  padding: 12px 30px;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background-color: #4096ff;
  color: white;
}

.btn-primary:hover {
  background-color: #1890ff;
}

.btn-secondary {
  background-color: white;
  color: #4096ff;
  border: 1px solid #4096ff;
}

.btn-secondary:hover {
  background-color: #e6f7ff;
}

/* 通用区块样式 */
.features-section, .hot-jobs-section, .trends-section {
  max-width: 1200px;
  margin: 60px auto;
  padding: 0 20px;
}

.section-header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
}

.hot-jobs-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-align: left;
}

.section-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.section-desc {
  color: #666;
  font-size: 1rem;
}

.btn-more {
  padding: 8px 16px;
  border: 1px solid #4096ff;
  color: #4096ff;
  background-color: transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-more:hover {
  background-color: #e6f7ff;
}

/* 功能区块 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
}

.feature-card {
  background-color: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.feature-title {
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.feature-desc {
  color: #666;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* 热门岗位 */
.jobs-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.job-card {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: box-shadow 0.3s;
}

.job-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.job-name {
  font-size: 1.1rem;
  font-weight: bold;
}

.salary-range {
  color: #ff7a45;
  font-weight: bold;
}

.job-info {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  font-size: 0.9rem;
  color: #666;
}

.job-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  font-size: 0.8rem;
  padding: 4px 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

/* 行业趋势 */
.trends-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.chart-container {
  height: 300px;
}

.trends-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.trend-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.trend-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  border-radius: 50%;
}

.trend-info {
  flex: 1;
}

.industry-name {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 8px;
}

.trend-desc {
  color: #666;
  font-size: 0.95rem;
  margin-bottom: 8px;
}

.growth-rate {
  color: #52c41a;
  font-weight: bold;
  font-size: 0.9rem;
}

/* 页脚 */
.home-footer {
  background-color: #f5f7fa;
  padding: 40px 0;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-logo {
  margin-bottom: 10px;
}

.copyright {
  color: #999;
  font-size: 0.9rem;
}

.footer-links {
  display: flex;
  list-style: none;
  gap: 20px;
  margin: 0;
  padding: 0;
}

.footer-links a {
  color: #666;
  text-decoration: none;
  font-size: 0.9rem;
}

.footer-links a:hover {
  color: #4096ff;
}

/* 暗黑模式样式 */
[data-theme="dark"] {
  --bg-color: #141414;
  --text-color: #e5e5e5;
  --nav-bg: #1f1f1f;
}

[data-theme="dark"] .feature-card,
[data-theme="dark"] .job-card,
[data-theme="dark"] .trend-item,
[data-theme="dark"] .dropdown-menu,
[data-theme="dark"] .user-menu {
  background-color: #262626;
  color: #e5e5e5;
}

[data-theme="dark"] .nav-search-wrap,
[data-theme="dark"] .btn-toggle-theme:hover,
[data-theme="dark"] .dropdown-item:hover,
[data-theme="dark"] .user-menu li:hover {
  background-color: #333;
}

[data-theme="dark"] .tag {
  background-color: #333;
  color: #e5e5e5;
}

/* 响应式样式 */
@media (max-width: 992px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .jobs-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .trends-content {
    grid-template-columns: 1fr;
  }
  .hero-title {
    font-size: 2.5rem;
  }
}

@media (max-width: 768px) {
  .nav-menu {
    display: none;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }
  .jobs-grid {
    grid-template-columns: 1fr;
  }
  .hero-title {
    font-size: 2rem;
  }
  .nav-search-wrap {
    width: 200px;
  }
}

@media (max-width: 576px) {
  .hero-section {
    height: 400px;
  }
  .hero-title {
    font-size: 1.8rem;
  }
  .hero-actions {
    flex-direction: column;
    gap: 10px;
  }
  .nav-search-wrap {
    width: 150px;
  }
}
</style>