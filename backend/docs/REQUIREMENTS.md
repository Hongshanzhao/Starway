# Starway 后端需求文档

## 1. 项目定位

Starway 是面向大学生的职业规划系统。后端围绕天池岗位、求职者、应聘数据，提供岗位检索、学生画像、兴趣测评、人岗匹配、职业报告生成和智能助手能力。

## 2. 用户角色

- 学生用户：注册登录、维护个人画像、上传简历、完成测评、查看岗位、获取推荐、生成报告、使用 AI 助手。
- 管理员：维护用户、岗位、报告，触发岗位图谱和岗位分类统计构建。
- 系统服务：导入天池数据、清理废弃表、生成岗位画像缓存、调用本地 ML 和 LLM。

## 3. 核心业务流程

1. 数据初始化：创建核心表，导入 `jobs`、`candidates`、`applications`，同步兼容表 `job`。
2. 用户认证：注册和登录只使用图形验证码，不启用短信验证码。
3. 学生画像：表单或简历解析生成技能、证书、软能力、教育经历、项目经历。
4. 岗位画像：优先读取 `job_profile` 缓存；没有缓存时用本地 ML/规则从岗位文本生成并写入缓存。
5. 人岗匹配：按技能、证书、软能力、学历、经历计算匹配分，并可调用 LLM 生成差距建议。
6. 职业报告：结合学生画像、岗位画像、匹配结果生成 Markdown 报告，支持普通和 SSE 流式输出。
7. 智能助手：支持 DeepSeek、智谱、本地 fallback 三种模式，为职业规划问答提供辅助。

## 4. 数据要求

核心表：

- `jobs`：天池岗位原始数据。
- `candidates`：天池求职者原始数据。
- `applications`：天池应聘匹配记录。
- `job`：兼容旧业务的岗位展示表。
- `users`：账号、角色、头像。
- `student`：学生能力画像。
- `job_profile`：岗位画像缓存。
- `assessment_questions` / `assessment_results`：兴趣测评。
- `match_history`：匹配历史。
- `report_history`：职业报告历史。
- `content`：运营内容。
- `user_profiles` / `user_browse_history`：用户扩展信息和浏览历史。

废弃表不再初始化：

- `verification_codes`
- `job_categories`
- `job_tags`
- `interests`
- `user_interests`
- `ability_dimensions`
- `ability_assessments`
- `user_plans`
- `plan_stages`
- `plan_goals`
- `plan_milestones`
- `path_types`
- `path_stage_templates`
- `learning_resources`
- `mentors`
- `practices`

## 5. 非功能要求

- 后端启动必须幂等，重复调用 `init_db()` 不破坏核心数据。
- LLM 失败时必须 fallback 到本地规则，不影响接口可用。
- 流式接口统一使用 SSE。
- 数据清理只删除废弃表或清空运行缓存，不删除核心三表。
- 所有接口必须返回非空内容，并有稳定状态码和错误格式。
