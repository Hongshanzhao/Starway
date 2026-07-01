import time

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from db import get_db
from routes.auth import admin_required
from services import job_repository
from services.career_ai_service import rebuild_job_graph


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _close(conn):
    try:
        conn.close()
    except Exception:
        pass


def _category_rows():
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT job_category AS name, COUNT(*) AS job_count
            FROM jobs
            WHERE job_category IS NOT NULL AND job_category != ''
            GROUP BY job_category
            ORDER BY job_category
            """
        ).fetchall()
    finally:
        _close(conn)


def _pick(data, current, *keys):
    for key in keys:
        if key in data:
            return data.get(key)
    return current


@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "credentials required"}), 400

    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        _close(conn)

    if not user:
        return jsonify({"error": "user not found"}), 404
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({
        "token": f"mock-token-{user['id']}",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    })


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, username, phone, role, is_active, created_at FROM users").fetchall()
        role_rows = conn.execute(
            "SELECT role AS name, COUNT(*) AS value FROM users GROUP BY role ORDER BY value DESC"
        ).fetchall()
        status_rows = conn.execute(
            """
            SELECT CASE WHEN is_active = 1 THEN '启用' ELSE '停用' END AS name, COUNT(*) AS value
            FROM users
            GROUP BY is_active
            ORDER BY is_active DESC
            """
        ).fetchall()
        profile_rows = conn.execute(
            """
            SELECT profile_status AS name, COUNT(*) AS value
            FROM (
              SELECT u.id,
                     CASE WHEN COUNT(s.id) = 0 THEN '未建画像' ELSE '已建画像' END AS profile_status
              FROM users u
              LEFT JOIN student s ON s.user_id = u.id
              GROUP BY u.id
            )
            GROUP BY profile_status
            """
        ).fetchall()
        recent_rows = conn.execute(
            """
            SELECT COALESCE(DATE(created_at), '未知日期') AS name, COUNT(*) AS value
            FROM users
            GROUP BY COALESCE(DATE(created_at), '未知日期')
            ORDER BY name DESC
            LIMIT 14
            """
        ).fetchall()
    finally:
        _close(conn)
    users = [dict(row) for row in rows]
    return jsonify({
        "total": len(users),
        "users": users,
        "analytics": {
            "roles": [dict(row) for row in role_rows],
            "status": [dict(row) for row in status_rows],
            "profiles": [dict(row) for row in profile_rows],
            "recent": [dict(row) for row in recent_rows],
        },
    })


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    conn = get_db()
    try:
        totals = {
            "users": conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"],
            "students": conn.execute("SELECT COUNT(*) AS total FROM student").fetchone()["total"],
            "jobs": conn.execute("SELECT COUNT(*) AS total FROM jobs").fetchone()["total"],
            "reports": conn.execute("SELECT COUNT(*) AS total FROM report_history").fetchone()["total"],
            "matches": conn.execute("SELECT COUNT(*) AS total FROM match_history").fetchone()["total"],
            "assessments": conn.execute("SELECT COUNT(*) AS total FROM assessment_results").fetchone()["total"],
        }
        categories = conn.execute(
            """
            SELECT COALESCE(job_category, '未分类') AS name, COUNT(*) AS value
            FROM jobs
            GROUP BY COALESCE(job_category, '未分类')
            ORDER BY value DESC
            LIMIT 10
            """
        ).fetchall()
        report_jobs = conn.execute(
            """
            SELECT job_name AS name, COUNT(*) AS value
            FROM report_history
            GROUP BY job_name
            ORDER BY value DESC
            LIMIT 8
            """
        ).fetchall()
        match_scores = conn.execute(
            """
            SELECT job_name, match_score, created_at
            FROM match_history
            ORDER BY created_at DESC
            LIMIT 12
            """
        ).fetchall()
        relations = conn.execute(
            """
            SELECT from_job, to_job, relation_type, description
            FROM job_relations
            ORDER BY id DESC
            LIMIT 80
            """
        ).fetchall()
        recent_reports = conn.execute(
            """
            SELECT id, student_id, job_name, created_at
            FROM report_history
            ORDER BY created_at DESC
            LIMIT 6
            """
        ).fetchall()
    finally:
        _close(conn)

    nodes = sorted({row["from_job"] for row in relations} | {row["to_job"] for row in relations})[:60]
    return jsonify({
        "totals": totals,
        "categories": [dict(row) for row in categories],
        "report_jobs": [dict(row) for row in report_jobs],
        "match_scores": [dict(row) for row in match_scores],
        "graph": {
            "nodes": [{"name": name, "value": 1} for name in nodes],
            "links": [
                {
                    "source": row["from_job"],
                    "target": row["to_job"],
                    "relation_type": row["relation_type"],
                    "description": row["description"] or "",
                }
                for row in relations
                if row["from_job"] in nodes and row["to_job"] in nodes
            ],
        },
        "recent_reports": [dict(row) for row in recent_reports],
    })


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, phone, role, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        _close(conn)
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    fields = []
    values = []
    for field in ("username", "phone", "role", "is_active"):
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return jsonify({"error": "no fields provided"}), 400

    conn = get_db()
    try:
        values.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    finally:
        _close(conn)
    return jsonify({"status": "ok"})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        _close(conn)
    return jsonify({"status": "deleted"})


@admin_bp.route("/categories", methods=["GET"])
@admin_required
def get_categories():
    rows = _category_rows()
    return jsonify({
        "list": [
            {
                "id": index + 1,
                "name": row["name"],
                "description": f"{row['job_count']} jobs",
                "job_count": row["job_count"],
            }
            for index, row in enumerate(rows)
        ]
    })


@admin_bp.route("/category-summary", methods=["GET"])
@admin_required
def get_category_summary():
    rows = _category_rows()
    categories = [
        {
            "id": index + 1,
            "name": row["name"],
            "job_count": row["job_count"],
        }
        for index, row in enumerate(rows)
    ]
    return jsonify({
        "total_categories": len(categories),
        "categories": categories,
    })


@admin_bp.route("/categories", methods=["POST"])
@admin_required
def add_category():
    return jsonify({"error": "job categories come from jobs.job_category and cannot be edited here"}), 400


@admin_bp.route("/categories/<int:cid>", methods=["DELETE"])
@admin_required
def delete_category(cid):
    return jsonify({"error": "job categories come from jobs.job_category and cannot be deleted here"}), 400


@admin_bp.route("/jobs", methods=["GET"])
@admin_required
def get_all_jobs():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)
    keyword = request.args.get("keyword", "", type=str)
    industry = request.args.get("industry", "", type=str)
    city = request.args.get("city", "", type=str)
    if page < 1 or size < 1:
        return jsonify({"error": "pagination parameters invalid"}), 400
    size = min(size, 100)
    total, rows = job_repository.admin_list_jobs(
        keyword=keyword,
        industry=industry,
        city=city,
        page=page,
        size=size,
    )
    conn = get_db()
    try:
        industry_rows = conn.execute(
            """
            SELECT COALESCE(job_category, '未分类') AS name, COUNT(*) AS value
            FROM jobs
            GROUP BY COALESCE(job_category, '未分类')
            ORDER BY value DESC
            LIMIT 12
            """
        ).fetchall()
        city_rows = conn.execute(
            """
            SELECT COALESCE(city, '未知城市') AS name, COUNT(*) AS value
            FROM jobs
            GROUP BY COALESCE(city, '未知城市')
            ORDER BY value DESC
            LIMIT 10
            """
        ).fetchall()
        salary_rows = conn.execute(
            """
            SELECT
              CASE
                WHEN salary_avg IS NULL OR salary_avg = 0 THEN '薪资未知'
                WHEN salary_avg < 8000 THEN '8k以下'
                WHEN salary_avg < 15000 THEN '8k-15k'
                WHEN salary_avg < 25000 THEN '15k-25k'
                ELSE '25k以上'
              END AS name,
              COUNT(*) AS value
            FROM jobs
            GROUP BY name
            ORDER BY value DESC
            """
        ).fetchall()
        quality_rows = conn.execute(
            """
            SELECT
              SUM(CASE WHEN skills IS NOT NULL AND TRIM(skills) != '' THEN 1 ELSE 0 END) AS has_skills,
              SUM(CASE WHEN job_description IS NOT NULL AND LENGTH(TRIM(job_description)) > 30 THEN 1 ELSE 0 END) AS has_description,
              SUM(CASE WHEN requirements IS NOT NULL AND LENGTH(TRIM(requirements)) > 20 THEN 1 ELSE 0 END) AS has_requirements,
              COUNT(*) AS total
            FROM jobs
            """
        ).fetchone()
        summary_rows = conn.execute(
            """
            SELECT
              COUNT(*) AS total_jobs,
              COUNT(DISTINCT NULLIF(job_category, '')) AS industry_count,
              COUNT(DISTINCT NULLIF(city, '')) AS city_count
            FROM jobs
            """
        ).fetchone()
    finally:
        _close(conn)
    return jsonify({
        "list": [{**row, "category_name": row["industry"]} for row in rows],
        "total": total,
        "page": page,
        "size": size,
        "analytics": {
            "industries": [dict(row) for row in industry_rows],
            "cities": [dict(row) for row in city_rows],
            "salary": [dict(row) for row in salary_rows],
            "quality": dict(quality_rows) if quality_rows else {},
            "summary": dict(summary_rows) if summary_rows else {},
        },
    })


@admin_bp.route("/jobs", methods=["POST"])
@admin_required
def add_job():
    data = request.get_json(silent=True) or {}
    job_code = data.get("job_code") or data.get("job_id") or f"MANUAL-{int(time.time())}"
    job_name = data.get("job_name") or data.get("job_title")
    if not job_name:
        return jsonify({"error": "job_name is required"}), 400
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO jobs (
                job_id, job_title, job_category, company_name, city,
                company_size, company_type, salary_min, salary_max, salary_avg,
                skills, job_description, requirements, publish_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_code,
                job_name,
                data.get("industry") or data.get("job_category"),
                data.get("company") or data.get("company_name"),
                data.get("location") or data.get("city"),
                data.get("company_size"),
                data.get("company_type"),
                data.get("salary_min"),
                data.get("salary_max"),
                data.get("salary_avg"),
                data.get("skills"),
                data.get("job_description"),
                data.get("requirements"),
                data.get("updated_at") or data.get("publish_date"),
            ),
        )
        conn.commit()
        job_repository.clear_cache()
    finally:
        _close(conn)
    return jsonify({"status": "ok"})


@admin_bp.route("/jobs/<int:jid>", methods=["PUT"])
@admin_required
def update_job(jid):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE rowid = ?", (jid,)).fetchone()
        if row is None:
            return jsonify({"error": "job not found"}), 404
        current = dict(row)
        old_job_id = current.get("job_id")
        new_job_id = _pick(data, old_job_id, "job_code", "job_id")
        if not new_job_id:
            return jsonify({"error": "job_id cannot be empty"}), 400
        if new_job_id != old_job_id:
            conn.execute("UPDATE applications SET job_id = ? WHERE job_id = ?", (new_job_id, old_job_id))
        conn.execute(
            """
            UPDATE jobs SET
                job_title = ?, city = ?, company_name = ?, job_category = ?,
                company_size = ?, company_type = ?, job_id = ?, job_description = ?,
                requirements = ?, publish_date = ?, skills = ?, salary_min = ?,
                salary_max = ?, salary_avg = ?
            WHERE rowid = ?
            """,
            (
                _pick(data, current.get("job_title"), "job_name", "job_title"),
                _pick(data, current.get("city"), "location", "city"),
                _pick(data, current.get("company_name"), "company", "company_name"),
                _pick(data, current.get("job_category"), "industry", "job_category"),
                _pick(data, current.get("company_size"), "company_size"),
                _pick(data, current.get("company_type"), "company_type"),
                new_job_id,
                _pick(data, current.get("job_description"), "job_description"),
                _pick(data, current.get("requirements"), "requirements"),
                _pick(data, current.get("publish_date"), "updated_at", "publish_date"),
                _pick(data, current.get("skills"), "skills"),
                _pick(data, current.get("salary_min"), "salary_min"),
                _pick(data, current.get("salary_max"), "salary_max"),
                _pick(data, current.get("salary_avg"), "salary_avg"),
                jid,
            ),
        )
        conn.commit()
        job_repository.clear_cache()
    finally:
        _close(conn)
    return jsonify({"status": "ok"})


@admin_bp.route("/jobs/<int:jid>", methods=["DELETE"])
@admin_required
def delete_job(jid):
    conn = get_db()
    try:
        row = conn.execute("SELECT job_id FROM jobs WHERE rowid = ?", (jid,)).fetchone()
        if row is None:
            return jsonify({"error": "job not found"}), 404
        application_count = conn.execute(
            "SELECT COUNT(*) AS total FROM applications WHERE job_id = ?",
            (row["job_id"],),
        ).fetchone()["total"]
        if application_count:
            return jsonify({
                "error": "job has applications and cannot be deleted",
                "application_count": application_count,
            }), 409
        conn.execute("DELETE FROM jobs WHERE rowid = ?", (jid,))
        conn.commit()
        job_repository.clear_cache()
    finally:
        _close(conn)
    return jsonify({"status": "deleted"})


@admin_bp.route("/build-job-graph", methods=["POST"])
@admin_required
def build_job_graph():
    try:
        vertical_count, lateral_count = rebuild_job_graph()
        conn = get_db()
        try:
            rows = conn.execute(
                """
                SELECT from_job, to_job, relation_type, description
                FROM job_relations
                ORDER BY id DESC
                LIMIT 60
                """
            ).fetchall()
        finally:
            _close(conn)
        nodes = sorted({row["from_job"] for row in rows} | {row["to_job"] for row in rows})
        return jsonify({
            "success": True,
            "message": f"岗位关系已更新：新增晋升路线 {vertical_count} 条，换岗路线 {lateral_count} 条。前台成长路径、相似岗位和换岗建议会使用这些关系。",
            "vertical_count": vertical_count,
            "lateral_count": lateral_count,
            "graph": {
                "nodes": [{"name": name, "value": 1} for name in nodes],
                "links": [
                    {
                        "source": row["from_job"],
                        "target": row["to_job"],
                        "relation_type": row["relation_type"],
                        "description": row["description"] or "",
                    }
                    for row in rows
                ],
            },
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@admin_bp.route("/graph/overview", methods=["GET"])
@admin_required
def graph_overview():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT from_job, to_job, relation_type, description
            FROM job_relations
            ORDER BY id DESC
            LIMIT 180
            """
        ).fetchall()
        relation_rows = conn.execute(
            """
            SELECT
              CASE
                WHEN relation_type = 'promotion' THEN '晋升路线'
                WHEN relation_type = 'transition' THEN '换岗路线'
                ELSE '其他关系'
              END AS name,
              COUNT(*) AS value
            FROM job_relations
            GROUP BY name
            ORDER BY value DESC
            """
        ).fetchall()
        isolated_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM jobs j
            WHERE NOT EXISTS (
              SELECT 1 FROM job_relations r
              WHERE r.from_job = j.job_title OR r.to_job = j.job_title
            )
            """
        ).fetchone()["total"]
        total_jobs = conn.execute("SELECT COUNT(*) AS total FROM jobs").fetchone()["total"]
    finally:
        _close(conn)

    nodes = sorted({row["from_job"] for row in rows} | {row["to_job"] for row in rows})
    coverage = round(((total_jobs - isolated_count) / total_jobs) * 100, 1) if total_jobs else 0
    return jsonify({
        "total_jobs": total_jobs,
        "isolated_jobs": isolated_count,
        "coverage": coverage,
        "relation_types": [dict(row) for row in relation_rows],
        "graph": {
            "nodes": [{"name": name, "value": 1} for name in nodes],
            "links": [
                {
                    "source": row["from_job"],
                    "target": row["to_job"],
                    "relation_type": row["relation_type"],
                    "description": row["description"] or "",
                }
                for row in rows
            ],
        },
    })


@admin_bp.route("/ai-tools/overview", methods=["GET"])
@admin_required
def ai_tools_overview():
    conn = get_db()
    try:
        totals = {
            "reports": conn.execute("SELECT COUNT(*) AS total FROM report_history").fetchone()["total"],
            "matches": conn.execute("SELECT COUNT(*) AS total FROM match_history").fetchone()["total"],
            "assessments": conn.execute("SELECT COUNT(*) AS total FROM assessment_results").fetchone()["total"],
            "profiles": conn.execute("SELECT COUNT(*) AS total FROM student").fetchone()["total"],
        }
        ai_rows = conn.execute(
            """
            SELECT '职业报告' AS name, COUNT(*) AS value FROM report_history
            UNION ALL
            SELECT '人岗匹配' AS name, COUNT(*) AS value FROM match_history
            UNION ALL
            SELECT '兴趣测评' AS name, COUNT(*) AS value FROM assessment_results
            """
        ).fetchall()
        report_rows = conn.execute(
            """
            SELECT COALESCE(job_name, '未知方向') AS name, COUNT(*) AS value
            FROM report_history
            GROUP BY COALESCE(job_name, '未知方向')
            ORDER BY value DESC
            LIMIT 8
            """
        ).fetchall()
        quality = conn.execute(
            """
            SELECT
              SUM(CASE WHEN LENGTH(COALESCE(content, '')) >= 800 THEN 1 ELSE 0 END) AS useful_reports,
              COUNT(*) AS total_reports
            FROM report_history
            """
        ).fetchone()
    finally:
        _close(conn)
    total_reports = quality["total_reports"] if quality else 0
    useful_reports = quality["useful_reports"] if quality else 0
    return jsonify({
        "totals": totals,
        "ai_outputs": [dict(row) for row in ai_rows],
        "report_jobs": [dict(row) for row in report_rows],
        "quality": {
            "useful_reports": useful_reports or 0,
            "total_reports": total_reports or 0,
            "report_quality_rate": round(((useful_reports or 0) / total_reports) * 100, 1) if total_reports else 0,
        },
        "tasks": [
            {"name": "刷新岗位关系图谱", "impact": "提升成长路径、相似岗位、换岗建议的连贯性", "action": "build_graph"},
            {"name": "检查报告质量", "impact": "发现过短、信息不足或不适合直接导出的报告", "action": "review_reports"},
            {"name": "补齐岗位画像", "impact": "让岗位画像和匹配指标不再空洞", "action": "review_jobs"},
        ],
    })


@admin_bp.route("/reports", methods=["GET"])
@admin_required
def list_reports():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)
    student_id = request.args.get("student_id", type=int)
    if page < 1 or size < 1:
        return jsonify({"error": "pagination parameters invalid"}), 400

    conditions = []
    params = []
    if student_id:
        conditions.append("student_id = ?")
        params.append(student_id)
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * size

    conn = get_db()
    try:
        total = conn.execute(f"SELECT COUNT(*) AS total FROM report_history {where_clause}", params).fetchone()["total"]
        rows = conn.execute(
            f"""
            SELECT id, student_id, job_name, content, format_type, created_at
            FROM report_history {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [size, offset],
        ).fetchall()
        job_rows = conn.execute(
            """
            SELECT COALESCE(job_name, '未知方向') AS name, COUNT(*) AS value
            FROM report_history
            GROUP BY COALESCE(job_name, '未知方向')
            ORDER BY value DESC
            LIMIT 10
            """
        ).fetchall()
        day_rows = conn.execute(
            """
            SELECT COALESCE(DATE(created_at, 'unixepoch'), '未知日期') AS name, COUNT(*) AS value
            FROM report_history
            GROUP BY COALESCE(DATE(created_at, 'unixepoch'), '未知日期')
            ORDER BY name DESC
            LIMIT 14
            """
        ).fetchall()
        length_rows = conn.execute(
            """
            SELECT
              CASE
                WHEN LENGTH(COALESCE(content, '')) < 500 THEN '偏短'
                WHEN LENGTH(COALESCE(content, '')) < 1500 THEN '适中'
                ELSE '详细'
              END AS name,
              COUNT(*) AS value
            FROM report_history
            GROUP BY name
            """
        ).fetchall()
    finally:
        _close(conn)

    return jsonify({
        "total": total,
        "page": page,
        "size": size,
        "items": [dict(row) for row in rows],
        "analytics": {
            "jobs": [dict(row) for row in job_rows],
            "daily": [dict(row) for row in day_rows],
            "length": [dict(row) for row in length_rows],
        },
    })


@admin_bp.route("/reports/<int:report_id>", methods=["GET"])
@admin_required
def get_report(report_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM report_history WHERE id = ?", (report_id,)).fetchone()
    finally:
        _close(conn)
    if not row:
        return jsonify({"error": "report not found"}), 404
    return jsonify(dict(row))


@admin_bp.route("/reports/<int:report_id>", methods=["DELETE"])
@admin_required
def delete_report(report_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM report_history WHERE id = ?", (report_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "report not found"}), 404
        conn.commit()
    finally:
        _close(conn)
    return jsonify({"status": "deleted"})


@admin_bp.route("/users/<int:user_id>/reports", methods=["GET"])
@admin_required
def get_user_reports(user_id):
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)
    if page < 1 or size < 1:
        return jsonify({"error": "pagination parameters invalid"}), 400

    offset = (page - 1) * size
    conn = get_db()
    try:
        total = conn.execute(
            "SELECT COUNT(*) AS total FROM report_history WHERE student_id = ?",
            (user_id,),
        ).fetchone()["total"]
        rows = conn.execute(
            """
            SELECT id, student_id, job_name, content, format_type, created_at
            FROM report_history
            WHERE student_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, size, offset),
        ).fetchall()
    finally:
        _close(conn)

    return jsonify({"total": total, "page": page, "size": size, "items": [dict(row) for row in rows]})
