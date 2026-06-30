import axios from 'axios'
import { ElMessage } from 'element-plus'

export const API_BASE_URL = 'http://127.0.0.1:5000'

const TOKEN_KEY = 'starway_token'
const USER_KEY = 'starway_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user || null))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error?.response?.data?.error || error?.message || '请求失败，请稍后重试'
    if (!error.config?.silent) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  },
)

export async function streamRequest(path, body, onEvent, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      ...(options.headers || {}),
    },
    credentials: 'include',
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok || !response.body) {
    let message = '流式请求失败'
    try {
      const data = await response.json()
      message = data.error || message
    } catch {
      message = response.statusText || message
    }
    throw new Error(message)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  function emitBlock(block) {
    if (!block.trim()) return
    const event = {}
    const data = []
    for (const rawLine of block.split(/\r?\n/)) {
      const line = rawLine.trim()
      if (!line || line.startsWith(':')) continue
      if (line.startsWith('event:')) {
        event.event = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        data.push(line.slice(5).trim())
      }
    }
    for (const item of data) {
      if (!item || item === '[DONE]') continue
      try {
        const parsed = JSON.parse(item)
        onEvent(event.event && !parsed.type ? { type: event.event, ...parsed } : parsed)
      } catch {
        onEvent({ type: event.event || 'delta', chunk: item, content: item })
      }
    }
  }

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = blocks.pop() || ''
    blocks.forEach(emitBlock)
  }
  buffer += decoder.decode()
  if (buffer.trim()) {
    emitBlock(buffer)
  }
}
