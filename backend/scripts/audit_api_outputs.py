import json
import os
import shutil
import sys
import tempfile
import base64
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
SOURCE_DB = BACKEND / "instance" / "career.db"
TMP = Path(tempfile.mkdtemp(prefix="starway_api_audit_"))
TMP_DB = TMP / "career_audit.db"
AVATAR_FILE = BACKEND / "uploads" / "avatars" / "audit.png"

shutil.copy2(SOURCE_DB, TMP_DB)
os.environ["SQLITE_DB_PATH"] = str(TMP_DB)
os.environ["LLM_PROVIDER"] = "local"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

from backend.app import app  # noqa: E402
from db import get_db  # noqa: E402


app.config["TESTING"] = True


def seed_data():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username IN (?, ?)", ("audit_user", "audit_admin"))
    cur.execute(
        "INSERT INTO users (username, phone, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        ("audit_user", "13900000001", generate_password_hash("pass123"), "user"),
    )
    user_id = cur.lastrowid
    cur.execute(
        "INSERT INTO users (username, phone, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        ("audit_admin", "13900000002", generate_password_hash("pass123"), "admin"),
    )
    admin_id = cur.lastrowid

    cur.execute("DELETE FROM student WHERE id = ?", (900101,))
    cur.execute(
        """
        INSERT INTO student
        (id, user_id, name, major, grade, skills, certificates, soft_abilities, internships, completeness, competitiveness)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            900101,
            user_id,
            "Audit Student",
            "Computer Science",
            "Senior",
            json.dumps(["Python", "SQL"]),
            json.dumps(["CET-6"]),
            json.dumps({"communication": {"score": 4}}),
            "backend internship",
            90,
            80,
        ),
    )
    cur.execute("DELETE FROM report_history WHERE id = ?", (900101,))
    cur.execute(
        "INSERT INTO report_history (id, student_id, job_name, content, format_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (900101, 900101, "Java Developer", "# Audit Report\ncontent", "markdown", datetime.now().isoformat()),
    )
    cur.execute("DELETE FROM match_history WHERE id = ?", (900101,))
    cur.execute(
        "INSERT INTO match_history (id, student_id, job_name, match_score, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (900101, 900101, "Java Developer", 88.0, json.dumps({"gap_analysis": {"skills": "ok"}}), datetime.now().isoformat()),
    )
    cur.execute("DELETE FROM assessment_results WHERE id = ?", (900101,))
    cur.execute(
        """
        INSERT INTO assessment_results
        (id, user_id, session_id, dimension_scores, recommendation, raw_answers, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (900101, user_id, "audit", json.dumps({"R": 4}), "audit recommendation", json.dumps([]), datetime.now().isoformat()),
    )
    cur.execute("DELETE FROM jobs WHERE job_id = ?", ("AUDIT-JOB-900201",))
    cur.execute(
        """
        INSERT INTO jobs
        (job_id, job_title, job_category, company_name, city, salary_min, salary_max, skills, job_description, requirements)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("AUDIT-JOB-900201", "Audit Delete Job", "Tech", "Audit Co", "Hangzhou", 10000, 15000, "Python,SQL", "Audit job desc", "Audit requirements"),
    )
    cur.execute("DELETE FROM user_browse_history WHERE id = ?", (900101,))
    cur.execute(
        "INSERT INTO user_browse_history (id, user_id, item_type, item_id, title, description) VALUES (?, ?, ?, ?, ?, ?)",
        (900101, user_id, "job", 1, "Audit History", "Audit desc"),
    )
    conn.commit()
    conn.close()
    seed_avatar_file()
    return user_id, admin_id


def seed_avatar_file():
    avatar_dir = AVATAR_FILE.parent
    avatar_dir.mkdir(parents=True, exist_ok=True)
    png_1x1 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    )
    AVATAR_FILE.write_bytes(base64.b64decode(png_1x1))


def get_fixtures():
    conn = get_db()
    job_row = conn.execute("SELECT rowid AS id, job_title AS job_name FROM jobs ORDER BY rowid LIMIT 1").fetchone()
    delete_job_row = conn.execute(
        "SELECT rowid AS id FROM jobs WHERE job_id = ?",
        ("AUDIT-JOB-900201",),
    ).fetchone()
    question = conn.execute("SELECT id FROM assessment_questions ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return (
        int(job_row["id"]),
        job_row["job_name"],
        int(delete_job_row["id"]),
        int(question["id"]) if question else 1,
    )


def is_json(resp):
    return resp.is_json and resp.get_json(silent=True) is not None


def nonempty(resp):
    return resp.status_code in (204, 304) or len(resp.get_data()) > 0


def summary(resp):
    ctype = resp.headers.get("Content-Type", "")
    if resp.is_json:
        data = resp.get_json(silent=True)
        if isinstance(data, dict):
            return "json keys=" + ",".join(map(str, list(data.keys())[:8]))
        if isinstance(data, list):
            return f"json list len={len(data)}"
        return f"json {type(data).__name__}"
    raw = resp.get_data()
    if "image/" in ctype or "application/" in ctype or (raw and raw[0] == 0x89):
        return f"{ctype} bytes={len(raw)}"
    return f"{ctype} " + raw[:160].decode("utf-8", errors="replace").replace("\n", "\\n")


def spec(method, path, kwargs=None, expected=200, kind="json"):
    return method, path, kwargs or {}, expected if isinstance(expected, set) else {expected}, kind


def build_specs(user_id, admin_id, job_id, job_name, delete_job_id, question_id):
    user_headers = {"Authorization": f"Bearer mock-token-{user_id}"}
    admin_headers = {"Authorization": f"Bearer mock-token-{admin_id}"}
    return [
        spec("GET", "/"),
        spec("GET", "/test-db"),
        spec("GET", "/uploads/avatars/audit.png", kind="binary"),
        spec("GET", "/api/captcha", kind="binary"),
        spec("POST", "/api/send_code", {"json": {"phone": "13900000003"}}, 410),
        spec("POST", "/api/login", {"json": {"username": "audit_user", "password": "pass123", "captcha": "skip"}}, {400, 401, 404}),
        spec("POST", "/api/register", {"json": {"username": "audit_new", "password": "x", "captcha": "skip"}}, {200, 400}),
        spec("GET", "/api/jobs/search?page=1&size=2"),
        spec("GET", "/api/jobs/simple_search?keyword=Java&page=1&size=2"),
        spec("GET", "/api/jobs/categories"),
        spec("GET", "/api/jobs/industries"),
        spec("GET", "/api/jobs/names"),
        spec("GET", f"/api/jobs/{job_id}"),
        spec("GET", f"/api/jobs/{job_id}/profile"),
        spec("GET", f"/api/jobs/{job_id}/similar?top_k=3"),
        spec("GET", f"/api/jobs/profile/{job_name}"),
        spec("GET", f"/api/jobs/{job_name}/full-path"),
        spec("GET", f"/api/jobs/{job_name}/vertical"),
        spec("GET", f"/api/jobs/{job_name}/lateral"),
        spec("GET", "/api/jobs/graph"),
        spec("POST", "/api/jobs/skills", {"json": {"job_description": "Python Flask SQL backend API", "top_k": 3}}),
        spec("GET", "/api/assessment/questions"),
        spec("POST", "/api/assessment/submit", {"json": {"answers": [{"question_id": question_id, "score": 4}], "user_id": user_id, "session_id": "audit", "test_mode": True}}),
        spec("GET", f"/api/assessment/history/{user_id}"),
        spec("POST", "/api/assistant/chat", {"json": {"message": "How should I prepare for Python backend jobs?", "context": {"skills": ["Python"]}}}),
        spec("POST", "/api/assistant/chat", {"json": {"message": "How should I prepare for Python backend jobs?", "stream": True}}, kind="stream"),
        spec("POST", "/api/llm/qa", {"json": {"question": "How to prepare for data analysis?", "context": "Python SQL"}}),
        spec("POST", "/api/llm/generate_plan", {"headers": user_headers, "json": {"student": {"skills": ["Python"]}, "job_name": "Java Developer"}}),
        spec("POST", "/api/llm/recommend", {"headers": user_headers, "json": {"student": {"skills": "Python,SQL"}}}),
        spec("GET", "/api/llm/test_connection"),
        spec("GET", "/api/match/recommend?student_id=900101&limit=3"),
        spec("POST", "/api/match/match", {"json": {"student_id": 900101, "job_name": job_name}}),
        spec("POST", "/api/match/match-stream", {"json": {"student_id": 900101, "job_name": job_name}}, kind="stream"),
        spec("GET", "/api/match/history/900101", {"headers": user_headers}),
        spec("POST", "/api/profile/submit", {"json": {"user_id": user_id, "name": "Audit Profile", "skills": ["Python", "SQL"], "education": "Bachelor"}}),
        spec("GET", "/api/profile/900101"),
        spec("POST", "/api/profile/upload", {"data": {}}, {400, 415}),
        spec("POST", "/api/report/generate", {"json": {"student_id": 900101, "job_name": job_name}}),
        spec("POST", "/api/report/generate-stream", {"json": {"student_id": 900101, "job_name": job_name}}, kind="stream"),
        spec("GET", "/api/report/history/900101"),
        spec("GET", "/api/report/900101"),
        spec("PUT", "/api/report/900101", {"json": {"content": "# Updated audit report"}}),
        spec("POST", "/api/report/polish", {"json": {"content": "Please polish this career plan."}}),
        spec("POST", "/api/report/export", {"json": {"markdown": "# Audit\ncontent"}}, kind="download"),
        spec("POST", "/api/admin/login", {"json": {"username": "audit_admin", "password": "pass123"}}),
        spec("GET", "/api/admin/users", {"headers": admin_headers}),
        spec("GET", f"/api/admin/users/{user_id}", {"headers": admin_headers}),
        spec("PUT", f"/api/admin/users/{user_id}", {"headers": admin_headers, "json": {"is_active": 1}}),
        spec("GET", "/api/admin/categories", {"headers": admin_headers}),
        spec("POST", "/api/admin/categories", {"headers": admin_headers, "json": {"name": "Audit"}}, 400),
        spec("DELETE", "/api/admin/categories/1", {"headers": admin_headers}, 400),
        spec("GET", "/api/admin/jobs", {"headers": admin_headers}),
        spec("POST", "/api/admin/jobs", {"headers": admin_headers, "json": {"job_name": "Audit Admin Job", "industry": "Tech"}}),
        spec("PUT", f"/api/admin/jobs/{job_id}", {"headers": admin_headers, "json": {"job_name": job_name, "industry": "Tech"}}),
        spec("DELETE", f"/api/admin/jobs/{delete_job_id}", {"headers": admin_headers}),
        spec("GET", "/api/admin/category-summary", {"headers": admin_headers}),
        spec("POST", "/api/admin/build-job-graph", {"headers": admin_headers, "json": {}}),
        spec("GET", "/api/admin/reports", {"headers": admin_headers}),
        spec("GET", "/api/admin/reports/900101", {"headers": admin_headers}, {200, 404}),
        spec("DELETE", "/api/admin/reports/900101", {"headers": admin_headers}, {200, 404}),
        spec("GET", f"/api/admin/users/{user_id}/reports", {"headers": admin_headers}),
        spec("DELETE", f"/api/admin/users/{admin_id}", {"headers": admin_headers}),
        spec("GET", "/api/user", {"headers": user_headers}),
        spec("GET", "/api/user/profile", {"headers": user_headers}),
        spec("PUT", "/api/user/profile", {"headers": user_headers, "json": {"name": "Audit User", "email": "audit@example.com"}}),
        spec("POST", "/api/user/change-password", {"headers": user_headers, "json": {"oldPwd": "pass123", "newPwd": "pass123"}}),
        spec("POST", "/api/user/bind-phone", {"headers": user_headers, "json": {"phone": "13900009999", "code": "000000"}}),
        spec("POST", "/api/user/avatar", {"headers": user_headers, "data": {}}, 400),
        spec("GET", "/api/user/plans", {"headers": user_headers}),
        spec("GET", "/api/user/interest-reports", {"headers": user_headers}),
        spec("GET", "/api/user/match-reports", {"headers": user_headers}),
        spec("GET", "/api/user/history", {"headers": user_headers}),
        spec("POST", "/api/user/history", {"headers": user_headers, "json": {"title": "Audit Browse", "desc": "desc", "type": "job", "itemId": 1}}),
        spec("DELETE", "/api/user/history/900101", {"headers": user_headers}, {200, 404}),
        spec("DELETE", "/api/user/history/clear", {"headers": user_headers}),
        spec("GET", "/api/user/stats", {"headers": user_headers}),
        spec("GET", "/api/user/reports", {"headers": user_headers}),
        spec("DELETE", "/api/user/report/career/900101", {"headers": user_headers}, {200, 404}),
        spec("DELETE", "/api/user/report/interest/900101", {"headers": user_headers}, {200, 404}),
        spec("DELETE", "/api/user/report/match/900101", {"headers": user_headers}, {200, 404}),
        spec("GET", "/api/contents"),
    ]


def check_format(resp, kind):
    ctype = resp.headers.get("Content-Type", "")
    if kind == "json":
        return is_json(resp)
    if kind == "stream":
        return "text/event-stream" in ctype and resp.get_data(as_text=True).startswith("data:")
    if kind == "binary":
        return len(resp.get_data()) > 0 and ("image/" in ctype or "application/octet-stream" in ctype)
    if kind == "download":
        return len(resp.get_data()) > 0
    return True


def main():
    user_id, admin_id = seed_data()
    try:
        job_id, job_name, delete_job_id, question_id = get_fixtures()
        specs = build_specs(user_id, admin_id, job_id, job_name, delete_job_id, question_id)
        results = []
        with app.test_client() as client:
            for method, path, kwargs, expected, kind in specs:
                resp = getattr(client, method.lower())(path, **kwargs)
                passed = resp.status_code in expected and nonempty(resp) and check_format(resp, kind)
                results.append({
                    "pass": passed,
                    "method": method,
                    "path": path,
                    "status": resp.status_code,
                    "expected": sorted(expected),
                    "content_type": resp.headers.get("Content-Type", ""),
                    "summary": summary(resp),
                })
    finally:
        AVATAR_FILE.unlink(missing_ok=True)

    print("API_AUDIT_DB", TMP_DB)
    print("API_AUDIT_TOTAL", len(results))
    print("API_AUDIT_PASS", sum(1 for r in results if r["pass"]))
    print("API_AUDIT_FAIL", sum(1 for r in results if not r["pass"]))
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"{mark}\t{r['method']}\t{r['path']}\tstatus={r['status']}\texpected={r['expected']}\t{r['content_type']}\t{r['summary']}")
    if any(not r["pass"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
