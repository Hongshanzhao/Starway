import io
import json
import time

from flask import Blueprint, Response, jsonify, request, send_file, stream_with_context

from db import get_db
from routes.match import compute_match, get_job_abilities, get_student_ability
from services.career_ai_service import call_llm, call_llm_stream
from services import job_repository


report_bp = Blueprint("report", __name__, url_prefix="/api/report")


def _report_prompt(student, job_name, match_detail):
    return f"""
你是大学生职业规划顾问，请生成 Markdown 职业规划报告。
学生画像：{json.dumps(student, ensure_ascii=False, default=list)}

目标岗位：{job_name}
匹配结果：{json.dumps(match_detail, ensure_ascii=False)}

报告必须包含：
1. 自我认知总结
2. 人岗匹配分析
3. 职业发展路径
4. 分阶段行动计划
5. 评估与调整建议
"""


def _default_job_name():
    rows = job_repository.all_jobs(limit=1)
    return rows[0]["job_name"] if rows else "目标岗位"


def _build_report(student_id, job_name):
    student = get_student_ability(student_id)
    if not student:
        raise ValueError("学生不存在")
    job_name = job_name or _default_job_name()
    match_detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name)
    prompt = _report_prompt(student, job_name, match_detail)
    content = call_llm(prompt, temperature=0.5, max_tokens=3000)
    if not content or len(content.strip()) < 50:
        content = _fallback_report(student, job_name, match_detail)
    return job_name, content, match_detail


def _fallback_report(student, job_name, match_detail):
    skills = "、".join(sorted(student.get("skills", []))) or "待完善"
    return f"""# 职业生涯发展报告

## 一、自我认知总结
当前技能包括：{skills}。

## 二、人岗匹配分析
目标岗位：{job_name}，综合匹配度：{match_detail.get("overall_score")}。

## 三、职业发展路径
建议从基础岗位能力、项目经验、行业理解三个层面推进。

## 四、分阶段行动计划
短期补齐核心技能，中期完成项目作品，长期沉淀岗位方法论。

## 五、评估与调整建议
每月复盘技能掌握、简历成果和面试反馈，持续调整目标岗位。
"""


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

    match_detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name)
    prompt = _report_prompt(student, job_name, match_detail)

    def generate():
        chunks = []
        for chunk in call_llm_stream(prompt, temperature=0.5, max_tokens=3000):
            if not chunk:
                continue
            chunks.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        content = "".join(chunks) or _fallback_report(student, job_name, match_detail)
        report_id = _save_report(student_id, job_name, content, "markdown")
        yield f"data: {json.dumps({'done': True, 'report_id': report_id}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@report_bp.route("/polish", methods=["POST"])
def polish_report():
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("content") or ""
    if not text:
        return jsonify({"error": "缺少文本内容"}), 400
    prompt = f"请润色以下职业规划报告，保持原意并提升专业度：\n{text}"
    polished = call_llm(prompt, max_tokens=2000)
    return jsonify({"content": polished})


@report_bp.route("/export", methods=["POST"])
def export_report():
    data = request.get_json(silent=True) or {}
    content = data.get("markdown") or data.get("content") or ""
    if not content:
        return jsonify({"error": "缺少 markdown 内容"}), 400
    buffer = io.BytesIO(content.encode("utf-8"))
    return send_file(buffer, mimetype="text/markdown", as_attachment=True, download_name="starway_report.md")


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
