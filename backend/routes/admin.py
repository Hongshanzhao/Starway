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
    finally:
        _close(conn)
    users = [dict(row) for row in rows]
    return jsonify({"total": len(users), "users": users})


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
        "source": "jobs.job_category",
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
    rows = job_repository.all_jobs()
    return jsonify({"list": [{**row, "category_name": row["industry"]} for row in rows]})


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
        return jsonify({
            "success": True,
            "message": f"岗位关系图谱重建完成，新增垂直路径 {vertical_count} 条，横向路径 {lateral_count} 条",
            "vertical_count": vertical_count,
            "lateral_count": lateral_count,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


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
    finally:
        _close(conn)

    return jsonify({"total": total, "page": page, "size": size, "items": [dict(row) for row in rows]})


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
