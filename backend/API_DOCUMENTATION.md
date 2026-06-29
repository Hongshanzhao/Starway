# Starway Backend API Documentation

Base URL: `http://127.0.0.1:5000`

## Environment

```bash
DEEPSEEK_API_KEY=sk-...
ZHIPU_API_KEY=...
LLM_PROVIDER=auto       # local | auto | zhipu | deepseek
SQLITE_DB_PATH=backend/instance/career.db
```

Aliyun/DashScope is no longer required. Existing API paths are kept.

## Data Import

Import Tianchi `jobs.csv`, `candidates.csv`, and `applications.csv`:

```bash
python backend/scripts/import_tianchi_data.py --data-dir D:\caogao6\岗位数据 --reset
```

Imported tables:

- `jobs`: job postings from Tianchi.
- `candidates`: Tianchi candidate capability records used for model training.
- `applications`: Tianchi historical matching records used for algorithm evaluation.
- `job`: normalized job display table synchronized from `jobs`.

Example output:

```json
{
  "jobs": 5000,
  "candidates": 1000,
  "applications": 3000
}
```

## Database Cleanup

Audit unused legacy tables without changing data:

```bash
python backend/scripts/cleanup_db.py
```

Apply cleanup after reviewing the candidate list:

```bash
python backend/scripts/cleanup_db.py --apply --purge-data
```

Protected business tables include `jobs`, `candidates`, `applications`, `job`,
`student`, `users`, `assessment_results`, `match_history`, `report_history`,
and frontend-facing content/profile tables. `assessment_results`, `*_history`,
`job_profile`, and `job_relations` can be purged as runtime/cache data while
keeping their schemas. `job_categories` is dropped because category data now
comes directly from `jobs.job_category`.

## Jobs

### Search Jobs

`GET /api/jobs/search?page=1&size=10&keyword=Python&industry=技术`

Response:

```json
{
  "total": 12,
  "page": 1,
  "size": 10,
  "items": [
    {
      "id": 1,
      "job_name": "Python开发工程师",
      "location": "杭州",
      "salary_range": "10000-18000",
      "company": "星途科技",
      "industry": "技术",
      "company_size": "20-99人",
      "company_type": "民营"
    }
  ]
}
```

### Job Profile

`GET /api/jobs/{job_id}/profile`

The endpoint first reads cached `job_profile`. If missing, it generates an offline ML/rule profile from job text and caches it, reducing LLM token usage.

Response:

```json
{
  "job_name": "Python开发工程师",
  "skills": ["Python", "Flask", "SQL"],
  "certificates": [],
  "soft_abilities": {
    "学习能力": {"score": 4, "description": "需要持续学习岗位相关工具和业务知识"}
  },
  "source": "ml_rules"
}
```

### Similar Jobs

`GET /api/jobs/{job_id}/similar?top_k=10`

Response:

```json
{
  "success": true,
  "model_source": "word2vec",
  "data": [
    {"job_id": 23, "similarity": 0.9123}
  ]
}
```

When the Word2Vec vector artifact is unavailable, the endpoint falls back to rule-based similarity and returns `"model_source": "rules"`.

## Match

### Recommend Jobs For Student

`GET /api/match/recommend?student_id=2&limit=10`

Response:

```json
{
  "results": [
    {
      "job_name": "Python开发工程师",
      "overall_score": 82.5,
      "skill_fit": 76.0,
      "soft_gap": 18.0,
      "cert_coverage": 0.0,
      "education_score": 80.0,
      "experience_score": 60.0
    }
  ],
  "total": 50
}
```

### Match Detail

`POST /api/match/match`

Request:

```json
{
  "student_id": 2,
  "job_name": "Python开发工程师"
}
```

Response:

```json
{
  "overall_score": 82.5,
  "skill_fit": 76.0,
  "gap_analysis": {
    "skills": "建议补齐 Flask 项目经验和 SQL 优化案例。",
    "recommended_resources": "Flask 官方教程、SQL 优化实战、部署项目作品集。"
  }
}
```

### Streaming Match

`POST /api/match/match-stream`

Returns `text/event-stream`:

```text
data: {"type":"base","data":{"overall_score":82.5}}

data: {"type":"gap","field":"skills","text":"建议补齐 Flask..."}

data: {"type":"done"}
```

## LLM

### Existing QA

`POST /api/llm/qa`

Request:

```json
{
  "question": "数据分析岗位需要哪些技能？",
  "context": "本科，熟悉 Python 和 Excel"
}
```

Response:

```json
{
  "answer": "建议补齐 SQL、统计分析、可视化和业务指标拆解能力。"
}
```

### Provider Switch

Set `LLM_PROVIDER` to:

- `deepseek`: use DeepSeek chat completions.
- `zhipu`: use Zhipu GLM chat completions.
- `auto`: prefer Zhipu, then DeepSeek, then local fallback.
- `local`: no external call, deterministic local response.

## Assistant

### Chat

`POST /api/assistant/chat`

Request:

```json
{
  "message": "我想找 Python 后端岗位，应该补哪些技能？",
  "context": {
    "skills": ["Python", "SQL"],
    "major": "计算机科学与技术"
  },
  "provider": "deepseek",
  "stream": false
}
```

Response:

```json
{
  "answer": "建议重点补齐 Flask/FastAPI、SQL 优化、接口设计、项目部署和简历中的量化项目成果。",
  "provider": "deepseek",
  "usage": {
    "fallback": false
  }
}
```

Streaming request:

```json
{
  "message": "帮我规划数据分析学习路径",
  "stream": true
}
```

Streaming response:

```text
data: {"type":"start","provider":"local"}

data: {"type":"delta","content":"可以先明确目标岗位..."}

data: {"type":"done"}
```

## Error Format

Common validation errors:

```json
{
  "error": "message is required"
}
```

HTTP status codes:

- `200`: success.
- `400`: missing or invalid request parameter.
- `404`: requested student/job not found.
- `500`: unexpected server error.
