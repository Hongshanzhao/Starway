import json
import re

from flask import Blueprint, jsonify, request

from db import get_db
from services import job_ml_service
from services.ml_recommender import build_job_profile as build_ml_job_profile


job_bp = Blueprint("job", __name__, url_prefix="/api/jobs")


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _tokens(value):
    text = str(value or "")
    return {
        item.strip().lower()
        for item in re.split(r"[,，、\s;/|]+", text)
        if len(item.strip()) > 1
    }


def _job_tokens(row):
    if not row:
        return set()
    return _tokens(" ".join([
        str(row["job_name"] if "job_name" in row.keys() else ""),
        str(row["industry"] if "industry" in row.keys() else ""),
        str(row["job_description"] if "job_description" in row.keys() else ""),
    ]))


def _salary_midpoint(value):
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", str(value or ""))]
    if not numbers:
        return 0.0
    if len(numbers) == 1:
        return numbers[0]
    return (numbers[0] + numbers[1]) / 2


def _similarity_score(source, target):
    source_tokens = _job_tokens(source)
    target_tokens = _job_tokens(target)
    union = source_tokens | target_tokens
    skill_score = len(source_tokens & target_tokens) / len(union) if union else 0.0
    industry_score = 1.0 if source["industry"] and source["industry"] == target["industry"] else 0.0

    source_salary = _salary_midpoint(source["salary_range"] if "salary_range" in source.keys() else "")
    target_salary = _salary_midpoint(target["salary_range"] if "salary_range" in target.keys() else "")
    if source_salary and target_salary:
        salary_score = 1 - min(abs(source_salary - target_salary) / max(source_salary, target_salary), 1)
    else:
        salary_score = 0.5

    return round(0.65 * skill_score + 0.25 * industry_score + 0.10 * salary_score, 4)


def _job_row_by_name(job_name):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT rowid AS id, job_name, industry, salary_range, job_description
            FROM job
            WHERE LOWER(job_name) = LOWER(?)
            LIMIT 1
            """,
            (job_name,),
        ).fetchone()
        if row:
            return row
        return conn.execute(
            """
            SELECT rowid AS id, job_name, industry, salary_range, job_description
            FROM job
            WHERE LOWER(job_name) LIKE LOWER(?)
            LIMIT 1
            """,
            (f"%{job_name}%",),
        ).fetchone()
    finally:
        conn.close()


def _normalize_job_name(job_name):
    row = _job_row_by_name(job_name)
    return row["job_name"] if row else job_name


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
            SELECT rowid AS id, job_name, location, salary_range, company, industry,
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
            SELECT rowid AS id, job_name, location, salary_range, company, industry,
                   company_size, company_type, job_code, job_description,
                   updated_at, company_info, source_url
            FROM job WHERE job_name = ? LIMIT 1
            """,
            (job_name,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "岗位不存在"}), 404
    return jsonify(dict(row))


@job_bp.route("/graph", methods=["GET"])
def get_job_graph():
    conn = get_db()
    try:
        rows = conn.execute("SELECT from_job, to_job, relation_type, description FROM job_relations").fetchall()
    finally:
        conn.close()
    nodes = sorted({row["from_job"] for row in rows} | {row["to_job"] for row in rows})
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
        conditions.append("(job_name LIKE ? OR company LIKE ? OR job_description LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
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
            SELECT rowid AS id, job_name, location, salary_range, company,
                   industry, company_size, company_type
            FROM job {where_clause}
            ORDER BY rowid {order_sql}
            LIMIT ? OFFSET ?
            """,
            params + [size, offset],
        ).fetchall()
    finally:
        conn.close()
    return jsonify({"total": total, "page": page, "size": size, "items": [dict(row) for row in rows]})


@job_bp.route("/simple_search", methods=["GET"])
def simple_search():
    keyword = request.args.get("keyword", "", type=str)
    page = max(1, request.args.get("page", 1, type=int))
    size = max(1, request.args.get("size", 10, type=int))
    offset = (page - 1) * size
    condition = "WHERE job_name LIKE ? OR company LIKE ?" if keyword else ""
    params = [f"%{keyword}%", f"%{keyword}%"] if keyword else []

    conn = get_db()
    try:
        rows = conn.execute(
            f"""
            SELECT rowid AS id, job_name, company, salary_range, location
            FROM job {condition}
            ORDER BY rowid
            LIMIT ? OFFSET ?
            """,
            params + [size, offset],
        ).fetchall()
    finally:
        conn.close()
    return jsonify([dict(row) for row in rows])


@job_bp.route("/<int:job_id>/profile", methods=["GET"])
def get_job_profile(job_id):
    conn = get_db()
    try:
        job = conn.execute(
            """
            SELECT
                job.rowid AS id,
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


def _career_path(job_name):
    normalized = _normalize_job_name(job_name)
    source = None
    model_source = "rules"
    conn = get_db()
    try:
        stored = conn.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'promotion' ORDER BY id",
            (normalized,),
        ).fetchall()
        if stored:
            current = normalized
            path = []
            for row in stored:
                path.append({"from_job": current, "to_job": row["to_job"], "description": row["description"]})
                current = row["to_job"]
            return path

        source = conn.execute(
            "SELECT rowid AS id, job_name, industry, salary_range, job_description FROM job WHERE job_name = ? LIMIT 1",
            (normalized,),
        ).fetchone()
        peers = conn.execute(
            """
            SELECT rowid AS id, job_name, industry, salary_range, job_description
            FROM job
            WHERE industry = ? AND job_name != ?
            """,
            (source["industry"], normalized),
        ).fetchall() if source else []
    finally:
        conn.close()

    word2vec_ranked = job_ml_service.rank_rows_with_word2vec(source["id"], peers) if source else None
    if word2vec_ranked:
        ranked = [item[0] for item in sorted(
            word2vec_ranked,
            key=lambda item: (_salary_midpoint(item[0]["salary_range"]), item[1]),
            reverse=True,
        )]
        model_source = "word2vec"
    else:
        ranked = sorted(
            peers,
            key=lambda row: (_salary_midpoint(row["salary_range"]), _similarity_score(source, row)),
            reverse=True,
        )
    path = []
    current = normalized
    for row in ranked[:2]:
        path.append({
            "from_job": current,
            "to_job": row["job_name"],
            "description": (
                "基于 Word2Vec 岗位向量、同赛道和薪资区间推导的纵向发展方向。"
                if model_source == "word2vec"
                else "基于同赛道、薪资区间和技能丰富度推导的纵向发展方向。"
            ),
        })
        current = row["job_name"]
    return path, model_source


def _lateral_paths(job_name):
    normalized = _normalize_job_name(job_name)
    source = None
    model_source = "rules"
    conn = get_db()
    try:
        stored = conn.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'transition' ORDER BY id",
            (normalized,),
        ).fetchall()
        if stored:
            return [{"job_name": row["to_job"], "description": row["description"]} for row in stored]

        source = conn.execute(
            "SELECT rowid AS id, job_name, industry, salary_range, job_description FROM job WHERE job_name = ? LIMIT 1",
            (normalized,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT rowid AS id, job_name, industry, salary_range, job_description
            FROM job
            WHERE job_name != ?
            """,
            (normalized,),
        ).fetchall() if source else []
    finally:
        conn.close()

    cross_track = [row for row in rows if row["industry"] != source["industry"]]
    word2vec_ranked = job_ml_service.rank_rows_with_word2vec(source["id"], cross_track) if source else None
    if word2vec_ranked:
        ranked_with_scores = word2vec_ranked
        model_source = "word2vec"
    else:
        ranked_with_scores = [
            (row, _similarity_score(source, row))
            for row in sorted(cross_track, key=lambda row: _similarity_score(source, row), reverse=True)
        ]
    return [
        {
            "job_name": row["job_name"],
            "description": (
                "基于 Word2Vec 岗位向量相似度推导的横向转岗方向，可进一步补齐行业知识和项目作品。"
                if model_source == "word2vec"
                else "基于技能交集推导的横向转岗方向，可进一步补齐行业知识和项目作品。"
            ),
        }
        for row, score in ranked_with_scores[:3]
        if score > 0
    ], model_source


@job_bp.route("/<job_name>/full-path", methods=["GET"])
def get_full_career_path(job_name):
    normalized = _normalize_job_name(job_name)
    vertical_path, vertical_source = _career_path(normalized)
    lateral_paths, lateral_source = _lateral_paths(normalized)
    model_source = "word2vec" if "word2vec" in {vertical_source, lateral_source} else "rules"
    return jsonify({
        "success": True,
        "job_name": normalized,
        "vertical_path": vertical_path,
        "lateral_paths": lateral_paths,
        "model_source": model_source,
    })


@job_bp.route("/<job_name>/vertical", methods=["GET"])
def get_vertical_path_simple(job_name):
    path, _ = _career_path(job_name)
    return jsonify(path)


@job_bp.route("/<job_name>/lateral", methods=["GET"])
def get_lateral_path_simple(job_name):
    normalized = _normalize_job_name(job_name)
    paths, _ = _lateral_paths(normalized)
    return jsonify([
        {"to_job": item["job_name"], "description": item["description"]}
        for item in paths
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
    word2vec_results = job_ml_service.word2vec_similar_jobs(job_id, top_k=top_k)
    if word2vec_results is not None:
        return jsonify({"success": True, "model_source": "word2vec", "data": word2vec_results})

    conn = get_db()
    try:
        source = conn.execute(
            "SELECT rowid AS job_id, job_name, industry, salary_range, job_description FROM job WHERE rowid = ?",
            (job_id,),
        ).fetchone()
        if not source:
            return jsonify({"success": False, "error": "岗位不存在"}), 404
        rows = conn.execute(
            """
            SELECT rowid AS job_id, job_name, industry, salary_range, job_description
            FROM job
            WHERE rowid != ?
            """,
            (job_id,),
        ).fetchall()
    finally:
        conn.close()

    scored = [
        {"job_id": row["job_id"], "similarity": _similarity_score(source, row)}
        for row in rows
    ]
    scored.sort(key=lambda item: item["similarity"], reverse=True)
    return jsonify({"success": True, "model_source": "rules", "data": scored[:top_k]})


@job_bp.route("/skills", methods=["POST"])
def predict_job_skills():
    data = request.get_json(silent=True) or {}
    text = data.get("job_description", "")
    if not text:
        return jsonify({"success": False, "error": "请提供 job_description"}), 400
    top_k = data.get("top_k", 5)
    predictions, model_source = job_ml_service.predict_skills_with_textcnn(text, top_k=top_k)
    if predictions:
        return jsonify({
            "success": True,
            "model_source": model_source,
            "data": predictions,
        })
    skills = build_ml_job_profile({"job_title": "", "job_description": text}).get("skills", [])
    return jsonify({
        "success": True,
        "model_source": "rules",
        "data": [
            {"skill": skill, "probability": round(1.0 - index * 0.05, 4)}
            for index, skill in enumerate(skills[:top_k])
        ],
    })
