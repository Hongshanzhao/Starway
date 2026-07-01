import { createRouter, createWebHistory } from 'vue-router'
import { authState } from '@/utils/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/PublicLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
      { path: 'jobs/search', name: 'jobs-search', component: () => import('@/views/jobs/JobsSearch.vue') },
      { path: 'jobs/:jobId', name: 'job-detail', component: () => import('@/views/jobs/JobDetail.vue') },
      { path: 'jobs/:jobId/profile', name: 'job-profile', component: () => import('@/views/jobs/JobProfile.vue') },
      { path: 'jobs/:jobId/similar', name: 'job-similar', component: () => import('@/views/jobs/SimilarJobs.vue') },
      { path: 'jobs/path/:jobName', name: 'job-path', component: () => import('@/views/jobs/JobPath.vue') },
      { path: 'assistant/chat', name: 'assistant-chat', component: () => import('@/views/assistant/AssistantChat.vue'), meta: { requiresAuth: true } },
      { path: 'profile/create', name: 'profile-create', component: () => import('@/views/profile/ProfileCreate.vue'), meta: { requiresAuth: true } },
      { path: 'profile/upload', name: 'profile-upload', component: () => import('@/views/profile/ProfileCreate.vue'), meta: { requiresAuth: true, uploadOnly: true } },
      { path: 'profile/:studentId', name: 'profile-detail', component: () => import('@/views/profile/ProfileDetail.vue'), meta: { requiresAuth: true } },
      { path: 'assessment', name: 'assessment-center', component: () => import('@/views/assessment/AssessmentCenter.vue'), meta: { requiresAuth: true } },
      { path: 'assessment/start', name: 'assessment-start', component: () => import('@/views/assessment/AssessmentStart.vue'), meta: { requiresAuth: true } },
      { path: 'assessment/result/:resultId', name: 'assessment-result', component: () => import('@/views/assessment/AssessmentResult.vue'), meta: { requiresAuth: true } },
      { path: 'match/recommend', name: 'match-recommend', component: () => import('@/views/match/MatchRecommend.vue'), meta: { requiresAuth: true } },
      { path: 'match/stream', name: 'match-stream', component: () => import('@/views/match/MatchStream.vue'), meta: { requiresAuth: true } },
      { path: 'match/history', name: 'match-history', component: () => import('@/views/match/MatchHistory.vue'), meta: { requiresAuth: true } },
      { path: 'report/generate', name: 'report-generate', component: () => import('@/views/report/ReportGenerate.vue'), meta: { requiresAuth: true } },
      { path: 'report/export', name: 'report-export', component: () => import('@/views/report/ReportExport.vue'), meta: { requiresAuth: true } },
      { path: 'report/:reportId', name: 'report-detail', component: () => import('@/views/report/ReportDetail.vue'), meta: { requiresAuth: true } },
    ],
  },
  {
    path: '/auth',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      { path: 'login', name: 'login', component: () => import('@/views/auth/LoginView.vue') },
      { path: 'register', name: 'register', component: () => import('@/views/auth/RegisterView.vue') },
    ],
  },
  {
    path: '/user',
    component: () => import('@/layouts/UserLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/user/profile' },
      { path: 'profile', name: 'user-profile', component: () => import('@/views/user/UserProfile.vue') },
      { path: 'plans', name: 'user-plans', component: () => import('@/views/user/UserReports.vue'), meta: { reportKind: 'plans' } },
      { path: 'interests', name: 'user-interests', component: () => import('@/views/user/UserReports.vue'), meta: { reportKind: 'interests' } },
      { path: 'matches', name: 'user-matches', component: () => import('@/views/user/UserReports.vue'), meta: { reportKind: 'matches' } },
      { path: 'history', name: 'user-history', component: () => import('@/views/user/UserHistory.vue') },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/admin/AdminDashboard.vue') },
      { path: 'users', name: 'admin-users', component: () => import('@/views/admin/AdminUsers.vue') },
      { path: 'jobs', name: 'admin-jobs', component: () => import('@/views/admin/AdminJobs.vue') },
      { path: 'reports', name: 'admin-reports', component: () => import('@/views/admin/AdminReports.vue') },
      { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/AdminCategories.vue') },
      { path: 'graph', name: 'admin-graph', component: () => import('@/views/admin/AdminGraph.vue') },
      { path: 'ai-tools', name: 'admin-ai-tools', component: () => import('@/views/admin/AdminAiTools.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !authState.user) {
    return { path: '/auth/login', query: { redirect: to.fullPath } }
  }
  if (authState.user?.role === 'admin' && !to.path.startsWith('/admin') && !to.path.startsWith('/auth')) {
    return '/admin/dashboard'
  }
  if (to.meta.requiresAdmin && authState.user?.role !== 'admin') {
    return '/'
  }
  return true
})

export default router
