from flask import Blueprint, jsonify, request

from routes.auth import token_required
from services import career_ai_service
from services import job_repository
from services.llm_client import LLMClient


llm_bp = Blueprint("llm", __name__, url_prefix="/api/llm")


@llm_bp.route("/test_connection", methods=["GET"])
def test_connection():
    client = LLMClient(provider=request.args.get("provider"))
    probe = [{"role": "user", "content": "请用一句话回答：1+1 等于几？"}]

    if client.is_local:
        result = client.chat(probe, max_tokens=100)
        return jsonify({
            "status": "ok",
            "provider": client.provider,
            "message": "Local fallback available",
            "response": result[:100],
        })

    try:
        result = client.test_remote(probe, max_tokens=100)
        return jsonify({
            "status": "ok",
            "provider": client.provider,
            "message": f"{client.provider} connection succeeded",
            "response": result[:100],
        })
    except Exception as exc:
        return jsonify({
            "status": "warning",
            "provider": client.provider,
            "message": f"{client.provider} call failed",
            "error": str(exc),
        }), 502


@llm_bp.route("/recommend", methods=["POST"])
@token_required
def recommend():
    data = request.json or {}
    student = data.get("student") or {}
    top_n = int(data.get("top_n", 5))
    jobs = job_repository.all_jobs()
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
