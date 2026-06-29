import json
import time

from flask import Blueprint, Response, jsonify, request, stream_with_context

from db import get_db
from routes.auth import token_required
from services.career_ai_service import call_llm
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


def compute_match(student_ability, job_ability, generate_gap=False, job_name=None):
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
    result["gap_analysis"] = generate_gap_analysis_with_llm(student_ability, job_ability, result) if generate_gap else {}
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


def generate_gap_analysis_with_llm(student_ability, job_ability, match_detail):
    _, _, missing_concepts = match_concepts(
        student_ability.get("skills", set()),
        job_ability.get("skills", set()),
        required_text=job_ability.get("job_description", ""),
    )
    need_skills = display_concepts(missing_concepts)
    prompt = f"""
请为大学生生成简洁的人岗匹配差距建议。
匹配分：{match_detail['overall_score']}
缺口技能：{', '.join(need_skills) if need_skills else '无明显缺口'}
请返回 JSON，字段为 base、skills、quality、potential、recommended_resources。
"""
    try:
        text = call_llm(prompt, temperature=0.4, max_tokens=800)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
    except Exception:
        pass
    return {
        "base": "保持学历与基础能力优势，结合目标岗位补充作品和经历证明。",
        "skills": "建议优先补齐：" + ("、".join(need_skills[:5]) if need_skills else "岗位核心技能的项目化表达"),
        "quality": "通过团队项目、复盘和汇报训练沟通协作与抗压能力。",
        "potential": "制定 3 个月技能补齐计划，并用项目成果沉淀简历亮点。",
        "recommended_resources": "官方文档、岗位相关开源项目、课程实战和模拟面试。",
    }


@match_bp.route("/recommend", methods=["GET"])
def recommend():
    student_id = request.args.get("student_id", type=int)
    limit = request.args.get("limit", 10, type=int)
    if student_id is None:
        return jsonify({"error": "缺少 student_id 参数"}), 400
    student = get_student_ability(student_id)
    if not student:
        return jsonify({"error": "学生不存在"}), 404
    if not student.get("skills"):
        return jsonify({"error": "学生能力数据不完整，请先完善技能信息"}), 400

    results = []
    for row in job_repository.all_jobs():
        job_name = row["job_name"]
        detail = compute_match(student, get_job_abilities(job_name), generate_gap=False, job_name=job_name)
        results.append({"job_name": job_name, **detail})
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
    if not student.get("skills"):
        return jsonify({"error": "学生能力数据不完整，请先完善技能信息"}), 400
    detail = compute_match(student, get_job_abilities(job_name), generate_gap=True, job_name=job_name)
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
    base_detail = compute_match(student, get_job_abilities(job_name), generate_gap=False, job_name=job_name)

    def generate():
        yield f"data: {json.dumps({'type': 'base', 'data': base_detail}, ensure_ascii=False)}\n\n"
        gap = generate_gap_analysis_with_llm(student, get_job_abilities(job_name), base_detail)
        for key, value in gap.items():
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
