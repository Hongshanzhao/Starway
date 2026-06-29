# Starway 后端接口文档

Base URL: `http://127.0.0.1:5000`

## 通用约定

认证头：

```http
Authorization: Bearer mock-token-{user_id}
```

SSE 响应：

```text
data: {"type":"start"}

data: {"type":"done"}
```

## 系统

### `GET /`

响应：

```json
{"message": "Starway backend is running", "database": "SQLite"}
```

### `GET /test-db`

响应：

```json
{"status": "ok", "message": "database connected"}
```

### `GET /uploads/avatars/{filename}`

返回头像图片文件。

## 认证

### `GET /api/captcha`

返回 `image/png` 图形验证码，并写入 session。

### `POST /api/send_code`

短信验证码已停用。

响应：

```json
{"error": "sms verification is disabled"}
```

状态码：`410`

### `POST /api/register`

请求：

```json
{
  "username": "student01",
  "phone": "13900000000",
  "password": "pass123",
  "captcha": "ABCD"
}
```

响应：

```json
{"id": 1, "username": "student01"}
```

### `POST /api/login`

请求：

```json
{
  "username": "student01",
  "password": "pass123",
  "captcha": "ABCD"
}
```

响应：

```json
{
  "token": "mock-token-1",
  "user": {"id": 1, "username": "student01", "role": "user"}
}
```

## 用户中心

### `GET /api/user`

响应：

```json
{
  "id": 1,
  "username": "student01",
  "phone": "13900000000",
  "role": "user",
  "is_active": 1,
  "avatar": "",
  "created_at": "2026-06-29 10:00:00"
}
```

### `GET /api/user/profile`

返回用户基础信息和最近一条学生画像。

### `PUT /api/user/profile`

请求：

```json
{
  "name": "张三",
  "email": "student@example.com",
  "education_text": "本科 计算机科学",
  "skills_certs_text": "Python, SQL, CET-6"
}
```

响应：

```json
{"status": "ok"}
```

### `POST /api/user/avatar`

表单上传字段：`file`

响应：

```json
{"avatar": "/uploads/avatars/example.png"}
```

### `POST /api/user/change-password`

请求：

```json
{"oldPwd": "pass123", "newPwd": "pass456"}
```

响应：

```json
{"status": "ok"}
```

### `POST /api/user/bind-phone`

请求：

```json
{"phone": "13900000001"}
```

响应：

```json
{"status": "ok"}
```

### `GET /api/user/plans`

返回当前用户职业规划报告列表。

### `GET /api/user/interest-reports`

返回兴趣测评报告列表。

### `GET /api/user/match-reports`

返回人岗匹配报告列表。

### `GET /api/user/history`

返回浏览历史列表。

### `POST /api/user/history`

请求：

```json
{"title": "Python 后端", "desc": "岗位详情", "type": "job", "itemId": 1}
```

响应：

```json
{"status": "added"}
```

### `DELETE /api/user/history/{history_id}`

响应：

```json
{"status": "deleted"}
```

### `DELETE /api/user/history/clear`

响应：

```json
{"status": "cleared"}
```

### `GET /api/user/stats`

响应：

```json
{"assessmentCount": 2, "planCount": 3}
```

### `GET /api/user/reports`

返回当前用户所有报告聚合列表。

### `DELETE /api/user/report/career/{report_id}`

删除职业规划报告。

### `DELETE /api/user/report/interest/{result_id}`

删除兴趣测评报告。

### `DELETE /api/user/report/match/{match_id}`

删除匹配报告。

## 岗位

### `GET /api/jobs/search`

查询参数：`page`、`size`、`keyword`、`industry`、`company_size`、`order`

响应：

```json
{
  "total": 100,
  "page": 1,
  "size": 10,
  "items": [
    {
      "id": 1,
      "job_name": "Python 后端工程师",
      "location": "杭州",
      "salary_range": "10000-18000",
      "company": "Starway",
      "industry": "技术"
    }
  ]
}
```

### `GET /api/jobs/simple_search`

返回简化岗位列表。

### `GET /api/jobs/categories`

从 `jobs.job_category` 聚合返回岗位类别。

### `GET /api/jobs/industries`

返回 `job.industry` 去重列表。

### `GET /api/jobs/names`

返回岗位名称列表。

### `GET /api/jobs/{job_id}`

返回岗位详情。

### `GET /api/jobs/{job_id}/profile`

返回岗位画像，优先缓存，没有缓存时本地生成。

### `GET /api/jobs/{job_id}/similar`

返回职业规划导向的相邻岗位方向。默认会按岗位名称去重，并排除同名招聘，避免把“相似岗位”变成同一岗位的重复招聘列表。

查询参数：

- `top_k`：返回数量，默认 `10`
- `include_same_title`：是否包含同名岗位招聘样本，默认 `false`；设为 `true` 时同名岗位的 `relation_type` 为 `same_role_posting`

响应：

```json
{
  "success": true,
  "model_source": "word2vec",
  "include_same_title": false,
  "data": [
    {
      "job_id": 2,
      "job_code": "JOB00002",
      "job_name": "后端开发工程师",
      "company": "星途科技",
      "job_category": "技术",
      "industry": "技术",
      "salary_range": "12000-20000",
      "location": "杭州",
      "skills": "Java,Spring,Redis",
      "similarity": 0.9123,
      "relation_type": "adjacent_role",
      "required_skills": ["API", "Java", "MySQL", "Redis", "Spring"],
      "matched_skills": ["API", "Java", "Redis", "Spring"],
      "missing_skills": ["MySQL"],
      "why_similar": "为什么推荐：后端开发工程师与Java开发工程师处在相邻职业方向，能力迁移路径比较清晰。可迁移能力包括API、Java、Redis、Spring。建议补充MySQL。排序同时参考了 Word2Vec 岗位向量相似度。"
    }
  ]
}
```

`model_source` 为 `word2vec` 时表示使用岗位向量文件参与排序；为 `rules` 时表示模型不可用并回退到本地规则。两种模式都会返回可直接展示的岗位字段、技能迁移解释和技能缺口。

### `GET /api/jobs/profile/{job_name}`

按岗位名返回岗位详情。

### `GET /api/jobs/{job_name}/full-path`

返回纵向和横向职业路径。

响应包含 `model_source`，优先为 `word2vec`，模型不可用时为 `rules`。

### `GET /api/jobs/{job_name}/vertical`

返回纵向路径。

### `GET /api/jobs/{job_name}/lateral`

返回横向路径。

### `GET /api/jobs/graph`

返回岗位关系图谱节点和边。

### `POST /api/jobs/skills`

请求：

```json
{"job_description": "Python Flask SQL backend API", "top_k": 3}
```

响应：

```json
{
  "success": true,
  "model_source": "textcnn",
  "data": [{"skill": "Python", "probability": 0.93}]
}
```

`model_source` 为 `textcnn` 时表示使用 TextCNN 技能预测模型；为 `rules` 时表示回退到本地技能词抽取。

## 学生画像

### `POST /api/profile/submit`

请求：

```json
{
  "user_id": 1,
  "name": "张三",
  "major": "计算机科学",
  "grade": "大四",
  "education": "本科",
  "work": "后端实习",
  "project": "校园职业规划系统",
  "skills_certs": "Python, SQL, CET-6",
  "summary": "希望从事后端开发"
}
```

响应：

```json
{
  "student_id": 1,
  "skills": ["Python", "SQL"],
  "certificates": ["CET-6"],
  "soft_abilities": {}
}
```

### `POST /api/profile/upload`

表单上传字段：`file`

响应包含解析文本、技能、证书、教育、经历和项目。

### `GET /api/profile/{student_id}`

返回学生画像详情。

## 兴趣测评

### `GET /api/assessment/questions`

返回测评题目列表。

### `POST /api/assessment/submit`

请求：

```json
{
  "user_id": 1,
  "session_id": "web",
  "answers": [{"question_id": 1, "score": 4}]
}
```

响应：

```json
{
  "success": true,
  "result_id": 1,
  "dimension_scores": {"R": 4},
  "recommendation": "..."
}
```

### `GET /api/assessment/history/{user_id}`

返回最近 10 条测评历史。

## 人岗匹配

### `GET /api/match/recommend`

查询参数：`student_id`、`limit`

响应：

```json
{"results": [{"job_name": "Python 后端", "overall_score": 82.5}], "total": 50}
```

### `POST /api/match/match`

请求：

```json
{"student_id": 1, "job_name": "Python 后端工程师"}
```

响应包含 `overall_score`、`skill_fit`、`cert_coverage`、`gap_analysis`。

### `POST /api/match/match-stream`

SSE 响应：

```text
data: {"type":"base","data":{"overall_score":82.5}}

data: {"type":"gap","field":"skills","text":"建议补齐 Flask"}

data: {"type":"done"}
```

### `GET /api/match/history/{student_id}`

返回匹配历史。

## 职业报告

### `POST /api/report/generate`

请求：

```json
{"student_id": 1, "job_name": "Python 后端工程师"}
```

响应：

```json
{"report_id": 1, "job_name": "Python 后端工程师", "content": "# 职业生涯发展报告"}
```

### `POST /api/report/generate-stream`

SSE 响应：

```text
data: {"chunk":"# 职业生涯发展报告"}

data: {"done":true,"report_id":1}
```

### `GET /api/report/history/{student_id}`

返回报告历史。

### `GET /api/report/{report_id}`

返回报告详情。

### `PUT /api/report/{report_id}`

请求：

```json
{"content": "# 更新后的报告"}
```

响应：

```json
{"status": "ok"}
```

### `POST /api/report/polish`

请求：

```json
{"content": "需要润色的报告"}
```

响应：

```json
{"content": "润色后的报告"}
```

### `POST /api/report/export`

请求：

```json
{"markdown": "# 报告"}
```

返回 `text/markdown` 下载文件。

## AI

### `POST /api/assistant/chat`

请求：

```json
{
  "message": "我想做 Python 后端，怎么准备？",
  "context": {"skills": ["Python", "SQL"]},
  "provider": "auto",
  "stream": false
}
```

响应：

```json
{"answer": "...", "provider": "local", "usage": {"fallback": true}}
```

流式请求将返回 SSE：`start`、`delta`、`done`。

### `POST /api/llm/qa`

兼容问答接口。

### `POST /api/llm/generate_plan`

需要登录，返回职业规划建议。

### `POST /api/llm/recommend`

需要登录，返回 ML 推荐结果。

### `GET /api/llm/test_connection`

查询参数：`provider=local|zhipu|deepseek`

响应：

```json
{"status": "ok", "provider": "local", "message": "Local fallback available", "response": "..."}
```

## 管理后台

### `POST /api/admin/login`

管理员登录，返回 token 和用户信息。

### `GET /api/admin/users`

返回用户列表。

### `GET /api/admin/users/{user_id}`

返回用户详情。

### `PUT /api/admin/users/{user_id}`

更新用户字段：`username`、`phone`、`role`、`is_active`。

### `DELETE /api/admin/users/{user_id}`

删除用户。

### `GET /api/admin/categories`

从 `jobs.job_category` 聚合岗位分类。

### `POST /api/admin/categories`

固定返回 400，分类来自天池数据，不手工维护。

### `DELETE /api/admin/categories/{cid}`

固定返回 400，分类来自天池数据，不手工删除。

### `GET /api/admin/category-summary`

从 `jobs.job_category` 返回分类统计。

响应：
```json
{
  "source": "jobs.job_category",
  "total_categories": 2,
  "categories": [{"id": 1, "name": "技术", "job_count": 120}]
}
```

### `GET /api/admin/jobs`

返回岗位列表。

### `POST /api/admin/jobs`

新增岗位。

### `PUT /api/admin/jobs/{jid}`

更新岗位。

### `DELETE /api/admin/jobs/{jid}`

删除岗位。

### `POST /api/admin/build-job-graph`

重建岗位关系图谱。

### `GET /api/admin/reports`

分页返回报告列表。

### `GET /api/admin/reports/{report_id}`

返回报告详情。

### `DELETE /api/admin/reports/{report_id}`

删除报告。

### `GET /api/admin/users/{user_id}/reports`

返回指定用户报告。

## 内容

### `GET /api/contents`

查询参数：`page`、`size`、`category`、`sort_by`、`order`

响应：

```json
{"total": 0, "page": 1, "size": 8, "data": []}
```
