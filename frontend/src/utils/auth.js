import { reactive, computed } from 'vue'
import { clearAuth, getStoredUser, getToken, setAuth } from '@/api/http'

export const authState = reactive({
  token: getToken(),
  user: getStoredUser(),
})

export const isLoggedIn = computed(() => Boolean(authState.token && authState.user))

export function loginWith(token, user) {
  setAuth(token, user)
  authState.token = token
  authState.user = user
}

export function logout() {
  clearAuth()
  authState.token = ''
  authState.user = null
}

export function currentUserId() {
  return authState.user?.id || null
}

export function currentStudentId(profile) {
  return profile?.student_id || profile?.studentId || null
}
