import json
import math
import os

from flask import Blueprint, jsonify, request

from db import get_db
from services.career_ai_service import get_job_skills
from services.ml_recommender import build_job_profile as build_ml_job_profile, split_skills


job_bp = Blueprint("job", __name__, url_prefix="/api/jobs")


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _row_to_dict(row):
    return dict(row) if row else None


@job_bp.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT job_category AS name, COUNT(*) AS job_count
            FROM jobs
            WHERE job_category IS NOT NULL AND job_category != ''
            GROUP BY job_category
            ORDER BY job_category
            """
        ).fetchall()
    finally:
        conn.close()
    return jsonify([
        {
            "id": index + 1,
            "name": row["name"],
            "icon": "",
            "description": f"{row['name']}类岗位，共 {row['job_count']} 个",
            "job_count": row["job_count"],
            "skills": [],
            "certificates": [],
            "soft_abilities": {},
        }
        for index, row in enumerate(rows)
    ])


@job_bp.route("/<int:job_id>", methods=["GET"])
def get_job_detail(job_id):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT rowid as id, job_name, location, salary_range, company, industry,
                   company_size, company_type, job_code, job_description,
                   updated_at, company_info, source_url
            FROM job WHERE rowid = ?
            """,
            (job_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "岗位不存在"}), 404
    return jsonify(dict(row))


@job_bp.route("/profile/<path:job_name>", methods=["GET"])
def get_job_profile_by_name(job_name):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT rowid as id, job_name, location, salary_range, company, industry,
                   company_size, company_type, job_code, job_description,
                   updated_at, company_info, source_url
            FROM job WHERE job_name = ? LIMIT 1
            """,
            (job_name,),
        ).fetchone()
        if not row:
            return jsonify({"error": "岗位不存在"}), 404
        data = dict(row)
    finally:
        conn.close()
    return jsonify(data)


@job_bp.route("/graph", methods=["GET"])
def get_job_graph():
    conn = get_db()
    try:
        rows = conn.execute("SELECT from_job, to_job, relation_type, description FROM job_relations").fetchall()
    finally:
        conn.close()
    nodes = sorted({r["from_job"] for r in rows} | {r["to_job"] for r in rows})
    return jsonify({
        "nodes": [{"id": name, "label": name} for name in nodes],
        "edges": [dict(row) for row in rows],
    })


@job_bp.route("/industries", methods=["GET"])
def get_industries():
    conn = get_db()
    try:
        rows = conn.execute(
            'SELECT DISTINCT industry FROM job WHERE industry IS NOT NULL AND industry != "" ORDER BY industry'
        ).fetchall()
    finally:
        conn.close()
    return jsonify([row["industry"] for row in rows])


@job_bp.route("/search", methods=["GET"])
def search_jobs():
    page = max(1, request.args.get("page", 1, type=int))
    size = max(1, request.args.get("size", 10, type=int))
    keyword = request.args.get("keyword", "", type=str)
    industry = request.args.get("industry", "", type=str)
    company_size = request.args.get("company_size", "", type=str)
    order = request.args.get("order", "asc", type=str)

    conditions = []
    params = []
    if keyword:
        conditions.append("(job_name LIKE ? OR company LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if industry:
        conditions.append("industry = ?")
        params.append(industry)
    if company_size:
        conditions.append("company_size = ?")
        params.append(company_size)
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    order_sql = "ASC" if order.lower() == "asc" else "DESC"
    offset = (page - 1) * size

    conn = get_db()
    try:
        total = conn.execute(f"SELECT COUNT(*) AS total FROM job {where_clause}", params).fetchone()["total"]
        rows = conn.execute(
            f"""
            SELECT rowid as id, job_name, location, salary_range, company,
                   industry, company_size, company_type
            FROM job {where_clause}
            ORDER BY rowid {order_sql}
            LIMIT ? OFFSET ?
            """,
            params + [size, offset],
        ).fetchall()
    finally:
        conn.close()
    return jsonify({"total": total, "page": page, "size": size, "items": [dict(r) for r in rows]})


@job_bp.route("/simple_search", methods=["GET"])
def simple_search():
    keyword = request.args.get("keyword", "", type=str)
    page = max(1, request.args.get("page", 1, type=int))
    size = max(1, request.args.get("size", 10, type=int))
    offset = (page - 1) * size
    conn = get_db()
    try:
        if keyword:
            rows = conn.execute(
                """
                SELECT rowid as id, job_name, company, salary_range, location
                FROM job WHERE job_name LIKE ? OR company LIKE ?
                ORDER BY rowid LIMIT ? OFFSET ?
                """,
                (f"%{keyword}%", f"%{keyword}%", size, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT rowid as id, job_name, company, salary_range, location FROM job ORDER BY rowid LIMIT ? OFFSET ?",
                (size, offset),
            ).fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@job_bp.route("/<int:job_id>/profile", methods=["GET"])
def get_job_profile(job_id):
    conn = get_db()
    try:
        job = conn.execute(
            """
            SELECT
                job.rowid as id,
                job.job_name,
                job.industry,
                job.salary_range,
                job.job_description,
                job.company,
                jobs.job_id,
                jobs.job_title,
                jobs.job_category,
                jobs.company_name,
                jobs.salary_min,
                jobs.salary_max,
                jobs.salary_avg,
                jobs.skills,
                jobs.requirements
            FROM job
            LEFT JOIN jobs ON jobs.job_id = job.job_code
            WHERE job.rowid = ?
            """,
            (job_id,),
        ).fetchone()
        if not job:
            return jsonify({"error": "岗位不存在"}), 404
        existing = conn.execute(
            "SELECT skills, certificates, soft_abilities FROM job_profile WHERE job_name = ?",
            (job["job_name"],),
        ).fetchone()
        if existing:
            profile = {
                "job_name": job["job_name"],
                "skills": _json_loads(existing["skills"], []),
                "certificates": _json_loads(existing["certificates"], []),
                "soft_abilities": _json_loads(existing["soft_abilities"], {}),
                "category": job["job_category"] or job["industry"] or "",
                "source": "job_profile",
            }
        else:
            profile = build_ml_job_profile(dict(job))
            conn.execute(
                """
                INSERT OR REPLACE INTO job_profile (job_name, skills, certificates, soft_abilities)
                VALUES (?, ?, ?, ?)
                """,
                (
                    profile["job_name"],
                    json.dumps(profile["skills"], ensure_ascii=False),
                    json.dumps(profile["certificates"], ensure_ascii=False),
                    json.dumps(profile["soft_abilities"], ensure_ascii=False),
                ),
            )
            conn.commit()
    finally:
        conn.close()
    return jsonify(profile)


def _normalize_job_name(job_name):
    conn = get_db()
    try:
        row = conn.execute("SELECT job_name FROM job WHERE LOWER(job_name) = LOWER(?) LIMIT 1", (job_name,)).fetchone()
        if row:
            return row["job_name"]
        row = conn.execute("SELECT job_name FROM job WHERE LOWER(job_name) LIKE LOWER(?) LIMIT 1", (f"%{job_name}%",)).fetchone()
        return row["job_name"] if row else job_name
    finally:
        conn.close()


def _career_path(job_name):
    normalized = _normalize_job_name(job_name)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'promotion' ORDER BY id",
            (normalized,),
        ).fetchall()
    finally:
        conn.close()
    if rows:
        current = normalized
        path = []
        for row in rows:
            path.append({"from_job": current, "to_job": row["to_job"], "description": row["description"]})
            current = row["to_job"]
        return path
    return [
        {"from_job": normalized, "to_job": f"高级{normalized}", "description": f"深化岗位技能，承担复杂项目。"},
        {"from_job": f"高级{normalized}", "to_job": f"{normalized}专家", "description": "沉淀方法论并指导团队。"},
    ]


def _lateral_paths(job_name):
    normalized = _normalize_job_name(job_name)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'transition' ORDER BY id",
            (normalized,),
        ).fetchall()
        if rows:
            return [{"job_name": row["to_job"], "description": row["description"]} for row in rows]
        source = conn.execute("SELECT industry FROM job WHERE job_name = ? LIMIT 1", (normalized,)).fetchone()
        industry = source["industry"] if source else None
        peers = conn.execute(
            "SELECT DISTINCT job_name FROM job WHERE industry = ? AND job_name != ? LIMIT 3",
            (industry, normalized),
        ).fetchall() if industry else []
    finally:
        conn.close()
    return [
        {"job_name": row["job_name"], "description": f"同属{industry}方向，技能可迁移。"}
        for row in peers
    ] or [{"job_name": f"{normalized}顾问", "description": "适合向咨询和方案方向拓展。"}]


@job_bp.route("/<job_name>/full-path", methods=["GET"])
def get_full_career_path(job_name):
    normalized = _normalize_job_name(job_name)
    return jsonify({
        "success": True,
        "job_name": normalized,
        "vertical_path": _career_path(normalized),
        "lateral_paths": _lateral_paths(normalized),
    })


@job_bp.route("/<job_name>/vertical", methods=["GET"])
def get_vertical_path_simple(job_name):
    return jsonify(_career_path(job_name))


@job_bp.route("/<job_name>/lateral", methods=["GET"])
def get_lateral_path_simple(job_name):
    normalized = _normalize_job_name(job_name)
    return jsonify([
        {"to_job": item["job_name"], "description": item["description"]}
        for item in _lateral_paths(normalized)
    ])


@job_bp.route("/names", methods=["GET"])
def get_all_job_names():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT job_name FROM job WHERE job_name IS NOT NULL AND job_name != '' ORDER BY job_name"
        ).fetchall()
    finally:
        conn.close()
    return jsonify([row["job_name"] for row in rows])


@job_bp.route("/<int:job_id>/similar", methods=["GET"])
def get_similar_jobs(job_id):
    top_k = request.args.get("top_k", 10, type=int)
    conn = get_db()
    try:
        job = conn.execute("SELECT industry FROM job WHERE rowid = ?", (job_id,)).fetchone()
        if not job:
            return jsonify({"success": False, "error": "岗位不存在"}), 404
        rows = conn.execute(
            "SELECT rowid as job_id FROM job WHERE industry = ? AND rowid != ? LIMIT ?",
            (job["industry"], job_id, top_k),
        ).fetchall()
    finally:
        conn.close()
    return jsonify({
        "success": True,
        "data": [{"job_id": row["job_id"], "similarity": 0.8} for row in rows],
    })


@job_bp.route("/skills", methods=["POST"])
def predict_job_skills():
    data = request.get_json(silent=True) or {}
    text = data.get("job_description", "")
    if not text:
        return jsonify({"success": False, "error": "请提供 job_description"}), 400
    skills = build_ml_job_profile({"job_title": "", "job_description": text}).get("skills", [])
    return jsonify({
        "success": True,
        "data": [{"skill": skill, "probability": round(1.0 - i * 0.05, 4)} for i, skill in enumerate(skills[: data.get("top_k", 5)])],
    })
