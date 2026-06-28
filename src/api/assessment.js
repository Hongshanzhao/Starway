// 职业兴趣测评 API 调用

const BASE_URL = 'http://127.0.0.1:5000/api/assessment'

// 获取题目
export async function getQuestions() {
  const res = await fetch(`${BASE_URL}/questions`)
  return res.json()
}

// 提交答案（可切换测试/正式模式）
export async function submitAssessment(answers, userId = 1, testMode = false) {
  const res = await fetch(`${BASE_URL}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      answers,
      user_id: userId,
      session_id: `session_${Date.now()}`,
      test_mode: testMode  // 正式使用时设为 false
    })
  })
  return res.json()
}

// 获取历史记录
export async function getHistory(userId) {
  const res = await fetch(`${BASE_URL}/history/${userId}`)
  return res.json()
}