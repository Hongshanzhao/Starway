import os
import sys
import json
import logging

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# 将项目根路径和 backend 目录加入 PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 【关键】强制开启真实 API 调用模式，覆盖 .env 配置
os.environ['LLM_FORCE_REAL'] = '1'
os.environ['LLM_MODE'] = 'auto'

from backend.app import app
from backend.db import get_db

# 配置日志输出到 stdout，确保 pytest -s 能看到详细打印
# force=True 确保即使 pytest 捕获也能看到部分关键日志
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True)
logger = logging.getLogger(__name__)


def setup_module(module):
    """初始化数据库，准备测试数据"""
    print("\n🔧 [SETUP] 正在初始化测试数据库...", flush=True)
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        # 清理旧数据
        cursor.execute('DELETE FROM match_history')
        cursor.execute('DELETE FROM student')
        cursor.execute('DELETE FROM job_profile')
        cursor.execute('DELETE FROM job')

        # 1. 插入一个技能较少的学生 (ID=1)，用于测试缺失技能提示
        cursor.execute(
            "INSERT INTO student (id, user_id, name, major, grade, skills, certificates, soft_abilities, internships) VALUES (?,?,?,?,?,?,?,?,?)",
            (1, 1, 'StudentEmpty', '计算机', '本科', json.dumps([]), json.dumps([]), json.dumps({}), '')
        )
        
        # 2. 插入一个技能丰富的学生 (ID=2)，用于测试匹配和差距分析
        cursor.execute(
            "INSERT INTO student (id, user_id, name, major, grade, skills, certificates, soft_abilities, internships) VALUES (?,?,?,?,?,?,?,?,?)",
            (2, 2, 'StudentFull', '计算机', '硕士', json.dumps(['python', 'sql']), json.dumps(['AWS']), json.dumps({'communication': {'score': 4}}), '3 年')
        )

        # 3. 插入岗位数据
        cursor.execute(
            "INSERT INTO job (id, job_name, job_description) VALUES (?,?,?)",
            (1, '软件工程师', '软件工程师，要求 3 年以上经验，精通 Python/Flask，熟悉 AWS，硕士优先')
        )
        cursor.execute(
            "INSERT INTO job_profile (id, job_name, skills, certificates, soft_abilities) VALUES (?,?,?,?,?)",
            (1, '软件工程师', json.dumps(['python', 'flask', 'sql', 'docker']), json.dumps(['AWS']), json.dumps({'communication': {'score': 5}, 'teamwork': {'score': 4}}))
        )

        conn.commit()
        conn.close()
        print("✅ [SETUP] 数据库初始化完成\n", flush=True)


def test_profile_submit_and_structured():
    """
    【核心测试 1】学生能力画像解析 (profile.py)
    目标：调用真实 API，提交简历文本，验证并打印大模型提取的结构化 JSON 内容。
    """
    print("\n" + "="*80, flush=True)
    print("🚀 [TEST 1] 开始测试：Profile Submit (真实调用阿里云 API)", flush=True)
    print("🎯 验证点：大模型能否从文本中提取出丰富的教育、工作、项目细节", flush=True)
    print("="*80, flush=True)

    with app.test_client() as c:
        # 构造一段包含丰富细节的简历文本
        payload = {
            'user_id': 99,
            'name': '测试用户 - 真实 API',
            'phone': '13800138000',
            'email': 'test_real@api.com',
            'education': '清华大学计算机科学与技术专业，本科，GPA 3.9/4.0，连续三年获得国家级奖学金。主修数据结构、算法设计、分布式系统。',
            'work': '阿里巴巴集团 - 后端开发工程师 (2021.07-至今)\n1. 负责淘宝用户中心微服务重构，使用 Python Flask + Docker 容器化部署，QPS 从 5k 提升至 20k。\n2. 主导双 11 大促流量压测，优化 Redis 缓存策略，降低数据库负载 40%。\n3. 设计并实现分布式任务调度系统，支持每日亿级数据处理。',
            'project': '智能招聘匹配系统 (个人全栈项目)\n技术栈：Python, Flask, SQLite, Redis, Vue.js\n描述：基于协同过滤算法实现人岗精准推荐。独立完成从需求分析、数据库设计到前端页面的全流程开发。实现了简历 PDF 解析与自动打分功能。',
            'skills_certs': 'Python, SQL, Flask, Docker, Kubernetes, Redis, AWS, PMP 证书，英语六级',
            'summary': '热爱技术，具备极强的学习能力和抗压能力。善于解决复杂分布式系统问题，有良好的代码规范和团队协作精神。'
        }

        print("📤 发送请求至 /api/profile/submit ... (等待大模型响应)", flush=True)
        resp = c.post('/api/profile/submit', json=payload)
        
        # 【修改】如果状态码不是 200，直接抛出异常，迫使测试失败并显示日志
        if resp.status_code != 200:
            error_msg = f"❌ API 调用失败！状态码：{resp.status_code}, 响应：{resp.get_json()}"
            print(error_msg, flush=True)
            raise AssertionError(error_msg)
            
        data = resp.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            raise AssertionError("❌ 提交成功但未返回 student_id")
            
        print(f"✅ 提交成功！生成 Student ID: {student_id}", flush=True)
        
        # 立即查询数据库，获取大模型解析后的完整结构化数据
        print("🔍 正在从数据库读取大模型解析结果...", flush=True)
        query_resp = c.get(f'/api/profile/{student_id}')
        
        if query_resp.status_code != 200:
            raise AssertionError(f"❌ 查询解析结果失败：{query_resp.get_json()}")

        profile = query_resp.get_json()

        # ================= 打印核心结果 (重点) =================
        print("\n" + "#"*80, flush=True)
        print("📄 【大模型解析结果展示】 (请直接检查以下内容是否丰富、准确)", flush=True)
        print("#"*80, flush=True)
        
        edu_json = profile.get('education_json', {})
        print(f"\n1️⃣ 教育背景 (education_json):\n{json.dumps(edu_json, ensure_ascii=False, indent=2)}", flush=True)
        
        work_list = profile.get('work_json', [])
        print(f"\n2️⃣ 工作经历 (work_json) [共 {len(work_list) if isinstance(work_list, list) else 0} 条]:", flush=True)
        if isinstance(work_list, list):
            for i, work in enumerate(work_list):
                print(f"   --- 经历 {i+1} ---\n{json.dumps(work, ensure_ascii=False, indent=2)}", flush=True)
        else:
            print(work_list, flush=True)
            
        proj_list = profile.get('project_json', [])
        print(f"\n3️⃣ 项目经历 (project_json) [共 {len(proj_list) if isinstance(proj_list, list) else 0} 条]:", flush=True)
        if isinstance(proj_list, list):
            for i, proj in enumerate(proj_list):
                print(f"   --- 项目 {i+1} ---\n{json.dumps(proj, ensure_ascii=False, indent=2)}", flush=True)
        else:
            print(proj_list, flush=True)

        skills = profile.get('skills', [])
        certs = profile.get('certificates', [])
        print(f"\n4️⃣ 提取的技能列表 ({len(skills)} 项):\n{skills}", flush=True)
        print(f"\n5️⃣ 提取的证书列表 ({len(certs)} 项):\n{certs}", flush=True)
        
        print("\n" + "#"*80 + "\n", flush=True)
        # ================= 结果展示结束 =================

        # 【修改】增加强制断言，确保内容非空，否则测试失败以便排查
        if not edu_json or not edu_json.get('school'):
            raise AssertionError("⚠️ 测试未通过：教育背景解析为空或缺少 school 字段，可能未调用真实 API 或 Prompt 失效。")
        
        if not work_list or not isinstance(work_list, list) or len(work_list) == 0:
            raise AssertionError("⚠️ 测试未通过：工作经历解析为空，可能未调用真实 API。")
        
        # 检查工作职责是否有内容
        first_work = work_list[0]
        responsibilities = first_work.get('responsibilities', '')
        if isinstance(responsibilities, list):
            resp_len = len("".join(str(i) for i in responsibilities))
        else:
            resp_len = len(str(responsibilities))
            
        if resp_len < 10:
            raise AssertionError(f"⚠️ 测试未通过：工作经历描述过于简单 (长度:{resp_len})，疑似未调用真实 API。")

        print("✅ [TEST 1] Profile 测试执行完毕，内容验证通过。", flush=True)


def test_match_detail_gap_analysis():
    """
    【核心测试 2】人岗匹配差距分析 (match.py)
    目标：调用真实 API，计算学生与岗位的匹配度，验证并打印大模型生成的差距分析建议。
    """
    print("\n" + "="*80, flush=True)
    print("🚀 [TEST 2] 开始测试：Match Detail & Gap Analysis (真实调用阿里云 API)", flush=True)
    print("🎯 验证点：大模型能否根据具体缺失技能，给出有针对性的改进建议", flush=True)
    print("="*80, flush=True)

    with app.test_client() as c:
        # 使用 setup_module 中插入的 student_id=2 (有 python, sql, AWS)
        # 目标岗位：软件工程师 (要求 python, flask, sql, docker, AWS)
        # 预期缺失：flask, docker
        print("📤 发送请求至 /api/match/match (Student ID: 2, Job: 软件工程师)...", flush=True)
        resp = c.post('/api/match/match', json={'student_id': 2, 'job_name': '软件工程师'})
        
        if resp.status_code != 200:
            error_msg = f"❌ API 调用失败！状态码：{resp.status_code}, 响应：{resp.get_json()}"
            print(error_msg, flush=True)
            raise AssertionError(error_msg)
            
        data = resp.get_json()
        
        print(f"✅ 匹配计算成功！综合得分：{data.get('overall_score')}", flush=True)
        print(f"📊 技能匹配度：{data.get('skill_fit')}% | 证书覆盖率：{data.get('cert_coverage')}%", flush=True)

        # ================= 打印核心结果 (重点) =================
        gap_analysis = data.get('gap_analysis', {})
        
        if not gap_analysis:
            raise AssertionError("❌ 测试未通过：gap_analysis 字段为空，疑似未调用真实 API。")

        print("\n" + "#"*80, flush=True)
        print("🤖 【大模型生成的差距分析详情】 (请检查建议是否具体、有针对性)", flush=True)
        print("#"*80, flush=True)
        
        total_len = 0
        for key, value in gap_analysis.items():
            val_str = str(value)
            total_len += len(val_str)
            print(f"\n📌 [{key.upper()}]:", flush=True)
            # 格式化输出，如果是长文本则换行
            if isinstance(value, str) and len(value) > 50:
                print(f"   {value}", flush=True)
            else:
                print(f"   {json.dumps(value, ensure_ascii=False)}", flush=True)
                
        print("\n" + "#"*80 + "\n", flush=True)
        # ================= 结果展示结束 =================

        # 【修改】验证内容长度，确保不是模板或空值
        if total_len < 100:
            raise AssertionError(f"⚠️ 测试未通过：差距分析内容过短 ({total_len} 字符)，疑似未调用真实 API 或返回了默认模板。")

        if 'recommended_resources' not in gap_analysis:
            raise AssertionError("⚠️ 测试未通过：缺少 recommended_resources 字段。")

        print("✅ [TEST 2] Match 测试执行完毕，内容验证通过。", flush=True)