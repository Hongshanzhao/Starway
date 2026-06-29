# Starway 后端技术方案

## 1. 技术栈

- Web 框架：Flask
- 数据库：SQLite
- 数据导入：天池公开数据集 CSV
- 机器学习：本地规则/Word2Vec/TextCNN 训练产物辅助岗位画像与推荐
- 大模型：智谱 GLM、DeepSeek、本地 fallback
- 流式输出：Server-Sent Events

## 2. 分层设计

### 路由层

路由层只负责参数读取、鉴权、响应格式和 HTTP 状态码。

- `routes/auth.py`：图形验证码、注册、登录、短信接口禁用响应、token/admin 装饰器。
- `routes/user.py`：当前用户、用户资料、头像、密码、手机号绑定、个人报告、浏览历史和统计。
- `routes/job.py`：岗位搜索、岗位详情、岗位画像、相似岗位、职业路径。
- `routes/profile.py`：学生画像提交、简历上传解析、画像详情。
- `routes/match.py`：岗位推荐、匹配计算、匹配历史、流式匹配。
- `routes/report.py`：报告生成、流式生成、润色、导出、历史。
- `routes/assessment.py`：兴趣测评问题、提交、历史。
- `routes/assistant.py`：职业规划智能助手。
- `routes/llm.py`：LLM 连接测试、推荐、规划、问答兼容接口。
- `routes/admin.py`：管理端用户、岗位、报告和图谱管理。

### 服务层

- `services/data_importer.py`：天池三表建表和导入，同步 `job` 兼容表。
- `services/db_cleanup.py`：废弃表清理和运行缓存清空。
- `services/ml_recommender.py`：技能抽取、岗位画像生成、人岗规则推荐。
- `services/job_ml_service.py`：加载 Word2Vec 岗位向量和 TextCNN 技能预测模型，模型不可用时降级到规则。
- `services/career_ai_service.py`：业务级 AI 能力编排。
- `services/llm_client.py`：DeepSeek、智谱、本地 fallback 的统一客户端。

### 数据层

`db.py` 只保留：

- `get_db()`
- `init_db()`
- 当前业务表创建
- 必要字段迁移
- 废弃表 drop

不再承担 Excel 导入、废弃表创建、短信验证码表初始化。

## 3. LLM 策略

`.env` 示例：

```env
LLM_PROVIDER=auto
ZHIPU_API_KEY=your_zhipu_key
DEEPSEEK_API_KEY=your_deepseek_key
```

选择规则：

- `local`：不调用外部 API。
- `zhipu`：只调用智谱。
- `deepseek`：只调用 DeepSeek。
- `auto`：优先智谱，其次 DeepSeek，没有 key 时使用本地 fallback。

业务策略：

- 岗位画像和推荐优先使用本地 ML/规则，减少 token 消耗。
- `/api/jobs/{job_id}/similar` 和 `/api/jobs/{job_name}/full-path` 优先使用 `data/embeddings/job_vectors_word2vec.pkl`。
- `/api/jobs/skills` 优先使用 `data/models/skill_predictor.pth`、`skill_text_processor.pkl`、`skill_label_extractor.pkl`。
- 所有 ML 接口返回 `model_source`，用于标识 `word2vec`、`textcnn` 或 `rules`。
- 报告生成、差距解释、助手问答使用 LLM。
- LLM 异常不抛给前端，返回本地 fallback 内容。

## 4. 数据库初始化策略

启动时执行：

1. `ensure_core_tables()` 创建 `jobs`、`candidates`、`applications`、`job`。
2. `db.py` 创建当前业务运行表。
3. 补齐旧库缺失字段。
4. 删除废弃表：`verification_codes`、`job_categories` 等。

核心天池表为 `jobs`、`candidates`、`applications`。`assessment_results`、`match_history`、`report_history`、`job_profile`、`job_relations` 只清空数据，不删除表结构。

## 5. 测试与验证

主要验证命令：

```powershell
python -m unittest discover backend\tests -v
python backend\scripts\audit_api_outputs.py
python -m compileall backend\routes backend\services backend\app.py backend\db.py
```

接口审计脚本使用临时数据库副本，避免污染真实数据。
