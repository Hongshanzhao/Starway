export function listify(value) {
  if (!value) return []
  if (Array.isArray(value)) return value
  if (value instanceof Set) return Array.from(value)
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      if (Array.isArray(parsed)) return parsed
    } catch {
      return value.split(/[,，、;\s]+/).filter(Boolean)
    }
  }
  return []
}

export function compactText(value, fallback = '') {
  if (value == null) return fallback
  if (typeof value === 'string') return value.trim()
  if (Array.isArray(value)) {
    return value.map((item) => compactText(item)).filter(Boolean).join('\n')
  }
  if (typeof value === 'object') {
    return Object.entries(value)
      .filter(([, val]) => val !== undefined && val !== null && String(val).trim() !== '')
      .map(([key, val]) => `${labelOfKey(key)}：${compactText(val)}`)
      .join('\n')
  }
  return String(value)
}

export function formatEducation(value, fallback = '') {
  if (!value) return fallback
  if (typeof value === 'string') {
    try {
      return formatEducation(JSON.parse(value), value)
    } catch {
      return value.trim()
    }
  }
  if (Array.isArray(value)) return value.map((item) => formatEducation(item)).filter(Boolean).join('\n')
  const parts = [
    value.school,
    value.major,
    value.degree,
    value.grade,
  ].map((item) => String(item || '').trim()).filter(Boolean)
  return parts.join(' · ') || compactText(value, fallback)
}

export function formatExperience(value, fallback = '') {
  if (!value) return fallback
  if (typeof value === 'string') {
    try {
      return formatExperience(JSON.parse(value), value)
    } catch {
      return value.trim()
    }
  }
  const rows = Array.isArray(value) ? value : [value]
  return rows.map((item) => {
    if (!item || typeof item !== 'object') return compactText(item)
    const title = item.company || item.project_name || item.name || item.title || ''
    const role = item.position || item.role || ''
    const description = item.description || item.desc || ''
    return [title, role, description].map((part) => String(part || '').trim()).filter(Boolean).join('：')
  }).filter(Boolean).join('\n')
}

export function plainTextFromMarkdown(value) {
  return String(value || '')
    .replace(/\r\n/g, '\n')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*\n]+)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '· ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

export function softAbilityRows(value) {
  if (!value || typeof value !== 'object') return []
  return Object.entries(value).map(([name, raw]) => ({
    name,
    score: Number(raw?.score ?? raw ?? 0),
    description: raw?.description || '',
  }))
}

function labelOfKey(key) {
  const labels = {
    degree: '学历',
    grade: '年级',
    major: '专业',
    school: '学校',
    company: '单位',
    position: '岗位',
    project_name: '项目',
    role: '角色',
    description: '说明',
  }
  return labels[key] || key
}

export function formatTime(value) {
  if (!value) return '-'
  if (typeof value === 'number') return new Date(value * 1000).toLocaleString()
  return String(value)
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
