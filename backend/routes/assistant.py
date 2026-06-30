from flask import Blueprint, Response, jsonify, request, stream_with_context

from services.llm_client import LLMClient, chunk_text, sse_event


assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


def _messages(message: str, context) -> list:
    system = (
        "你是 Starway 大学生职业规划系统的智能助手。"
        "回答必须围绕求职方向、岗位匹配、技能提升、简历优化和学习路径。"
        "用户只要给出任何专业、年级、目标岗位、技能、经历或困惑，就必须直接作答。"
        "禁止把已经给出的信息说成信息不足；确实缺信息时，也要先基于现有信息给出可执行方案。"
        "禁止输出泛泛的 AI 概念解释或通用模板。"
    )
    ctx = f"\n用户背景：{context}" if context else ""
    user_prompt = f"""
用户原话：{message}
{ctx}

请直接给出职业规划建议，结构固定为：
1. 方向判断：引用用户原话中的专业、年级或目标岗位，判断目标是否合理，并给出相邻方向；
2. 三步行动：按 30/60/90 天拆解技能、作品、简历和面试准备；
3. 可验证成果：列出用户完成后应留下的作品、简历条目或证明材料。

不要说“信息不足”“无法判断”“请提供更多信息”。不要把用户的问题改写成通用职业规划。
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]


def _retry_messages(message: str, context) -> list:
    ctx = f"\n用户背景：{context}" if context else ""
    return [
        {
            "role": "system",
            "content": (
                "你是严格执行任务的大学生职业规划顾问。"
                "必须引用用户原话里的已知信息并直接生成路线。"
                "不要要求用户补充信息，不要输出通用模板。"
            ),
        },
        {
            "role": "user",
            "content": f"""
用户已给出的信息是：{message}
{ctx}

请重新回答，必须输出：
1. 方向判断；
2. 30/60/90 天三步行动；
3. 可验证成果。

如果用户提到“软件工程大四，想做数据分析师”，必须围绕“软件工程大四 -> 数据分析师”回答。
""",
        },
    ]


def _needs_retry(answer: str) -> bool:
    bad_phrases = [
        "信息不足",
        "无法判断",
        "无法准确判断",
        "请提供",
        "需要更多",
        "补充背景",
        "没有提供",
        "并未提供",
        "虽然您没有提供",
        "通用",
        "所有大学生",
        "职业探索启动方案",
        "只输入了问号",
        "直接套用",
        "零起点",
    ]
    head = (answer or "")[:500]
    return any(phrase in head for phrase in bad_phrases)


def _is_off_topic(message: str, answer: str) -> bool:
    source = message or ""
    result = answer or ""
    head = result[:1000]
    if "数据分析" in source and "数据分析" not in head:
        return True
    if "软件工程" in source and "软件工程" not in head:
        return True
    if "大四" in source and "大四" not in head:
        return True
    if any(item in source for item in ["三步", "计划", "规划", "怎么准备", "如何准备"]):
        if not any(item in result for item in ["30", "60", "90", "三步行动"]):
            return True
    return False


def _direct_plan_answer(message: str, context) -> str:
    text = f"{message} {context or ''}"
    target = "目标岗位"
    for marker in ["想做", "目标是", "应聘", "转"]:
        if marker in text:
            target = (
                text.split(marker, 1)[1]
                .split("，")[0]
                .split(",")[0]
                .split("。")[0]
                .strip()
                or target
            )
            break
    major = "当前专业"
    if "软件工程" in text:
        major = "软件工程"
    elif "计算机" in text:
        major = "计算机相关专业"
    grade = "当前阶段"
    for item in ["大一", "大二", "大三", "大四", "研一", "研二", "研三"]:
        if item in text:
            grade = item
            break
    return f"""1. 方向判断
你现在给出的关键信息是“{message}”。如果你是{major}{grade}，目标指向“{target}”，这个方向是合理的：软件工程背景可以迁移到数据分析里的 Python/SQL、数据处理、业务系统理解和自动化能力。相邻方向可以同时关注数据分析师、BI 分析师、数据运营、数据产品助理；如果你的代码基础更强，也可以保留数据开发或后端数据工程作为备选。

2. 三步行动
30 天：先补齐入门闭环。每天固定练 SQL 查询、Python pandas、Excel/可视化和基础统计，把 3 个真实岗位 JD 拆成技能清单。完成一个小项目，例如校园消费、招聘岗位或电商订单数据分析，产出清洗脚本、分析结论和图表。

60 天：做一份像样的作品集。选择一个更贴近业务的问题，例如用户增长、岗位薪资、留存转化或销售漏斗，完成“问题定义 -> 数据清洗 -> 指标体系 -> 可视化看板 -> 业务建议”。同时把项目整理成网页、Notebook 或 PDF 报告，准备 3 分钟讲解稿。

90 天：进入求职表达。简历里突出“{major} + {target}”的复合优势：会写脚本、懂数据库、能做可视化、能把分析落成工具。准备 SQL 高频题、统计指标解释、项目复盘和业务 case；投递时优先选择数据分析实习、BI、数据运营、数据产品助理。

3. 可验证成果
你至少要留下：1 个 GitHub/作品集链接、1 份数据分析报告、1 个可交互看板或图表页面、30 道 SQL 练习记录、1 份岗位 JD 拆解表、1 版针对“{target}”的简历。这样面试时就不是“我想做”，而是“我已经按这个岗位的方式做过一次”。"""


def _instant_career_answer(message: str, context) -> str:
    if _is_greeting_only(message):
        return (
            "你好，我在。你可以直接发我目标岗位、简历片段或当前困惑，"
            "我会把它拆成方向判断、30/60/90 天行动和可验证成果。"
        )
    return _direct_plan_answer(message, context)


def _should_answer_directly(message: str) -> bool:
    text = message or ""
    plan_markers = ["三步", "计划", "路径", "怎么做", "如何做", "怎么准备", "职业规划", "想做", "转行", "转岗"]
    target_markers = ["数据分析", "软件工程", "目标", "岗位", "实习", "求职"]
    return any(item in text for item in plan_markers) and any(item in text for item in target_markers)


def _is_greeting_only(message: str) -> bool:
    normalized = (
        (message or "")
        .strip()
        .lower()
        .replace(" ", "")
        .replace("!", "")
        .replace("！", "")
        .replace("。", "")
        .replace("，", "")
        .replace(",", "")
        .replace("?", "")
        .replace("？", "")
    )
    return normalized in {"你好", "您好", "嗨", "在吗", "在嘛", "哈喽", "hello", "hi"}


def _answer_with_quality_gate(message: str, context, provider: str):
    if _is_greeting_only(message):
        client = LLMClient(provider="local")
        client.used_fallback = False
        return _instant_career_answer(message, {}), client

    client = LLMClient(provider=provider, timeout=18)
    attempted = set()
    try:
        answer = client.chat_remote_only(_messages(message, context), max_tokens=1200)
        attempted.add(client.provider)
    except Exception:
        client.provider = "local"
        client.used_fallback = True
        return _direct_plan_answer(message, context), client

    if _needs_retry(answer) or _is_off_topic(message, answer):
        try:
            retry_answer = client.chat_remote_only(
                _retry_messages(message, context),
                max_tokens=1400,
                skip_providers=attempted,
            )
            if retry_answer:
                answer = retry_answer
                attempted.add(client.provider)
        except Exception:
            pass

    if _needs_retry(answer) or _is_off_topic(message, answer):
        try:
            backup_answer = client.chat_remote_only(
                _retry_messages(message, context),
                max_tokens=1400,
                skip_providers=attempted,
            )
            if backup_answer:
                answer = backup_answer
                attempted.add(client.provider)
        except Exception:
            pass

    if _needs_retry(answer) or _is_off_topic(message, answer):
        client.last_error = (client.last_error + " | " if client.last_error else "") + "remote answer quality warning"
    return answer, client


def _stream_answer(message: str, context, provider: str):
    if _is_greeting_only(message):
        client = LLMClient(provider="local")
        client.used_fallback = False
        answer = _instant_career_answer(message, {})
        for chunk in chunk_text(answer, size=40):
            yield chunk, client, False
        return

    client = LLMClient(provider=provider, timeout=18)
    chunks = []
    try:
        if not hasattr(client, "stream_chat"):
            answer = client.chat_remote_only(_messages(message, context), max_tokens=1200)
            for chunk in chunk_text(answer, size=40):
                chunks.append(chunk)
                yield chunk, client, False
            yield "", client, True
            return
        for chunk in client.stream_chat(_messages(message, context), temperature=0.3, max_tokens=1400):
            if not chunk:
                continue
            chunks.append(chunk)
            yield chunk, client, False
    except Exception:
        client.used_fallback = True
        client.provider = "local"
        chunks = []

    answer = "".join(chunks)
    if not answer or _needs_retry(answer) or _is_off_topic(message, answer):
        client.used_fallback = True
        fallback = _direct_plan_answer(message, context)
        if answer:
            yield "\n\n补充成可执行版本：\n", client, False
        for chunk in chunk_text(fallback, size=40):
            yield chunk, client, False
        client.provider = "local" if not answer else client.provider
    yield "", client, True


@assistant_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or data.get("question") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    provider = data.get("provider")
    stream = bool(data.get("stream", False))
    context = data.get("context") or {}

    if stream:
        def generate():
            try:
                yield sse_event("start", {"provider": provider or "default"})
                last_client = None
                for chunk, client, done in _stream_answer(message, context, provider):
                    last_client = client
                    if done:
                        yield sse_event("done", {
                            "provider": client.provider if client else provider,
                            "fallback": bool(client.used_fallback if client else False),
                            "error": client.last_error if client else "",
                        })
                    elif chunk:
                        yield sse_event("delta", {"content": chunk})
                if not last_client:
                    yield sse_event("done", {"provider": provider or "local", "fallback": True, "error": ""})
            except Exception as exc:
                fallback = _instant_career_answer(message, context)
                yield sse_event("delta", {"content": fallback})
                yield sse_event("done", {"provider": "local", "fallback": True, "error": str(exc)})

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    try:
        answer, client = _answer_with_quality_gate(message, context, provider)
        fallback = client.used_fallback or client.is_local
    except Exception as exc:
        client = LLMClient(provider="local")
        client.used_fallback = True
        client.last_error = str(exc)
        answer = _direct_plan_answer(message, context)
        fallback = True

    if _needs_retry(answer) or _is_off_topic(message, answer):
        client.last_error = (client.last_error + " | " if client.last_error else "") + "remote answer quality warning"
        fallback = client.used_fallback or client.is_local

    return jsonify({
        "answer": answer,
        "provider": client.provider,
        "usage": {"fallback": fallback, "error": client.last_error},
    })
