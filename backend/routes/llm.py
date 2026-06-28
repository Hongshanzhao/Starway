import os

from flask import Blueprint, jsonify, request

from db import get_db
from routes.auth import token_required
from services import career_ai_service
from services.llm_client import LLMClient


llm_bp = Blueprint("llm", __name__, url_prefix="/api/llm")


@llm_bp.route("/test_connection", methods=["GET"])
def test_connection():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return jsonify({"status": "error", "message": "DEEPSEEK_API_KEY 未配置"}), 400
    try:
        result = LLMClient(provider="deepseek").chat(
            [{"role": "user", "content": "请用一句话回答：1+1 等于几？"}],
            max_tokens=100,
        )
        return jsonify({"status": "ok", "message": "DeepSeek 连接成功", "response": result[:100]})
    except Exception as exc:
        return jsonify({"status": "warning", "message": "DeepSeek 调用失败", "error": str(exc)}), 502


@llm_bp.route("/recommend", methods=["POST"])
@token_required
def recommend():
    data = request.json or {}
    student = data.get("student") or {}
    top_n = int(data.get("top_n", 5))
    conn = get_db()
    try:
        jobs = [dict(r) for r in conn.execute("SELECT * FROM job").fetchall()]
    finally:
        conn.close()
    recs = career_ai_service.intelligent_recommendation(student, jobs, top_n)
    return jsonify({"results": recs})


@llm_bp.route("/generate_plan", methods=["POST"])
@token_required
def generate_plan():
    data = request.json or {}
    text = career_ai_service.generate_plan_suggestion(data.get("student") or {}, data.get("job_name") or "")
    return jsonify({"plan": text})


@llm_bp.route("/qa", methods=["POST"])
def qa():
    data = request.json or {}
    ans = career_ai_service.chat_qa(data.get("question", ""), data.get("context", ""))
    return jsonify({"answer": ans})
