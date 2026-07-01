import datetime
import json
import os
import sqlite3
import uuid

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import get_db
from routes.auth import token_required


user_bp = Blueprint("user", __name__, url_prefix="/api")


def _row_get(row, key, default=None):
    if not row:
        return default
    try:
        return row[key]
    except Exception:
        return default


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _latest_student_for_user(conn, user_id):
    return conn.execute(
        "SELECT * FROM student WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()


def _current_student_id(conn, user_id):
    row = conn.execute("SELECT id FROM student WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    return row["id"] if row else None


def _format_created_at(value):
    if isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(value).isoformat()
    return value


@user_bp.route("/user", methods=["GET"])
@token_required
def get_current_user():
    user = request.user
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "phone": user["phone"],
        "role": user["role"],
        "is_active": user["is_active"],
        "avatar": _row_get(user, "avatar", "") or "",
        "created_at": user["created_at"],
    })


@user_bp.route("/user/profile", methods=["GET"])
@token_required
def get_user_profile():
    conn = get_db()
    try:
        user_row = conn.execute(
            "SELECT id, username, phone, role, avatar, created_at FROM users WHERE id = ?",
            (request.user["id"],),
        ).fetchone()
        if not user_row:
            return jsonify({"error": "用户不存在"}), 404
        student_row = _latest_student_for_user(conn, request.user["id"])
    finally:
        conn.close()

    profile = {
        "id": user_row["id"],
        "username": user_row["username"],
        "phone": user_row["phone"],
        "role": user_row["role"],
        "avatar": user_row["avatar"] or "",
        "joinTime": user_row["created_at"],
    }

    if student_row:
        profile.update({
            "student_id": student_row["id"],
            "name": student_row["name"] or "",
            "realName": student_row["name"] or "",
            "gender": "",
            "school": "",
            "major": student_row["major"] or "",
            "grade": student_row["grade"] or "",
            "email": student_row["email"] or "",
            "introduction": student_row["summary"] or "",
            "education_text": student_row["education_text"] or "",
            "work_text": student_row["work_text"] or "",
            "project_text": student_row["project_text"] or "",
            "skills_certs_text": student_row["skills_certs_text"] or "",
            "summary": student_row["summary"] or "",
            "skills": _json_loads(student_row["skills"], []),
            "soft_abilities": _json_loads(student_row["soft_abilities"], {}),
            "completeness": student_row["completeness"] or 0,
            "created_at": student_row["created_at"] or "",
        })
    else:
        profile.update({
            "student_id": None,
            "name": "",
            "realName": "",
            "gender": "",
            "school": "",
            "major": "",
            "grade": "",
            "email": "",
            "introduction": "",
            "education_text": "",
            "work_text": "",
            "project_text": "",
            "skills_certs_text": "",
            "summary": "",
            "skills": [],
            "soft_abilities": {},
            "completeness": 0,
            "created_at": "",
        })

    return jsonify(profile)


@user_bp.route("/user/profile", methods=["PUT"])
@token_required
def update_user_profile():
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        student_row = conn.execute("SELECT id FROM student WHERE user_id = ?", (request.user["id"],)).fetchone()
        if not student_row:
            cur = conn.execute(
                "INSERT INTO student (user_id, name, email, completeness) VALUES (?, ?, ?, ?)",
                (request.user["id"], data.get("name", ""), data.get("email", ""), 0),
            )
            student_id = cur.lastrowid
        else:
            student_id = student_row["id"]

        fields = []
        params = []
        allowed_fields = [
            "name", "email", "major", "grade", "education_text", "work_text",
            "project_text", "skills_certs_text", "summary",
        ]
        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                params.append(data[field])
        if fields:
            params.append(student_id)
            conn.execute(f"UPDATE student SET {', '.join(fields)} WHERE id = ?", params)
        if "phone" in data:
            existing = conn.execute(
                "SELECT id FROM users WHERE phone = ? AND id != ?",
                (data["phone"], request.user["id"]),
            ).fetchone()
            if existing:
                return jsonify({"error": "该手机号已被其他账号绑定"}), 409
            conn.execute("UPDATE users SET phone = ? WHERE id = ?", (data["phone"], request.user["id"]))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "该手机号已被其他账号绑定"}), 409
    finally:
        conn.close()
    return jsonify({"status": "ok"})


@user_bp.route("/user/avatar", methods=["POST"])
@token_required
def upload_avatar():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400
    if not file.content_type.startswith("image/"):
        return jsonify({"error": "invalid image type"}), 400

    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "avatars")
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))
    avatar_url = f"/uploads/avatars/{filename}"

    conn = get_db()
    try:
        conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar_url, request.user["id"]))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"avatar": avatar_url})


@user_bp.route("/user/change-password", methods=["POST"])
@token_required
def change_password():
    data = request.get_json(silent=True) or {}
    old_pwd = data.get("oldPwd")
    new_pwd = data.get("newPwd")
    if not old_pwd or not new_pwd:
        return jsonify({"error": "old password and new password required"}), 400

    conn = get_db()
    try:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (request.user["id"],)).fetchone()
        if not row:
            return jsonify({"error": "user not found"}), 404
        if not check_password_hash(row["password_hash"], old_pwd):
            return jsonify({"error": "invalid old password"}), 401
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_pwd), request.user["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "ok"})


@user_bp.route("/user/bind-phone", methods=["POST"])
@token_required
def bind_phone():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "phone required"}), 400
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE phone = ? AND id != ?",
            (phone, request.user["id"]),
        ).fetchone()
        if existing:
            return jsonify({"error": "该手机号已被其他账号绑定"}), 409
        conn.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, request.user["id"]))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "该手机号已被其他账号绑定"}), 409
    finally:
        conn.close()
    return jsonify({"status": "ok"})


@user_bp.route("/user/plans", methods=["GET"])
@token_required
def get_user_plans():
    conn = get_db()
    try:
        student_id = _current_student_id(conn, request.user["id"])
        if not student_id:
            return jsonify([])
        rows = conn.execute(
            """
            SELECT id, job_name, content, format_type, created_at
            FROM report_history
            WHERE student_id = ?
            ORDER BY created_at DESC
            """,
            (student_id,),
        ).fetchall()
    finally:
        conn.close()
    return jsonify([
        {
            "id": row["id"],
            "title": f"{row['job_name']} 职业规划报告",
            "targetJob": row["job_name"],
            "cycle": "1-3年",
            "matchRate": 0,
            "createTime": row["created_at"],
        }
        for row in rows
    ])


@user_bp.route("/user/interest-reports", methods=["GET"])
@token_required
def get_interest_reports():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, dimension_scores, recommendation, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (request.user["id"],),
        ).fetchall()
    finally:
        conn.close()

    reports = []
    for row in rows:
        scores = _json_loads(row["dimension_scores"], {})
        top_dimension = max(scores, key=scores.get) if scores else "综合兴趣"
        reports.append({
            "id": row["id"],
            "title": "霍兰德职业兴趣测评报告",
            "type": "霍兰德测评",
            "result": f"优势维度：{top_dimension}",
            "suitableJobs": "产品经理、运营、人力资源、数据分析、咨询顾问",
            "createTime": row["created_at"],
        })
    return jsonify(reports)


@user_bp.route("/user/match-reports", methods=["GET"])
@token_required
def get_match_reports():
    conn = get_db()
    try:
        student_id = _current_student_id(conn, request.user["id"])
        if not student_id:
            return jsonify([])
        rows = conn.execute(
            """
            SELECT id, job_name, match_score, details, created_at
            FROM match_history
            WHERE student_id = ?
            ORDER BY created_at DESC
            """,
            (student_id,),
        ).fetchall()
    finally:
        conn.close()

    reports = []
    for row in rows:
        details = _json_loads(row["details"], {})
        gap = details.get("gap_analysis", {})
        score = row["match_score"] or 0
        reports.append({
            "id": row["id"],
            "title": f"{row['job_name']} 匹配报告",
            "targetJob": row["job_name"],
            "score": score,
            "result": "高度匹配" if score >= 80 else ("中度匹配" if score >= 60 else "待提升"),
            "suggestion": gap.get("skills", "请完善技能并补充岗位相关项目经历"),
            "createTime": row["created_at"],
        })
    return jsonify(reports)


@user_bp.route("/user/history", methods=["GET"])
@token_required
def get_browse_history():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, title, description, cover, created_at
            FROM user_browse_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (request.user["id"],),
        ).fetchall()
    finally:
        conn.close()
    return jsonify([
        {
            "id": row["id"],
            "title": row["title"],
            "desc": row["description"],
            "cover": row["cover"],
            "browseTime": row["created_at"],
        }
        for row in rows
    ])


@user_bp.route("/user/history", methods=["POST"])
@token_required
def add_browse_history():
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO user_browse_history (user_id, item_type, item_id, title, description, cover)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.user["id"],
                data.get("type", "job"),
                data.get("itemId", 0),
                data.get("title"),
                data.get("desc") or "",
                data.get("cover") or "",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "added"})


@user_bp.route("/user/history/<int:history_id>", methods=["DELETE"])
@token_required
def delete_browse_history(history_id):
    conn = get_db()
    try:
        cur = conn.execute(
            "DELETE FROM user_browse_history WHERE id = ? AND user_id = ?",
            (history_id, request.user["id"]),
        )
        if cur.rowcount == 0:
            return jsonify({"error": "not found"}), 404
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "deleted"})


@user_bp.route("/user/history/clear", methods=["DELETE"])
@token_required
def clear_browse_history():
    conn = get_db()
    try:
        conn.execute("DELETE FROM user_browse_history WHERE user_id = ?", (request.user["id"],))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "cleared"})


@user_bp.route("/user/stats", methods=["GET"])
@token_required
def get_user_stats():
    conn = get_db()
    try:
        assessment_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM assessment_results WHERE user_id = ?",
            (request.user["id"],),
        ).fetchone()["cnt"]
        student_id = _current_student_id(conn, request.user["id"])
        plan_count = 0
        if student_id:
            plan_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM report_history WHERE student_id = ?",
                (student_id,),
            ).fetchone()["cnt"]
    finally:
        conn.close()
    return jsonify({"assessmentCount": assessment_count, "planCount": plan_count})


@user_bp.route("/user/reports", methods=["GET"])
@token_required
def get_all_reports():
    conn = get_db()
    try:
        student_id = _current_student_id(conn, request.user["id"])
        reports = []
        rows = conn.execute(
            """
            SELECT id, dimension_scores, recommendation, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (request.user["id"],),
        ).fetchall()
        for row in rows:
            created_at = _format_created_at(row["created_at"])
            summary = row["recommendation"][:100] if row["recommendation"] else "兴趣类型分析报告"
            reports.append({
                "id": f"interest_{row['id']}",
                "title": "霍兰德职业兴趣测评报告",
                "type": "interest_test",
                "summary": summary,
                "created_at": created_at,
                "original_id": row["id"],
                "original_table": "assessment_results",
            })

        if student_id:
            rows = conn.execute(
                """
                SELECT id, job_name, match_score, details, created_at
                FROM match_history
                WHERE student_id = ?
                ORDER BY created_at DESC
                """,
                (student_id,),
            ).fetchall()
            for row in rows:
                created_at = _format_created_at(row["created_at"])
                reports.append({
                    "id": f"match_{row['id']}",
                    "title": f"{row['job_name']} 人岗匹配报告",
                    "type": "job_match",
                    "summary": f"匹配度 {row['match_score']}%",
                    "created_at": created_at,
                    "original_id": row["id"],
                    "original_table": "match_history",
                })

            rows = conn.execute(
                """
                SELECT id, job_name, content, format_type, created_at
                FROM report_history
                WHERE student_id = ?
                ORDER BY created_at DESC
                """,
                (student_id,),
            ).fetchall()
            for row in rows:
                created_at = _format_created_at(row["created_at"])
                content = row["content"] or ""
                summary = (content[:100] + "...") if len(content) > 100 else content
                reports.append({
                    "id": f"plan_{row['id']}",
                    "title": f"{row['job_name']} 职业规划报告",
                    "type": "career_plan",
                    "summary": summary,
                    "created_at": created_at,
                    "original_id": row["id"],
                    "original_table": "report_history",
                })
    finally:
        conn.close()

    reports.sort(key=lambda item: item["created_at"] or "", reverse=True)
    return jsonify(reports)


@user_bp.route("/user/report/career/<int:report_id>", methods=["DELETE"])
@token_required
def delete_career_report(report_id):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT r.id
            FROM report_history r
            JOIN student s ON r.student_id = s.id
            WHERE r.id = ? AND s.user_id = ?
            """,
            (report_id, request.user["id"]),
        ).fetchone()
        if not row:
            return jsonify({"error": "报告不存在或无权限"}), 404
        conn.execute("DELETE FROM report_history WHERE id = ?", (report_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "deleted", "message": "职业规划报告已删除"})


@user_bp.route("/user/report/interest/<int:result_id>", methods=["DELETE"])
@token_required
def delete_interest_report(result_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM assessment_results WHERE id = ? AND user_id = ?",
            (result_id, request.user["id"]),
        ).fetchone()
        if not row:
            return jsonify({"error": "报告不存在或无权限"}), 404
        conn.execute("DELETE FROM assessment_results WHERE id = ?", (result_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "deleted", "message": "兴趣测评报告已删除"})


@user_bp.route("/user/report/match/<int:match_id>", methods=["DELETE"])
@token_required
def delete_match_report(match_id):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT m.id
            FROM match_history m
            JOIN student s ON m.student_id = s.id
            WHERE m.id = ? AND s.user_id = ?
            """,
            (match_id, request.user["id"]),
        ).fetchone()
        if not row:
            return jsonify({"error": "报告不存在或无权限"}), 404
        conn.execute("DELETE FROM match_history WHERE id = ?", (match_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "deleted", "message": "人岗匹配报告已删除"})
