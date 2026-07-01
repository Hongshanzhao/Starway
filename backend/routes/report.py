import io
import json
import re
import time

from flask import Blueprint, Response, jsonify, request, send_file, stream_with_context

from db import get_db
from routes.match import compute_match, get_job_abilities, get_student_ability
from services.career_ai_service import call_llm, call_llm_stream
from services import job_repository
from services.llm_client import provider_chain


report_bp = Blueprint("report", __name__, url_prefix="/api/report")


def _report_prompt(student, job_name, match_detail):
    return f"""
你是 Starway 大学生职业规划平台的资深职业规划顾问。请基于学生画像、目标岗位和匹配结果，生成一份可直接导出的中文职业规划报告。

重要要求：
1. 必须围绕目标岗位「{job_name}」展开，不能输出通用模板。
2. 必须引用学生已有信息，例如专业、年级、技能、项目/实习经历、作品证据或缺失项。
3. 输出普通中文纯文本，不要使用 Markdown 标记，不要出现 #、**、*、```、模板占位符。
4. 全文使用第二人称“你/你的”，不要使用“您/您的”，不要写成客服聊天。
5. 每段都要给出具体判断或可执行动作，避免空泛鸡汤。

学生画像：{json.dumps(student, ensure_ascii=False, default=list)}

目标岗位：{job_name}
匹配结果：{json.dumps(match_detail, ensure_ascii=False)}

报告必须包含：
一、自我认知总结：说明学生当前基础、优势证据和画像缺口。
二、人岗匹配分析：解释综合匹配、方向匹配、已匹配技能、缺口技能、软能力和经历准备度。
三、目标岗位理解：说明该岗位真实工作内容、产出物和常见评价标准。
四、职业发展路径：给出入门、胜任、进阶三个阶段，每阶段说明能力重点和作品/经历证据。
五、90 天行动计划：按 0-30 天、31-60 天、61-90 天列出具体任务、交付物和检查标准。
六、投递与复盘建议：说明简历改写、面试准备、每周复盘指标。
"""


def _default_job_name():
    rows = job_repository.all_jobs(limit=1)
    return rows[0]["job_name"] if rows else "目标岗位"


def _remote_ai_enabled():
    requested = request.args.get("ai") if request else None
    if requested == "0":
        return False
    return any(provider != "local" for provider in provider_chain())


def _clean_report_text(value):
    text = str(value or "")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = text.replace("*", "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "· ", text, flags=re.MULTILINE)
    text = _to_second_person(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _clean_report_chunk(value):
    text = str(value or "")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = text.replace("*", "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return _to_second_person(text)


def _to_second_person(text):
    return (
        str(text or "")
        .replace("您好", "你好")
        .replace("您已经", "你已经")
        .replace("您可以", "你可以")
        .replace("您的", "你的")
        .replace("您", "你")
    )


def _local_polish_report(text, job_name="目标岗位"):
    cleaned = _clean_report_text(text)
    if not cleaned:
        return ""
    if len(cleaned) > 1800:
        return cleaned
    return f"""润色后的职业规划报告：{job_name}

{cleaned}

补充建议
请把上面的报告继续落到三个可执行层面：第一，围绕{job_name}整理 15 到 20 条真实 JD，标出高频技能、常见任务和交付物；第二，把已有项目或实习经历改写成“问题、动作、工具、结果、复盘”的结构；第三，每周复盘一次投递反馈、技能卡点和作品完成度。这样导出后的报告不仅能阅读，也能直接指导后续行动。"""


def _looks_generic_report(content, job_name):
    text = str(content or "")
    if len(text.strip()) < 300:
        return True
    if job_name and job_name not in text:
        return True
    generic_hits = sum(
        phrase in text
        for phrase in ["建议先明确一个主目标岗位", "职业规划不是一次性决定", "基础能力、项目作品、简历表达"]
    )
    return generic_hits >= 2


def _build_report(student_id, job_name):
    student = get_student_ability(student_id)
    if not student:
        raise ValueError("学生不存在")
    job_name = job_name or _default_job_name()
    match_detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name, use_llm_gap=False)
    prompt = _report_prompt(student, job_name, match_detail)
    content = ""
    if _remote_ai_enabled():
        try:
            content = _clean_report_text(call_llm(prompt, temperature=0.55, max_tokens=3200))
        except Exception:
            content = ""
    if _looks_generic_report(content, job_name):
        content = _fallback_report(student, job_name, match_detail)
    return job_name, content, match_detail


def _fallback_report(student, job_name, match_detail):
    debug = match_detail.get("debug_info") or {}
    matched = debug.get("matched_skills") or []
    missing = debug.get("missing_skills") or []
    required = debug.get("required_skills") or []
    skills = sorted(student.get("skills", []))
    major = student.get("major") or "专业信息待完善"
    grade = student.get("grade") or "年级待完善"
    has_project = bool(student.get("project_json"))
    has_work = bool(student.get("work_json") or student.get("internships"))
    role_focus = _role_focus(job_name, required)
    matched_text = "、".join(matched[:8]) if matched else "暂未识别到强匹配技能"
    missing_text = "、".join(missing[:8]) if missing else "暂无明显技能缺口，下一步重点是用项目证据证明能力"
    required_text = "、".join(required[:10]) if required else "请继续补充岗位 JD 或选择数据库中的具体岗位"
    skills_text = "、".join(skills[:12]) if skills else "技能信息待完善"
    project_text = "已有项目经历，可进一步沉淀为作品集和面试案例。" if has_project else "项目经历暂少，需要优先做一个贴近岗位的作品。"
    work_text = "已有实习/工作经历，可将职责改写成目标岗位语言。" if has_work else "实习经历暂少，需要用课程项目、开源任务或模拟业务项目补足经历证据。"
    return f"""职业生涯发展报告：{job_name}

一、自我认知总结
你的当前画像显示：专业为{major}，年级为{grade}，已记录技能包括{skills_text}。这说明你已经有一部分可用于求职表达的基础材料，但还需要把这些材料和「{job_name}」的真实职责连接起来。{project_text}{work_text}

对你来说，下一步不是单纯多学几门课，而是把“我会什么”改造成“我能为{job_name}交付什么”。简历、作品集和面试回答都应该围绕岗位产出展开，例如需求理解、方案设计、执行过程、结果指标、复盘改进。

二、人岗匹配分析
系统计算的综合匹配度为 {match_detail.get("overall_score")}%。技能匹配为 {match_detail.get("skill_fit")}%，方向匹配为 {match_detail.get("direction_fit")}%，学历基础为 {match_detail.get("education_score")}，经历基础为 {match_detail.get("experience_score")}。这个结果不是简单判断“能不能投”，而是告诉你目前最该补哪里。

已经能迁移到{job_name}的能力：{matched_text}。
岗位侧高频要求：{required_text}。
当前最需要补齐的缺口：{missing_text}。

如果匹配度偏低，优先处理缺口技能和作品证据；如果匹配度已经较高，重点改为提高表达质量，把项目成果写成可验证的简历条目。

三、目标岗位理解
{job_name}的准备重点可以概括为：{role_focus}。你需要证明自己不仅知道工具名，还能把工具用于真实问题。评价标准通常包括：是否理解业务或场景、是否能拆解任务、是否能独立完成关键环节、是否能解释结果质量、是否能在反馈后迭代。

建议你整理 15 到 20 条{job_name}相关 JD，把岗位职责按“工具技能、业务任务、协作方式、交付物”四类标注。这样能避免学习方向飘散，也能让后续报告和匹配结果更贴近真实招聘。

四、职业发展路径
入门阶段：先补齐{missing_text}中的前 2 到 3 项，配合一个小作品验证学习效果。作品不追求复杂，但必须有明确问题、输入输出、实现过程和结果截图或数据。

胜任阶段：围绕{job_name}制作一个完整案例。技术类岗位要有代码仓库、接口文档、测试记录或部署说明；产品/运营/分析类岗位要有调研过程、指标拆解、方案文档和效果评估；职能类岗位要有流程梳理、表格模板、风险清单和复盘记录。

进阶阶段：开始关注行业背景、团队协作和岗位晋升要求。你需要能说清楚“这个岗位在团队中解决什么问题”“我的方案为什么合理”“如果资源有限我如何取舍”。这类表达会明显提升面试可信度。

五、90 天行动计划
0-30 天：完成岗位拆解。收集 20 条{job_name} JD，统计高频技能和职责；选择 2 项最高频缺口集中学习；同步完善学生画像中的教育背景、项目经历、实习经历和作品证据。检查标准是形成一页岗位能力清单和一页个人差距清单。

31-60 天：完成作品验证。围绕{job_name}做一个可展示项目或案例，把需求、方案、执行、结果、复盘写完整。检查标准是至少产出一个作品链接或文档、一段 150 字简历描述、三分钟项目讲述稿。

61-90 天：进入投递准备。把作品和经历改写成岗位语言，准备 10 个面试高频问题，进行 3 次模拟面试。每周复盘投递数量、回复率、面试卡点和技能缺口，必要时调整岗位关键词或补充作品细节。

六、投递与复盘建议
简历中不要只写“熟悉”“了解”，要写你用什么方法解决了什么问题，结果如何验证。每条经历尽量包含动作、工具、场景和结果。面试时优先讲最贴近{job_name}的案例，少讲泛泛学习经历。

如果两周内投递反馈较少，先检查岗位关键词覆盖和项目成果是否具体；如果面试反馈卡在能力深度，回到缺口技能做小练习；如果发现自己对{job_name}兴趣不足，可以在相邻岗位中选择 2 个方向重新做人岗匹配对比。
"""


def _role_focus(job_name, required):
    text = " ".join([str(job_name or ""), " ".join(required or [])]).lower()
    if any(word in text for word in ["测试", "qa", "test"]):
        return "理解需求与风险，设计测试用例，执行功能/接口/自动化测试，并能用缺陷报告和质量数据说明结果"
    if any(word in text for word in ["前端", "vue", "react", "javascript"]):
        return "把交互需求实现成稳定页面，兼顾组件复用、接口联调、响应式布局、性能和用户体验"
    if any(word in text for word in ["后端", "java", "python", "spring", "flask", "api"]):
        return "设计清晰的数据模型和 API，处理鉴权、数据库、缓存、错误边界、日志和部署问题"
    if any(word in text for word in ["数据", "分析", "sql", "算法", "机器学习"]):
        return "把业务问题转成数据问题，完成清洗、分析、建模或可视化，并能解释结论对决策的价值"
    if any(word in text for word in ["产品", "需求", "用户"]):
        return "理解用户场景，拆解需求优先级，输出原型/需求文档，并推动研发、测试和运营协作落地"
    if any(word in text for word in ["运营", "市场", "内容"]):
        return "围绕用户增长、内容质量或转化目标设计动作，用数据复盘效果并持续迭代"
    return "拆解岗位职责，补齐关键技能，用项目或实习证据证明自己能完成真实工作任务"


@report_bp.route("/generate", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    job_name = data.get("job_name")
    if not student_id:
        return jsonify({"error": "缺少 student_id"}), 400
    try:
        job_name, content, _ = _build_report(student_id, job_name)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    report_id = _save_report(student_id, job_name, content, "markdown")
    return jsonify({"report_id": report_id, "content": content, "job_name": job_name})


@report_bp.route("/generate-stream", methods=["POST"])
def generate_report_stream():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    job_name = data.get("job_name") or _default_job_name()
    if not student_id:
        return jsonify({"error": "缺少 student_id"}), 400
    student = get_student_ability(student_id)
    if not student:
        return jsonify({"error": "学生不存在"}), 404

    match_detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name, use_llm_gap=False)
    prompt = _report_prompt(student, job_name, match_detail)

    def generate():
        chunks = []
        if _remote_ai_enabled():
            try:
                for chunk in call_llm_stream(prompt, temperature=0.45, max_tokens=1600):
                    if not chunk:
                        continue
                    chunks.append(chunk)
                    yield f"data: {json.dumps({'chunk': _clean_report_chunk(chunk)}, ensure_ascii=False)}\n\n"
            except Exception:
                chunks = []
        content = _clean_report_text("".join(chunks))
        if _looks_generic_report(content, job_name):
            content = _fallback_report(student, job_name, match_detail)
            yield f"data: {json.dumps({'chunk': content}, ensure_ascii=False)}\n\n"
        report_id = _save_report(student_id, job_name, content, "markdown")
        yield f"data: {json.dumps({'done': True, 'report_id': report_id}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@report_bp.route("/polish", methods=["POST"])
def polish_report():
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("content") or ""
    if not text:
        return jsonify({"error": "缺少文本内容"}), 400
    prompt = f"""
请润色以下职业规划报告，保持原意并提升专业度。
输出要求：
1. 使用普通中文纯文本，不要使用 Markdown 标记。
2. 不要输出 **、*、#、```、- 这类格式符号。
3. 全文使用第二人称“你/你的”，不要使用“您/您的”。
4. 保留清晰段落和编号，方便用户直接保存、复制和导出。

原文：
{text}
"""
    polished = call_llm(prompt, max_tokens=2000)
    return jsonify({"content": _clean_report_text(polished)})


@report_bp.route("/polish-stream", methods=["POST"])
def polish_report_stream():
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("content") or ""
    job_name = data.get("job_name") or "目标岗位"
    if not text:
        return jsonify({"error": "缺少文本内容"}), 400
    prompt = f"""
你是 Starway 职业规划报告编辑。请把下面这份报告润色为更有建议价值、更像真实顾问写给学生的版本。

要求：
1. 输出普通中文纯文本，不要 Markdown 符号。
2. 围绕目标岗位「{job_name}」补充具体建议、行动标准、简历表达方式和复盘指标。
3. 不要套模板，不要空泛鼓励；如果原文有数据，请解释数据对行动的意义。
4. 保留清晰编号，便于用户直接导出。
5. 全文使用第二人称“你/你的”，不要使用“您/您的”，不要写成聊天对话。

原文：
{text}
"""

    def generate():
        chunks = []
        try:
            for chunk in call_llm_stream(prompt, temperature=0.38, max_tokens=1200):
                if not chunk:
                    continue
                chunks.append(chunk)
                yield f"data: {json.dumps({'chunk': _clean_report_chunk(chunk)}, ensure_ascii=False)}\n\n"
        except Exception:
            chunks = []
        content = _clean_report_text("".join(chunks))
        if _looks_generic_report(content, job_name):
            content = _local_polish_report(text, job_name)
            yield f"data: {json.dumps({'chunk': content}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@report_bp.route("/<int:report_id>/insights", methods=["GET"])
def get_report_insights(report_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM report_history WHERE id = ?", (report_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "报告不存在"}), 404

    student = get_student_ability(row["student_id"])
    if not student:
        return jsonify({"error": "学生不存在"}), 404
    job_name = row["job_name"] or _default_job_name()
    detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name, use_llm_gap=False)
    debug = detail.get("debug_info") or {}
    matched = debug.get("matched_skills", [])
    missing = debug.get("missing_skills", [])
    required = debug.get("required_skills", [])
    if not required:
        required = _infer_required_skills(job_name)
    if not missing and required:
        missing = required[:6]
    readiness = [
        {
            "name": "画像完整度",
            "value": _profile_readiness(student),
            "text": "教育、技能、项目、实习字段越完整，AI 报告越能贴近个人情况。",
        },
        {
            "name": "作品证据",
            "value": 80 if student.get("project_json") else 35,
            "text": "至少准备一个能解释问题、过程和结果的作品或案例。",
        },
        {
            "name": "岗位理解",
            "value": 70 if required else 45,
            "text": f"建议拆解 15 到 20 条 {job_name} JD，确认高频任务和交付物。",
        },
        {
            "name": "投递准备",
            "value": 65 if matched else 40,
            "text": "简历需要把技能改写成岗位语言，并准备面试复盘记录。",
        },
    ]
    return jsonify({
        "job_name": job_name,
        "student_id": row["student_id"],
        "score": detail.get("overall_score", 0),
        "metrics": [
            {"name": "技能匹配", "value": detail.get("skill_fit", 0)},
            {"name": "方向匹配", "value": detail.get("direction_fit", 0)},
            {"name": "学历基础", "value": detail.get("education_score", 0)},
            {"name": "经历基础", "value": detail.get("experience_score", 0)},
            {"name": "软能力", "value": max(0, 100 - float(detail.get("soft_gap", 0) or 0))},
        ],
        "matched_skills": matched,
        "missing_skills": missing,
        "required_skills": required,
        "readiness": readiness,
        "timeline": [
            {"stage": "0-30 天", "title": "拆解岗位与补基础", "output": f"岗位能力清单、个人差距清单、优先补齐：{'、'.join(missing[:3]) if missing else '岗位高频技能'}"},
            {"stage": "31-60 天", "title": "完成岗位作品", "output": f"围绕 {job_name} 产出作品链接或文档、简历项目条目、复盘记录"},
            {"stage": "61-90 天", "title": "投递与面试复盘", "output": "投递记录、面试问题库、下一轮改进计划"},
        ],
        "gap_analysis": detail.get("gap_analysis", {}),
    })


def _profile_readiness(student):
    fields = [
        bool(student.get("major")),
        bool(student.get("grade")),
        bool(student.get("skills")),
        bool(student.get("education_json")),
        bool(student.get("project_json")),
        bool(student.get("work_json") or student.get("internships")),
    ]
    return round((sum(fields) / len(fields)) * 100, 1)


def _infer_required_skills(job_name):
    text = str(job_name or "").lower()
    if any(item in text for item in ["java", "后端", "开发"]):
        return ["Java", "Spring Boot", "SQL", "接口设计", "数据库", "项目部署"]
    if any(item in text for item in ["前端", "vue", "web"]):
        return ["Vue", "JavaScript", "组件化", "接口联调", "响应式布局", "性能优化"]
    if any(item in text for item in ["数据", "分析", "算法"]):
        return ["SQL", "Python", "数据清洗", "可视化", "统计分析", "业务指标"]
    if any(item in text for item in ["产品"]):
        return ["需求分析", "原型设计", "用户研究", "数据分析", "项目协作", "PRD"]
    if any(item in text for item in ["测试", "qa"]):
        return ["测试用例", "缺陷定位", "接口测试", "自动化测试", "质量复盘", "需求分析"]
    return ["岗位 JD 拆解", "关键技能练习", "作品证据", "简历表达", "面试复盘"]


@report_bp.route("/export", methods=["POST"])
def export_report():
    data = request.get_json(silent=True) or {}
    content = data.get("markdown") or data.get("content") or ""
    if not content:
        return jsonify({"error": "缺少 markdown 内容"}), 400
    export_type = (data.get("type") or data.get("format") or "text").lower()
    buffer = io.BytesIO(content.encode("utf-8"))
    if export_type == "html":
        return send_file(buffer, mimetype="text/html", as_attachment=True, download_name="starway_report.html")
    return send_file(buffer, mimetype="text/plain", as_attachment=True, download_name="starway_report.txt")


@report_bp.route("/history/<int:student_id>", methods=["GET"])
def get_report_history(student_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, student_id, job_name, content, format_type, created_at FROM report_history WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        ).fetchall()
    finally:
        conn.close()
    return jsonify([dict(row) for row in rows])


@report_bp.route("/<int:report_id>", methods=["GET"])
def get_report_detail(report_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM report_history WHERE id = ?", (report_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "报告不存在"}), 404
    return jsonify(dict(row))


@report_bp.route("/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    data = request.get_json(silent=True) or {}
    content = data.get("content")
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    conn = get_db()
    try:
        cur = conn.execute("UPDATE report_history SET content = ? WHERE id = ?", (content, report_id))
        conn.commit()
    finally:
        conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "报告不存在"}), 404
    return jsonify({"status": "ok"})


def _save_report(student_id, job_name, content, format_type):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO report_history (student_id, job_name, content, format_type, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, job_name, content, format_type, int(time.time())),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
