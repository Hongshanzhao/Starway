import json
import os
import random

from flask import Blueprint, jsonify, request, session

from db import get_db
from services.career_ai_service import call_llm


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
    test_mode = bool(data.get("test_mode", False))

    conn = get_db()
    try:
        scores = _calculate_dimension_scores(conn, answers)
        if test_mode or not should_call_llm_api():
            recommendation = "【测试模式】推荐功能已启用，正式使用时将生成个性化职业建议。"
        else:
            recommendation = generate_career_recommendation(scores)
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

请使用 Markdown 格式输出。
"""
    return call_llm(prompt, temperature=0.4, max_tokens=1600)


def should_call_llm_api():
    if os.getenv("ENABLE_LLM_RECOMMENDATION", "false").lower() != "true":
        return False
    max_calls = int(os.getenv("MAX_DAILY_API_CALLS", "100"))
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM assessment_results
            WHERE DATE(created_at) = DATE('now')
            AND recommendation NOT LIKE '%测试模式%'
            """
        ).fetchone()
        return row["cnt"] < max_calls
    finally:
        conn.close()
