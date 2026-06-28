# 系统部署与运行指南

## 一、环境要求

| 环境 | 版本要求 |
|------|----------|
| Python | 3.8 及以上 |
| Node.js | 16.0 及以上 |
| 操作系统 | Windows / macOS / Linux |

---

## 二、后端部署

### 
2.1 进入后端目录
```bash
cd backend

 2.2 创建虚拟环境（推荐）
Windows：
python -m venv venv
venv\Scripts\activate

Mac / Linux：
python -m venv venv
source venv/bin/activate

2.3 安装依赖
pip install -r requirements.txt

2.4 配置环境变量（重要）
在 backend 目录下创建 .env 文件：
ALIYUN_API_KEY=你的阿里云百炼API Key
注意：如果没有配置 API Key，以下功能可能将无法使用：
1、AI 职业规划报告生成   2、岗位画像动态生成（只能查看以前生成好的）  3、AI 简历智能解析   4、兴趣测评 AI 推荐

2.6 启动后端服务
python app.py
启动成功提示：
* Running on http://127.0.0.1:5000
✅ 后端服务默认运行在：http://localhost:5000

三、前端部署
3.1 进入前端目录
cd frontend

3.2 安装依赖
npm install

3.3 启动前端服务
npm run dev

启动成功提示：

VITE v4.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
✅ 前端服务默认运行在：http://localhost:5173

测试用户 u1 密码：12345678



```
frontend/                # 前端代码
  index.html             # 入口html
  package.json           # npm依赖与脚本
  vite.config.js
  src/
    main.js              # Vue应用入口
    app.vue              # 顶层组件
    style.css            # 全局样式
    router/              # 路由定义
      index.js
    views/               # 所有页面视图组件
      Home.vue
      Login.vue
      Register.vue
      AdminLogin.vue
      AdminDashboard.vue
      StudentInfo.vue
      MatchResult.vue
      Report.vue
      JobPortrait.vue
      AbilityAssessment.vue
      CareerPlanning.vue
      ReportGenerate.vue
      ResourceLibrary.vue
      AboutUs.vue
      CareerInterestTest.vue
      AbilityAnalysis.vue
      DevelopmentPath.vue
      ReportExport.vue
      ...                # 其他页面多数为功能占位或完整表单

后端说明
backend/
  app.py                 # Flask 应用主入口，注册所有蓝图、初始化全局配置与数据库
  config.py              # 全局配置文件，数据库路径、文件上传目录、API 密钥、运行模式等
  db.py                  # 数据库操作封装，提供连接、建表、数据导入与通用 CRUD 方法
  schema.sql             # 标准建表脚本，用于数据库初始化、迁移与环境重建
  models.py              # 数据实体定义，规范用户、学生、岗位、报告等数据结构
  algorithms.py          # 传统匹配算法实现，岗位推荐、人岗匹配、评分计算核心逻辑
  
  routes/                # 接口路由层，所有前端请求入口
    __init__.py          # 路由统一导出
    auth.py              # 用户登录、注册、token 鉴权、个人中心、权限控制
    admin.py             # 管理员接口，用户管理、数据管理、后台操作
    job.py               # 岗位查询、分类、详情、岗位画像与推荐接口
    profile.py           # 学生档案管理、简历上传、AI 解析、能力画像存储
    match.py             # 人岗匹配、匹配度计算、匹配报告生成与流式输出
    report.py            # 报告管理，测评报告、规划报告、匹配报告查询与导出
    llm.py                # 大模型接口，规划生成、智能问答、AI 能力调用
    assessment.py         # 职业兴趣测评、能力测评、结果提交与报告生成
  
  services/              # 业务服务层，封装复杂业务与第三方依赖
    llm_service.py       # 大模型统一服务，AI 核心：简历解析、岗位画像、图谱构建、规划生成、本地降级
    
  deprecated/            # 废弃代码目录，旧算法与历史实现，不参与主流程
  
  utils/                 # 工具函数库，通用处理、格式校验、文件操作
  uploads/               # 用户上传文件目录，头像、简历文件存储
  instance/              # 运行时目录，存放 SQLite 数据库文件 career.db

说明：
- 后端使用原生 sqlite3，采用 `db.init_db()` 动态创建表并支持 Excel 导入。
- 前端页面均使用 Element Plus / 原生组件实现 UI，部分页面使用 Canvas 绘图。
- 通过 `axios` 实现前端与后端的数据交互，授权使用简单 Bearer token `mock-token-<id>`。



```
```
