from flask import Blueprint, Response, jsonify, request, stream_with_context

from services.llm_client import LLMClient, chunk_text, sse_event


assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


def _clean_ai_text(value: str) -> str:
    text = str(value or "")
    text = text.replace("**", "").replace("*", "")
    text = text.replace("您好", "你好").replace("您的", "你的").replace("您", "你")
    return text


def _messages(message: str, context) -> list:
    system = (
        "你是 Starway 大学生职业规划系统的智能助手。"
        "你是万能型职业与学习 AI 助手，可以回答职业规划、岗位选择、简历优化、项目设计、学习路径、面试准备、报告解读、情绪困惑和具体执行问题。"
        "如果上下文里有报告或学生画像，要主动分析其中的关键信息；但回答不能被报告限制，用户问什么就答什么。"
        "用户只要给出任何专业、年级、目标岗位、技能、经历、报告片段或困惑，就必须直接作答。"
        "禁止把已经给出的信息说成信息不足；确实缺信息时，也要先基于现有信息给出可执行方案。"
        "禁止输出泛泛的 AI 概念解释或通用模板。禁止输出 Markdown 星号、粗体符号和星号项目符号。"
    )
    ctx = f"\n用户背景：{context}" if context else ""
    user_prompt = f"""
用户原话：{message}
{ctx}

请直接回答用户问题，并根据问题类型灵活组织：
1. 如果是方向/岗位/报告问题，先给判断，再说明依据；
2. 如果是学习/求职/面试问题，给具体步骤、优先级和可验证成果；
3. 如果是开放困惑，给利弊分析、选择标准和下一步动作。

不要说“信息不足”“无法判断”“请提供更多信息”。不要把用户的问题改写成通用职业规划。
不要输出 * 或 **，直接用普通中文段落和编号。
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
        "很抱歉",
        "抱歉",
        "对不起",
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
    role_focus = _target_role_focus(target)
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
你现在给出的关键信息是“{message}”。如果你是{major}{grade}，目标指向“{target}”，这个方向可以推进，但不要只停留在“想做”。你需要把已有课程、项目、技能和岗位真实要求对齐起来，重点证明自己能完成{role_focus["core_task"]}。相邻方向可以同时关注{role_focus["adjacent"]}，这样投递时不会被单一岗位卡住。

2. 三步行动
30 天：先补齐入门闭环。收集 15 到 20 条“{target}”相关 JD，统计高频技能、常见任务、工具和作品要求；每天固定练 1 个核心技能点，优先处理{role_focus["skills"]}。同时完成一个小练习，产出能截图、能复盘、能放进简历的材料。

60 天：做一份像样的作品集。围绕“{target}”选择一个贴近真实业务的项目，按“问题定义 -> 方案设计 -> 执行过程 -> 结果展示 -> 复盘改进”整理。项目不一定很大，但必须体现{role_focus["project_value"]}，并准备 3 分钟讲解稿。

90 天：进入求职表达。简历里突出“{major} + {target}”的复合优势：你用什么工具、解决什么问题、交付什么结果。准备岗位高频面试题、项目复盘、作品演示和自我介绍；投递时每周记录投递数量、回复率、面试卡点和简历修改点。

3. 可验证成果
你至少要留下：1 份岗位 JD 拆解表、1 个贴近“{target}”的作品或案例、1 版针对该岗位的简历、1 份项目讲解稿、1 张技能差距清单、1 份投递复盘表。这样面试时就不是“我想做”，而是“我已经按这个岗位的方式做过一次”。"""


def _target_role_focus(target: str) -> dict:
    text = str(target or "")
    if any(word in text for word in ["前端", "Vue", "React", "Web"]):
        return {
            "core_task": "页面交互、组件复用、接口联调、响应式布局和性能体验优化",
            "adjacent": "前端开发实习、Web 开发、低代码平台开发、测试开发、产品技术支持",
            "skills": "HTML/CSS、JavaScript、Vue 或 React、组件化、接口请求、Git 和基础工程化",
            "project_value": "真实页面、可复用组件、接口数据流、异常状态、移动端适配和部署链接",
        }
    if any(word in text for word in ["数据", "分析", "BI"]):
        return {
            "core_task": "数据清洗、指标拆解、可视化分析和业务建议输出",
            "adjacent": "数据分析师、BI 分析师、数据运营、数据产品助理",
            "skills": "SQL、Python pandas、Excel、可视化、基础统计和业务指标",
            "project_value": "指标体系、清洗过程、图表结论、业务建议和可复现数据处理流程",
        }
    if any(word in text for word in ["后端", "Java", "Python", "服务端"]):
        return {
            "core_task": "接口设计、数据模型、鉴权、异常处理、日志和部署联调",
            "adjacent": "后端开发、Java 开发、Python 开发、测试开发、运维开发",
            "skills": "一门后端语言、数据库、HTTP/API、缓存、测试、Git 和部署",
            "project_value": "可运行接口、数据库表设计、接口文档、测试记录和部署说明",
        }
    return {
        "core_task": "岗位要求中的关键任务，并用作品或经历证明交付能力",
        "adjacent": "同类初级岗位、实习岗位、助理岗位和技能相邻方向",
        "skills": "岗位 JD 中出现频率最高的 2 到 3 项技能",
        "project_value": "真实问题、执行过程、结果证据和可复盘改进",
    }


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

    client = LLMClient(provider=provider, timeout=12)
    attempted = set()
    try:
        answer = client.chat_remote_only(_messages(message, context), max_tokens=700)
        attempted.add(client.provider)
    except Exception:
        client.provider = "local"
        client.used_fallback = True
        return _direct_plan_answer(message, context), client

    if _needs_retry(answer) or _is_off_topic(message, answer):
        try:
            retry_answer = client.chat_remote_only(
                _retry_messages(message, context),
                max_tokens=760,
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
                max_tokens=760,
                skip_providers=attempted,
            )
            if backup_answer:
                answer = backup_answer
                attempted.add(client.provider)
        except Exception:
            pass

    if _needs_retry(answer) or _is_off_topic(message, answer):
        client.last_error = (client.last_error + " | " if client.last_error else "") + "remote answer quality warning"
    return _clean_ai_text(answer), client


def _stream_answer(message: str, context, provider: str):
    if _is_greeting_only(message):
        client = LLMClient(provider="local")
        client.used_fallback = False
        answer = _instant_career_answer(message, {})
        for chunk in chunk_text(_clean_ai_text(answer), size=32):
            yield chunk, client, False
        return

    client = LLMClient(provider=provider, timeout=12)
    chunks = []
    released_head = False
    yield "我先基于你给的信息开始分析，马上给你可执行建议。\n\n", client, False
    try:
        if not hasattr(client, "stream_chat"):
            answer = client.chat_remote_only(_messages(message, context), max_tokens=700)
            for chunk in chunk_text(_clean_ai_text(answer), size=32):
                chunks.append(chunk)
                yield chunk, client, False
            yield "", client, True
            return
        for chunk in client.stream_chat(_messages(message, context), temperature=0.3, max_tokens=700):
            if not chunk:
                continue
            clean_chunk = _clean_ai_text(chunk)
            chunks.append(clean_chunk)
            if not released_head:
                head = "".join(chunks)
                if _needs_retry(head):
                    chunks = []
                    break
                if len(head) < 36 and "\n" not in head and "。" not in head and "：" not in head:
                    continue
                released_head = True
                yield head, client, False
                continue
            yield clean_chunk, client, False
    except Exception:
        client.used_fallback = True
        client.provider = "local"
        chunks = []

    answer = "".join(chunks)
    if answer and not released_head and not _needs_retry(answer) and not _is_off_topic(message, answer):
        yield answer, client, False
    if not answer or _needs_retry(answer) or _is_off_topic(message, answer):
        client.used_fallback = True
        fallback = _clean_ai_text(_direct_plan_answer(message, context))
        if answer:
            yield "\n\n补充成可执行版本：\n", client, False
        for chunk in chunk_text(fallback, size=32):
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
                fallback = _clean_ai_text(_instant_career_answer(message, context))
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
        answer = _clean_ai_text(_direct_plan_answer(message, context))
        fallback = True

    if _needs_retry(answer) or _is_off_topic(message, answer):
        client.last_error = (client.last_error + " | " if client.last_error else "") + "remote answer quality warning"
        fallback = client.used_fallback or client.is_local

    return jsonify({
        "answer": _clean_ai_text(answer),
        "provider": client.provider,
        "usage": {"fallback": fallback, "error": client.last_error},
    })
