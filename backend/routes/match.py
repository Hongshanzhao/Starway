import json
import time

from flask import Blueprint, Response, jsonify, request, stream_with_context

from db import get_db
from routes.auth import token_required
from services.career_ai_service import call_llm, call_llm_stream
from services import job_repository
from services.ml_recommender import build_job_profile
from services.skill_normalizer import display_concepts, match_concepts


match_bp = Blueprint("match", __name__, url_prefix="/api/match")


def _load_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def get_student_ability(student_id):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT id, user_id, name, major, grade, skills, certificates,
                   soft_abilities, internships, education_json, work_json, project_json
            FROM student WHERE id = ?
            """,
            (student_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "major": row["major"] or "",
            "grade": row["grade"] or "",
            "skills": set(_load_json(row["skills"], [])),
            "certificates": set(_load_json(row["certificates"], [])),
            "soft_abilities": _load_json(row["soft_abilities"], {}),
            "internships": row["internships"] or "",
            "education_json": _load_json(row["education_json"], {}),
            "work_json": _load_json(row["work_json"], []),
            "project_json": _load_json(row["project_json"], []),
        }
    finally:
        conn.close()


def get_job_abilities(job_name):
    conn = get_db()
    try:
        profile = conn.execute(
            "SELECT skills, certificates, soft_abilities FROM job_profile WHERE job_name = ?",
            (job_name,),
        ).fetchone()
        job = job_repository.get_job_by_name(job_name)
        if profile:
            return {
                "skills": set(_load_json(profile["skills"], [])),
                "certificates": set(_load_json(profile["certificates"], [])),
                "soft_abilities": _load_json(profile["soft_abilities"], {}),
                "job_description": job["job_description"] if job else "",
            }
        if job:
            generated = build_job_profile(job)
            return {
                "skills": set(generated["skills"]),
                "certificates": set(generated["certificates"]),
                "soft_abilities": generated["soft_abilities"],
                "job_description": job["job_description"] or "",
            }
        return {"skills": set(), "certificates": set(), "soft_abilities": {}, "job_description": ""}
    finally:
        conn.close()


def _job_abilities_from_row(row):
    generated = build_job_profile(row)
    return {
        "skills": set(generated["skills"]),
        "certificates": set(generated["certificates"]),
        "soft_abilities": generated["soft_abilities"],
        "job_description": row.get("job_description") or "",
    }


def compute_match(student_ability, job_ability, generate_gap=False, job_name=None, use_llm_gap=True):
    required_concepts, overlap, missing_concepts = match_concepts(
        student_ability.get("skills", set()),
        job_ability.get("skills", set()),
        required_text=job_ability.get("job_description", ""),
    )
    skill_fit = len(overlap) / len(required_concepts) if required_concepts else 0.0

    student_certs = {s.lower() for s in student_ability.get("certificates", set())}
    job_certs = {s.lower() for s in job_ability.get("certificates", set())}
    cert_coverage = len(student_certs & job_certs) / len(job_certs) if job_certs else 0.0

    soft_score = _soft_similarity(student_ability.get("soft_abilities", {}), job_ability.get("soft_abilities", {}))
    education_score = 80.0 if student_ability.get("grade") or student_ability.get("education_json") else 60.0
    experience_score = 75.0 if student_ability.get("internships") or student_ability.get("work_json") else 45.0
    overall = 0.55 * skill_fit + 0.15 * cert_coverage + 0.15 * soft_score + 0.08 * (education_score / 100) + 0.07 * (experience_score / 100)

    result = {
        "overall_score": round(overall * 100, 1),
        "dl_score": None,
        "skill_fit": round(skill_fit * 100, 1),
        "soft_gap": round((1 - soft_score) * 100, 1),
        "cert_coverage": round(cert_coverage * 100, 1),
        "education_score": round(education_score, 1),
        "experience_score": round(experience_score, 1),
        "debug_info": {
            "matched_skills": sorted(overlap),
            "required_skills": sorted(required_concepts),
            "missing_skills": sorted(missing_concepts),
        },
    }
    result["gap_analysis"] = generate_gap_analysis_with_llm(
        student_ability,
        job_ability,
        result,
        use_llm=use_llm_gap,
    ) if generate_gap else {}
    return result


def _soft_similarity(student_soft, job_soft):
    if not job_soft:
        return 0.6
    scores = []
    for key, required in job_soft.items():
        required_score = required.get("score", 3) if isinstance(required, dict) else required
        student_val = student_soft.get(key, {})
        student_score = student_val.get("score", 3) if isinstance(student_val, dict) else student_val or 3
        scores.append(min(float(student_score), float(required_score)) / max(float(required_score), 1.0))
    return sum(scores) / len(scores) if scores else 0.6


def _fallback_gap_analysis(student_ability, job_ability, match_detail, need_skills=None):
    need_skills = need_skills if need_skills is not None else []
    return {
        "base": f"当前综合匹配度为 {match_detail['overall_score']}%。这个分数不只是“能不能投”的判断，更像是一张成长地图：你已经具备学历、基础学习能力和部分通用素养，可以从目标岗位的真实职责出发，把已有经历重新组织成岗位语言。若画像信息还不完整，建议先补充教育、项目、实习和技能证书，系统会给出更精准的排序。",
        "skills": "技能补齐建议优先按“岗位高频要求 -> 能快速做出作品 -> 面试可讲清楚”的顺序推进。" + (
            "当前建议先补齐 " + "、".join(need_skills[:6]) + "。每个技能不要只停留在课程学习，最好配一个小作品：例如接口服务、数据看板、自动化脚本、部署记录或性能优化笔记。"
            if need_skills else
            "当前没有明显技能缺口，下一步重点不是继续堆技能，而是把已有技能做成可展示作品，并在简历中写清问题、方案、指标和结果。"
        ),
        "quality": "职业素养方面，建议围绕沟通表达、任务拆解、复盘能力和抗压推进来补强。可以每周做一次项目周报，把目标、完成内容、遇到的问题、下一步计划写清楚；这类训练会直接提升面试表达质量，也能让团队协作经历更可信。",
        "potential": "30 天内完成岗位要求拆解和一份技能清单，选 2 个最关键技能集中突破；60 天内完成一个贴近目标岗位的小项目，并记录从需求到上线或交付的过程；90 天内把项目整理成简历亮点、作品集和面试讲稿。这个节奏能把“想做某岗位”变成“我已经按岗位方式做过一次”。",
        "recommended_resources": "资源建议优先选择官方文档、岗位 JD 高频关键词、开源项目 issue、课程实战和模拟面试。学习时保留证据：代码仓库、接口文档、数据分析报告、截图、部署链接、复盘文档。面试准备时用 STAR 法组织经历，并准备一页纸说明你为什么适合这个岗位。",
    }


def generate_gap_analysis_with_llm(student_ability, job_ability, match_detail, use_llm=True):
    _, _, missing_concepts = match_concepts(
        student_ability.get("skills", set()),
        job_ability.get("skills", set()),
        required_text=job_ability.get("job_description", ""),
    )
    need_skills = display_concepts(missing_concepts)
    if not use_llm:
        return _fallback_gap_analysis(student_ability, job_ability, match_detail, need_skills)
    prompt = f"""
你是 Starway 大学生职业规划系统的人岗匹配 AI 顾问。请生成详细、鼓励、可执行的人岗匹配分析。
学生能力：{json.dumps(student_ability, ensure_ascii=False, default=list)}
岗位能力：{json.dumps(job_ability, ensure_ascii=False, default=list)}
匹配详情：{json.dumps(match_detail, ensure_ascii=False)}
缺口技能：{', '.join(need_skills) if need_skills else '无明显缺口'}
请只返回 JSON，字段为：
base：基础匹配判断，至少 120 字；
skills：技能差距与补齐顺序，至少 180 字；
quality：职业素养、沟通、抗压、协作建议，至少 120 字；
potential：成长潜力和 30/60/90 天行动节奏，至少 180 字；
recommended_resources：推荐资源、项目作品和面试准备清单，至少 160 字。
"""
    try:
        text = call_llm(prompt, temperature=0.4, max_tokens=800)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
    except Exception:
        pass
    return _fallback_gap_analysis(student_ability, job_ability, match_detail, need_skills)


def _gap_prompt(student_ability, job_ability, match_detail, need_skills):
    return f"""
你是 Starway 大学生职业规划系统的人岗匹配 AI 顾问。请生成详细、鼓励、可执行的人岗匹配分析。
学生能力：{json.dumps(student_ability, ensure_ascii=False, default=list)}
岗位能力：{json.dumps(job_ability, ensure_ascii=False, default=list)}
匹配详情：{json.dumps(match_detail, ensure_ascii=False)}
缺口技能：{', '.join(need_skills) if need_skills else '无明显缺口'}
请只返回 JSON，字段为：
base：基础匹配判断，至少 120 字；
skills：技能差距与补齐顺序，至少 180 字；
quality：职业素养、沟通、抗压、协作建议，至少 120 字；
potential：成长潜力和 30/60/90 天行动节奏，至少 180 字；
recommended_resources：推荐资源、项目作品和面试准备清单，至少 160 字。
"""


def _gap_stream_prompt(student_ability, job_ability, match_detail, need_skills, job_name):
    return f"""
你是 Starway 人岗匹配顾问。请用普通中文自然语言，实时写给学生一段有行动价值的人岗匹配分析。
不要输出 JSON，不要 Markdown，不要使用 #、**、```。

目标岗位：{job_name}
学生能力：{json.dumps(student_ability, ensure_ascii=False, default=list)}
岗位能力：{json.dumps(job_ability, ensure_ascii=False, default=list)}
匹配详情：{json.dumps(match_detail, ensure_ascii=False)}
缺口技能：{', '.join(need_skills) if need_skills else '无明显缺口'}

请按这四段输出：
一、当前匹配意味着什么；
二、最该先补的技能和作品证据；
三、30/60/90 天行动节奏；
四、简历和面试如何表达。
每段都要结合匹配分、已匹配技能或缺口技能，不要泛泛鼓励。
"""


def _extract_gap_json(text, fallback):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end + 1])
            return {**fallback, **{k: v for k, v in parsed.items() if isinstance(v, str) and v.strip()}}
    except Exception:
        pass
    return fallback


@match_bp.route("/recommend", methods=["GET"])
def recommend():
    student_id = request.args.get("student_id", type=int)
    limit = request.args.get("limit", 10, type=int)
    if student_id is None:
        return jsonify({"error": "缺少 student_id 参数"}), 400
    student = get_student_ability(student_id)
    if not student:
        return jsonify({"error": "学生不存在"}), 404

    results = []
    for row in job_repository.all_jobs():
        job_name = row["job_name"]
        detail = compute_match(student, _job_abilities_from_row(row), generate_gap=False, job_name=job_name)
        results.append({**row, **detail, "job_name": job_name})
    results.sort(key=lambda item: item["overall_score"], reverse=True)
    return jsonify({"results": results[:limit], "total": len(results)})


@match_bp.route("/match", methods=["POST"])
def match():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    job_name = data.get("job_name")
    if not student_id or not job_name:
        return jsonify({"error": "缺少参数"}), 400
    student = get_student_ability(student_id)
    if not student:
        return jsonify({"error": "学生不存在"}), 404
    detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name, use_llm_gap=False)
    _save_match_history(student_id, job_name, detail)
    return jsonify(detail)


@match_bp.route("/history/<int:student_id>", methods=["GET"])
@token_required
def get_match_history(student_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, job_name, match_score, details, created_at FROM match_history WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        ).fetchall()
    finally:
        conn.close()
    return jsonify({"history": [dict(row) for row in rows]})


@match_bp.route("/match-stream", methods=["POST"])
def match_stream():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    job_name = data.get("job_name")
    if not student_id or not job_name:
        return jsonify({"error": "缺少参数"}), 400
    student = get_student_ability(student_id)
    if not student:
        return jsonify({"error": "学生不存在"}), 404
    job_ability = get_job_abilities(job_name)
    base_detail = compute_match(student, job_ability, generate_gap=False, job_name=job_name)
    _, _, missing_concepts = match_concepts(
        student.get("skills", set()),
        job_ability.get("skills", set()),
        required_text=job_ability.get("job_description", ""),
    )
    need_skills = display_concepts(missing_concepts)
    fallback_gap = _fallback_gap_analysis(student, job_ability, base_detail, need_skills)
    prompt = _gap_prompt(student, job_ability, base_detail, need_skills)
    stream_prompt = _gap_stream_prompt(student, job_ability, base_detail, need_skills, job_name)

    def generate():
        yield f"data: {json.dumps({'type': 'base', 'data': base_detail}, ensure_ascii=False)}\n\n"
        json_chunks = []
        try:
            yield f"data: {json.dumps({'type': 'gap', 'field': 'base', 'text': fallback_gap['base']}, ensure_ascii=False)}\n\n"
            for chunk in call_llm_stream(stream_prompt, temperature=0.45, max_tokens=1100):
                if chunk:
                    yield f"data: {json.dumps({'type': 'gap_stream', 'field': 'ai', 'text': chunk}, ensure_ascii=False)}\n\n"
            for chunk in call_llm_stream(prompt, temperature=0.3, max_tokens=900):
                if chunk:
                    json_chunks.append(chunk)
            gap = _extract_gap_json(''.join(json_chunks), fallback_gap)
        except Exception:
            gap = fallback_gap
        for key, value in gap.items():
            if key == "base":
                continue
            yield f"data: {json.dumps({'type': 'gap', 'field': key, 'text': value}, ensure_ascii=False)}\n\n"
        base_detail["gap_analysis"] = gap
        _save_match_history(student_id, job_name, base_detail)
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


def _save_match_history(student_id, job_name, detail):
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO match_history (student_id, job_name, match_score, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, job_name, detail["overall_score"], json.dumps(detail, ensure_ascii=False), int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()
