import json
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import get_db, init_db


QUESTIONS = [
    ("我喜欢动手操作机械或工具", "R", 1),
    ("我喜欢思考和分析问题", "I", 2),
    ("我喜欢绘画、音乐或写作", "A", 3),
    ("我喜欢帮助他人解决问题", "S", 4),
    ("我喜欢领导和组织活动", "E", 5),
    ("我喜欢按规则和流程做事", "C", 6),
]

JOBS = [
    ("JOB-DEMO-001", "Python后端工程师", "技术", "星途科技", "100-499人", "民营", "杭州", "本科", "1-3年", 10000, 18000, 14000, "Python,Flask,SQL,Redis,Docker", "负责后端 API、数据库建模、服务部署与性能优化。", "熟悉 Python Web 框架、SQL 优化和接口设计。", "2026-06-30", 120, 24),
    ("JOB-DEMO-002", "数据分析师", "技术", "云杉数据", "500-999人", "民营", "上海", "本科", "应届", 9000, 16000, 12500, "SQL,Python,Excel,ECharts,统计分析", "负责业务数据指标分析、看板搭建和增长洞察。", "熟悉 SQL、Python 数据处理和可视化表达。", "2026-06-30", 98, 18),
    ("JOB-DEMO-003", "前端开发工程师", "技术", "莫兰迪互动", "20-99人", "民营", "深圳", "本科", "1-3年", 11000, 20000, 15500, "Vue,JavaScript,TypeScript,Element Plus,ECharts", "负责 Web 前端功能开发、组件复用和体验优化。", "熟悉 Vue3、工程化和数据可视化。", "2026-06-30", 88, 16),
    ("JOB-DEMO-004", "产品经理助理", "产品", "北岸科技", "100-499人", "民营", "北京", "本科", "应届", 8000, 14000, 11000, "需求分析,原型设计,沟通协作,数据分析", "协助需求调研、竞品分析、原型设计和项目推进。", "具备清晰表达、用户洞察和文档能力。", "2026-06-30", 76, 12),
    ("JOB-DEMO-005", "自动化测试工程师", "技术", "知行软件", "1000-9999人", "上市", "广州", "本科", "1-3年", 10000, 17000, 13500, "Python,自动化测试,接口测试,Linux,Jenkins", "负责接口自动化、质量保障和缺陷定位。", "熟悉测试流程、Python 脚本和 CI 工具。", "2026-06-30", 67, 10),
]


def table_count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def seed():
    init_db()
    conn = get_db()
    try:
        if table_count(conn, "users") == 0:
            conn.execute(
                "INSERT INTO users (username, phone, password_hash, role) VALUES (?, ?, ?, ?)",
                ("student01", "13900000000", generate_password_hash("pass123"), "user"),
            )
            conn.execute(
                "INSERT INTO users (username, phone, password_hash, role) VALUES (?, ?, ?, ?)",
                ("admin", "13811110000", generate_password_hash("pass123"), "admin"),
            )

        if table_count(conn, "student") == 0:
            conn.execute(
                """
                INSERT INTO student (
                    user_id, name, major, grade, skills, certificates, internships,
                    completeness, competitiveness, phone, email, education_text,
                    work_text, project_text, skills_certs_text, summary,
                    soft_abilities, education_json, work_json, project_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    "张三",
                    "计算机科学与技术",
                    "大四",
                    json.dumps(["Python", "SQL", "Vue", "Flask"], ensure_ascii=False),
                    json.dumps(["CET-6"], ensure_ascii=False),
                    "后端开发实习，参与 API 与数据看板开发。",
                    86,
                    78,
                    "13900000000",
                    "student@example.com",
                    "本科 计算机科学与技术",
                    "后端实习，负责 Flask API 开发。",
                    "校园职业规划系统，负责前后端联调和可视化。",
                    "Python, SQL, Vue, Flask, CET-6",
                    "希望从事后端开发或数据分析方向。",
                    json.dumps({
                        "创新能力": {"score": 4, "description": "能主动尝试新方案。"},
                        "学习能力": {"score": 5, "description": "持续学习框架和工程实践。"},
                        "抗压能力": {"score": 4, "description": "能稳定推进项目。"},
                        "沟通能力": {"score": 4, "description": "能清晰表达需求和方案。"},
                        "实习能力": {"score": 4, "description": "有项目和实习基础。"},
                    }, ensure_ascii=False),
                    json.dumps({"school": "某大学", "major": "计算机科学与技术", "degree": "本科"}, ensure_ascii=False),
                    json.dumps([{"company": "星途科技", "position": "后端实习生", "description": "参与接口开发。"}], ensure_ascii=False),
                    json.dumps([{"project_name": "Starway", "role": "开发", "description": "职业规划系统。"}], ensure_ascii=False),
                ),
            )

        users_without_student = conn.execute(
            """
            SELECT u.id, u.username, u.phone
            FROM users u
            LEFT JOIN student s ON s.user_id = u.id
            WHERE s.id IS NULL
            """
        ).fetchall()
        for user in users_without_student:
            conn.execute(
                """
                INSERT INTO student (
                    user_id, name, skills, certificates, completeness, competitiveness,
                    phone, summary, soft_abilities, education_json, work_json, project_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    user["username"],
                    json.dumps([], ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                    12,
                    20,
                    user["phone"],
                    "刚刚加入 Starway，建议先完善学生画像。",
                    json.dumps({
                        "创新能力": {"score": 3, "description": "待通过项目经历进一步识别。"},
                        "学习能力": {"score": 3, "description": "待通过技能和证书进一步识别。"},
                        "抗压能力": {"score": 3, "description": "待通过实习和项目经历进一步识别。"},
                        "沟通能力": {"score": 3, "description": "待通过协作经历进一步识别。"},
                        "实习能力": {"score": 2, "description": "建议补充实习或项目作品。"},
                    }, ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                ),
            )

        if table_count(conn, "assessment_questions") == 0:
            conn.executemany(
                "INSERT INTO assessment_questions (question, dimension, sort_order) VALUES (?, ?, ?)",
                QUESTIONS,
            )

        if table_count(conn, "jobs") == 0:
            conn.executemany(
                """
                INSERT INTO jobs (
                    job_id, job_title, job_category, company_name, company_size,
                    company_type, city, education, experience, salary_min,
                    salary_max, salary_avg, skills, job_description, requirements,
                    publish_date, views, applications
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                JOBS,
            )

        conn.commit()
        print("demo data ready")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
