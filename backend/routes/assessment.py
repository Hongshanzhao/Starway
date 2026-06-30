import json
import os
import random

from flask import Blueprint, jsonify, request, session

from db import get_db
from services.career_ai_service import call_llm
from services.llm_client import provider_chain


assessment_bp = Blueprint("assessment", __name__, url_prefix="/api/assessment")


@assessment_bp.route("/questions", methods=["GET"])
def get_questions():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, question, dimension FROM assessment_questions ORDER BY sort_order"
        ).fetchall()
    finally:
        conn.close()
    questions = [{"id": r["id"], "question": r["question"], "dimension": r["dimension"]} for r in rows]
    random.shuffle(questions)
    return jsonify(questions)


@assessment_bp.route("/submit", methods=["POST"])
def submit_assessment():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers")
    if answers is None:
        return jsonify({"error": "answers required"}), 400
    if not answers:
        return jsonify({"error": "answers cannot be empty"}), 400

    user_id = _resolve_user_id(data)
    session_id = data.get("session_id", "guest")
    conn = get_db()
    try:
        scores = _calculate_dimension_scores(conn, answers)
        use_ai = request.args.get("ai") == "1"
        if use_ai and should_call_llm_api():
            recommendation = generate_career_recommendation(scores)
        else:
            recommendation = _fallback_recommendation(scores)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO assessment_results
            (user_id, session_id, dimension_scores, recommendation, raw_answers)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                json.dumps(scores, ensure_ascii=False),
                recommendation,
                json.dumps(answers, ensure_ascii=False),
            ),
        )
        conn.commit()
        result_id = cur.lastrowid
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "result_id": result_id,
        "dimension_scores": scores,
        "recommendation": recommendation,
    })


@assessment_bp.route("/history/<int:user_id>", methods=["GET"])
def get_history(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, dimension_scores, recommendation, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    return jsonify([
        {
            "id": row["id"],
            "dimension_scores": json.loads(row["dimension_scores"]),
            "recommendation": row["recommendation"],
            "created_at": row["created_at"],
        }
        for row in rows
    ])


def _resolve_user_id(data):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer mock-token-"):
        try:
            return int(auth_header.replace("Bearer mock-token-", "").strip())
        except ValueError:
            pass
    return data.get("user_id") or session.get("user_id") or 6


def _calculate_dimension_scores(conn, answers):
    totals = {}
    counts = {}
    for answer in answers:
        question_id = answer.get("question_id")
        score = answer.get("score")
        if not question_id or not isinstance(score, int) or score < 0 or score > 5:
            continue
        row = conn.execute("SELECT dimension FROM assessment_questions WHERE id = ?", (question_id,)).fetchone()
        if not row:
            continue
        dim = row["dimension"]
        totals[dim] = totals.get(dim, 0) + score
        counts[dim] = counts.get(dim, 0) + 1
    return {dim: round(totals[dim] / counts[dim], 2) for dim in totals if counts[dim]}


def generate_career_recommendation(dimension_scores):
    if not dimension_scores:
        return "未获取到有效测评得分，无法生成职业推荐。"
    sorted_dims = sorted(dimension_scores.items(), key=lambda item: item[1], reverse=True)
    prompt = f"""
基于霍兰德职业兴趣理论，以下是用户的维度得分（1-5 分）：
{sorted_dims}

请生成一份职业推荐报告，包括：
1. 维度得分解读
2. 主要兴趣类型分析
3. 推荐职业方向（3-5 个具体职业）
4. 职业发展建议

请使用普通中文文本输出，不要使用 Markdown 符号。内容要包含可执行的岗位探索建议和 30 天行动计划。
"""
    return call_llm(prompt, temperature=0.4, max_tokens=1600)


def _fallback_recommendation(dimension_scores):
    if not dimension_scores:
        return "这次测评没有形成有效得分，建议重新完成题目后再查看结果。"
    names = {
        "R": "现实型",
        "I": "研究型",
        "A": "艺术型",
        "S": "社会型",
        "E": "企业型",
        "C": "常规型",
    }
    sorted_dims = sorted(dimension_scores.items(), key=lambda item: item[1], reverse=True)
    top_codes = [code for code, _ in sorted_dims[:2]]
    top = [names.get(code, code) for code in top_codes]
    direction_map = {
        "R": "工程实施、测试、运维、质量管理、硬件调试",
        "I": "数据分析、算法助理、用户研究、测试开发、科研助理",
        "A": "视觉设计、内容策划、交互设计、品牌运营、产品体验",
        "S": "教育培训、人力资源、用户运营、客户成功、咨询助理",
        "E": "产品经理、项目管理、商业分析、销售运营、创业实践",
        "C": "财务、人事行政、流程管理、数据整理、质量审核",
    }
    directions = "；".join(direction_map.get(code, code) for code in top_codes)
    return (
        f"你的兴趣倾向最明显地落在{'、'.join(top)}。这并不是限制，而是一组方向线索："
        "可以优先寻找那些既能发挥高分维度，又能让你积累作品和经验的岗位。\n\n"
        f"可优先观察的方向包括：{directions}。选择岗位时不要只看名称，要看日常任务是否与你喜欢的工作方式一致。\n\n"
        "建议接下来做三件事：第一，选择 3 个相关岗位查看真实 JD，标出反复出现的技能、工具和交付物；"
        "第二，把已有课程、项目、社团或实习经历改写成岗位语言，形成 3 条可以放进简历的证据；"
        "第三，用 30 天完成一个小作品或一次深度调研，把兴趣从感受推进到证据。\n\n"
        "如果最高维度和第二维度差距不大，可以组合探索。例如研究型加常规型适合数据、测试、质量类岗位；"
        "艺术型加企业型适合产品、内容、品牌和用户增长；社会型加企业型适合运营、咨询、HR 和客户成功。"
    )


def should_call_llm_api():
    configured = any(provider != "local" for provider in provider_chain("auto"))
    env_enabled = os.getenv("ENABLE_LLM_RECOMMENDATION", "auto").lower()
    if env_enabled == "false":
        return False
    if env_enabled not in {"true", "auto", ""} and not configured:
        return False
    if not configured and env_enabled != "true":
        return False
    max_calls = int(os.getenv("MAX_DAILY_API_CALLS", "100"))
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM assessment_results
            WHERE DATE(created_at) = DATE('now')
            """
        ).fetchone()
        return row["cnt"] < max_calls
    finally:
        conn.close()
