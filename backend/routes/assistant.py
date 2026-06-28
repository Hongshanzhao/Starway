from flask import Blueprint, Response, jsonify, request, stream_with_context

from services.llm_client import LLMClient, local_answer, sse_event


assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


def _messages(message: str, context) -> list:
    system = (
        "你是 Starway 大学生职业规划系统的智能助手。"
        "回答要围绕求职方向、岗位匹配、技能提升、简历优化和学习路径，"
        "给出务实、可执行、适合大学生的建议。"
    )
    ctx = f"\n用户背景：{context}" if context else ""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{message}{ctx}"},
    ]


@assistant_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or data.get("question") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    provider = data.get("provider")
    stream = bool(data.get("stream", False))
    context = data.get("context") or {}
    client = LLMClient(provider=provider)
    messages = _messages(message, context)

    if stream:
        def generate():
            yield sse_event("start", {"provider": client.provider})
            try:
                for chunk in client.stream_chat(messages, max_tokens=1200):
                    if chunk:
                        yield sse_event("delta", {"content": chunk})
                yield sse_event("done", {})
            except Exception as exc:
                fallback = local_answer(messages)
                yield sse_event("delta", {"content": fallback})
                yield sse_event("done", {"fallback": True, "error": str(exc)})

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    try:
        answer = client.chat(messages, max_tokens=1200)
        fallback = client.is_local
    except Exception as exc:
        answer = local_answer(messages)
        fallback = True
    return jsonify({
        "answer": answer,
        "provider": client.provider,
        "usage": {"fallback": fallback},
    })
