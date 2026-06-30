import { http } from './http'

export const authApi = {
  captchaUrl: (captchaId) => `http://127.0.0.1:5000/api/captcha?captcha_id=${encodeURIComponent(captchaId)}&t=${Date.now()}`,
  login: (data) => http.post('/api/login', data),
  register: (data) => http.post('/api/register', data),
  adminLogin: (data) => http.post('/api/admin/login', data),
  me: () => http.get('/api/user'),
}

export const userApi = {
  profile: () => http.get('/api/user/profile'),
  updateProfile: (data) => http.put('/api/user/profile', data),
  uploadAvatar: (data) => http.post('/api/user/avatar', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  changePassword: (data) => http.post('/api/user/change-password', data),
  bindPhone: (data) => http.post('/api/user/bind-phone', data),
  plans: () => http.get('/api/user/plans'),
  interests: () => http.get('/api/user/interest-reports'),
  matches: () => http.get('/api/user/match-reports'),
  history: () => http.get('/api/user/history'),
  addHistory: (data) => http.post('/api/user/history', data),
  deleteHistory: (id) => http.delete(`/api/user/history/${id}`),
  clearHistory: () => http.delete('/api/user/history/clear'),
  stats: () => http.get('/api/user/stats'),
  reports: () => http.get('/api/user/reports'),
}

export const profileApi = {
  submit: (data) => http.post('/api/profile/submit', data),
  upload: (data) => http.post('/api/profile/upload', data, { headers: { 'Content-Type': 'multipart/form-data' }, silent: true }),
  detail: (id) => http.get(`/api/profile/${id}`),
}

export const jobsApi = {
  search: (params) => http.get('/api/jobs/search', { params }),
  simpleSearch: (params) => http.get('/api/jobs/simple_search', { params }),
  categories: () => http.get('/api/jobs/categories'),
  industries: () => http.get('/api/jobs/industries'),
  names: () => http.get('/api/jobs/names'),
  detail: (id) => http.get(`/api/jobs/${id}`),
  profile: (id) => http.get(`/api/jobs/${id}/profile`),
  profileAi: (id) => http.get(`/api/jobs/${id}/profile-ai`),
  similar: (id, params) => http.get(`/api/jobs/${id}/similar`, { params }),
  path: (jobName, params) => http.get(`/api/jobs/${encodeURIComponent(jobName)}/full-path`, { params }),
  pathAi: (jobName, params) => http.get(`/api/jobs/${encodeURIComponent(jobName)}/full-path-ai`, { params }),
  graph: () => http.get('/api/jobs/graph'),
  skills: (data) => http.post('/api/jobs/skills', data),
}

export const assessmentApi = {
  questions: () => http.get('/api/assessment/questions'),
  submit: (data) => http.post('/api/assessment/submit', data),
  history: (userId) => http.get(`/api/assessment/history/${userId}`),
}

export const matchApi = {
  recommend: (params) => http.get('/api/match/recommend', { params }),
  match: (data) => http.post('/api/match/match', data),
  history: (studentId) => http.get(`/api/match/history/${studentId}`),
}

export const reportApi = {
  generate: (data) => http.post('/api/report/generate', data),
  history: (studentId) => http.get(`/api/report/history/${studentId}`),
  detail: (id) => http.get(`/api/report/${id}`),
  insights: (id) => http.get(`/api/report/${id}/insights`),
  update: (id, data) => http.put(`/api/report/${id}`, data),
  polish: (data) => http.post('/api/report/polish', data),
  exportMarkdown: (data) => http.post('/api/report/export', data, { responseType: 'blob' }),
}

export const assistantApi = {
  chat: (data) => http.post('/api/assistant/chat', data),
}

export const adminApi = {
  dashboard: () => http.get('/api/admin/dashboard'),
  users: () => http.get('/api/admin/users'),
  updateUser: (id, data) => http.put(`/api/admin/users/${id}`, data),
  deleteUser: (id) => http.delete(`/api/admin/users/${id}`),
  jobs: () => http.get('/api/admin/jobs'),
  addJob: (data) => http.post('/api/admin/jobs', data),
  updateJob: (id, data) => http.put(`/api/admin/jobs/${id}`, data),
  deleteJob: (id) => http.delete(`/api/admin/jobs/${id}`),
  reports: (params) => http.get('/api/admin/reports', { params }),
  reportDetail: (id) => http.get(`/api/admin/reports/${id}`),
  deleteReport: (id) => http.delete(`/api/admin/reports/${id}`),
  categories: () => http.get('/api/admin/category-summary'),
  buildGraph: () => http.post('/api/admin/build-job-graph', {}),
  graphOverview: () => http.get('/api/admin/graph/overview'),
  aiToolsOverview: () => http.get('/api/admin/ai-tools/overview'),
}
