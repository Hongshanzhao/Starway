import { createRouter, createWebHistory } from 'vue-router'
import html2pdf from 'html2pdf.js'
import { ArrowRight, ArrowLeft } from '@element-plus/icons-vue'

// 导入所有页面组件
import Home from '../views/Home.vue'
// 新增：导入职业规划引导页组件
import CareerPlanningIntro from '../views/CareerPlanningIntro.vue'
import StudentAbility from '../views/StudentAbility.vue'
// 🔥 改动1：注释/删除原有MatchResult，导入新的JobMatchAnalysis
import MatchResult from '../views/MatchResult.vue'
import JobMatchAnalysis from '../views/JobMatchAnalysis.vue' // 新增：导入人岗匹配分析页
import Report from '../views/Report.vue'
import JobPortrait from '../views/JobPortrait.vue'

// 新增：导入登录、注册组件
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminLogin from '../views/AdminLogin.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

// 新增：导入个人中心组件（核心添加）
import ProfilePage from '../views/ProfilePage.vue'

// 新增：导入其他功能页面组件（未创建的组件先用Home占位）
import CareerPlanning from '../views/CareerPlanning.vue'
import AbilityAssessment from '../views/AbilityAssessment.vue'
import ReportGenerate from '../views/ReportGenerate.vue'
import ResourceLibrary from '../views/ResourceLibrary.vue'
import AboutUs from '../views/AboutUs.vue'
import CareerInterestTest from '../views/CareerInterestTest.vue'
import ResumeUpload from '../views/ResumeUpload.vue'

// 新增：导入岗位详情组件
import JobDetail from '../views/JobDetail.vue'

// 临时占位组件
const PostgraduatePlanning = () => import('../views/Home.vue') 
const StudyAbroadPlanning = () => import('../views/Home.vue') 
const CivilServicePlanning = () => import('../views/Home.vue') 
const EntrepreneurshipPlanning = () => import('../views/Home.vue') 
const InterestAssessment = () => import('../views/Home.vue') 
import AbilityAnalysis from '../views/AbilityAnalysis.vue'
import DevelopmentPath from '../views/DevelopmentPath.vue'
import ReportExport from '../views/ReportExport.vue'
const Search = () => import('../views/Home.vue') 

const routes = [
  { 
    path: '/', 
    name: 'Home',
    component: Home 
  },
  // 新增：职业规划引导页路由（核心添加）
  { 
    path: '/career-planning-intro', 
    name: 'CareerPlanningIntro',
    component: CareerPlanningIntro,
    meta: {
      title: 'AI智能职业规划系统 - 规划流程' // 可选：页面标题
    }
  },
  // 新增：登录页路由
  { 
    path: '/login', 
    name: 'Login',
    component: Login 
  },
  {
    path: '/admin-login',
    name: 'AdminLogin',
    component: AdminLogin
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard
  },
  // 新增：注册页路由
  { 
    path: '/register', 
    name: 'Register',
    component: Register 
  },
  // 新增：个人中心路由（核心添加）
  { 
    path: '/profile', 
    name: 'ProfilePage',
    component: ProfilePage,
    // 可选：添加路由元信息，标记需要登录才能访问
    meta: { 
      requireAuth: true 
    }
  },
  // 原有功能页面路由
  {
     path: '/student-ability', 
     name: 'StudentAbility', 
     component: StudentAbility 
  },
  { 
    path: '/match-result', 
    name: 'MatchResult',
    component: MatchResult 
  },
  { 
    path: '/jobmatch-analysis', // 保留原有路径，保证导航栏跳转不失效
    name: 'JobMatchAnalysis', // 新的路由名称
    component: JobMatchAnalysis, // 新的组件
  },
  // // 🔥 可选：新增职业探索专属路由（方便直接访问）
  // { 
  //   path: '/career-exploration', 
  //   name: 'CareerExploration',
  //   component: JobMatchAnalysis, // 复用同一个组件
  //   meta: {
  //     title: '大学生职业规划系统 - 职业探索'
  //   }
  // },
  { 
    path: '/report', 
    name: 'Report',
    component: Report 
  },
  { 
    path: '/job-portrait', 
    name: 'JobPortrait',
    component: JobPortrait 
  },
  // 新增：岗位详情页路由（核心修改）
  { 
    path: '/job-detail', 
    name: 'JobDetail',
    component: JobDetail,
    // 接收URL参数
    props: (route) => ({ 
      id: route.query.id 
    })
  },
  // 新增：顶部导航菜单路由
  { 
    path: '/career-planning', 
    name: 'CareerPlanning',
    component: CareerPlanning 
  },
  { path: '/resume-upload', component: ResumeUpload },
  { 
    path: '/ability-assessment', 
    name: 'AbilityAssessment',
    component: AbilityAssessment 
  },
  { 
    path: '/report-generate', 
    name: 'ReportGenerate',
    component: ReportGenerate 
  },
  { 
    path: '/resource-library', 
    name: 'ResourceLibrary',
    component: ResourceLibrary 
  },
  { 
    path: '/about-us', 
    name: 'AboutUs',
    component: AboutUs 
  },
  {
    path: '/interest-test',
    name: 'CareerInterestTest',
    component:CareerInterestTest
  },
  // 新增：核心分类入口路由
  { 
    path: '/postgraduate-planning', 
    name: 'PostgraduatePlanning',
    component: PostgraduatePlanning 
  },
  { 
    path: '/study-abroad-planning', 
    name: 'StudyAbroadPlanning',
    component: StudyAbroadPlanning 
  },
  { 
    path: '/civil-service-planning', 
    name: 'CivilServicePlanning',
    component: CivilServicePlanning 
  },
  { 
    path: '/entrepreneurship-planning', 
    name: 'EntrepreneurshipPlanning',
    component: EntrepreneurshipPlanning 
  },
  // 新增：核心功能下拉菜单路由
  { 
    path: '/interest-assessment', 
    name: 'InterestAssessment',
    component: InterestAssessment 
  },
  { 
    path: '/ability-analysis', 
    name: 'AbilityAnalysis',
    component: AbilityAnalysis 
  },
  { 
    path: '/development-path', 
    name: 'DevelopmentPath',
    component: DevelopmentPath 
  },
  { 
    path: '/report-export', 
    name: 'ReportExport',
    component: ReportExport 
  },
  // 新增：搜索和详情页路由
  { 
    path: '/search', 
    name: 'Search',
    component: Search 
  },
  // 保留原有detail路由作为兼容（可选）
  { 
    path: '/detail/:id', 
    name: 'Detail',
    component: JobDetail,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 可选：添加路由守卫（如需登录后才能访问其他页面，可取消注释）
router.beforeEach((to, from, next) => {
  // 排除登录、注册、首页、职业规划引导页（可根据需求调整）
  // 🔥 改动3：把新的人岗匹配/职业探索页面加入白名单（或根据需求调整）
  const whiteList = ['/login', '/register', '/', '/job-detail', '/career-planning-intro', '/match-result', '/career-exploration']
  // 从localStorage获取token（登录成功后存储）
  const hasToken = localStorage.getItem('token')
  
  // 如果路由需要认证且不在白名单，检查token
  if (to.meta.requireAuth && !whiteList.includes(to.path)) {
    hasToken ? next() : next('/login')
  } else {
    // 设置页面标题
    if (to.meta.title) {
      document.title = to.meta.title
    }
    next()
  }
})

export default router