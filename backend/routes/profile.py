import json
import os
import re
import tempfile

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from db import get_db
from services.career_ai_service import call_llm
from services.ml_recommender import split_skills


profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "md"}
REQUIRED_SOFT_ABILITIES = {
    "创新能力": {"score": 3, "description": "能主动尝试新方法解决问题。"},
    "学习能力": {"score": 4, "description": "能持续学习岗位相关知识。"},
    "抗压能力": {"score": 3, "description": "能在项目周期内稳定推进任务。"},
    "沟通能力": {"score": 3, "description": "能清晰表达并协作完成任务。"},
    "实习能力": {"score": 3, "description": "具备基础实践意识，可通过项目继续提升。"},
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def ensure_required_soft_abilities(soft_abilities):
    result = dict(REQUIRED_SOFT_ABILITIES)
    if isinstance(soft_abilities, dict):
        result.update({k: v for k, v in soft_abilities.items() if v})
    return result


def _rule_extract_profile(text, data=None):
    data = data or {}
    skills = split_skills(data.get("skills_certs") or data.get("skills") or "")
    skills += [s for s in ["Python", "Java", "SQL", "Vue", "React", "Flask", "Docker"] if s.lower() in text.lower()]
    skills = list(dict.fromkeys(skills))
    certs = [item for item in split_skills(data.get("skills_certs") or "") if "证" in item or "PMP" in item.upper()]
    education = data.get("education", "")
    work = data.get("work", "")
    project = data.get("project", "")
    return {
        "skills": skills,
        "certificates": certs,
        "soft_abilities": ensure_required_soft_abilities({}),
        "education": _parse_education(education),
        "work_experience": _parse_list_text(work, ["company", "position", "description"]),
        "project_experience": _parse_list_text(project, ["project_name", "role", "description"]),
    }


def _parse_education(text):
    if not text:
        return {}
    degree = ""
    for item in ["博士", "硕士", "本科", "大专", "专科"]:
        if item in text:
            degree = item
            break
    return {"school": text[:30], "major": "", "degree": degree}


def _parse_list_text(text, keys):
    if not text:
        return []
    item = {keys[0]: text[:30], keys[1]: "", keys[2]: text}
    return [item]


def _extract_with_llm(text, data=None):
    prompt = f"""
请从以下大学生简历/档案文本中抽取结构化 JSON：
字段：skills, certificates, soft_abilities, education, work_experience, project_experience。
只返回 JSON。

文本：
{text}
"""
    try:
        raw = call_llm(prompt, temperature=0.2, max_tokens=1800)
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(raw[start:end + 1])
            parsed["soft_abilities"] = ensure_required_soft_abilities(parsed.get("soft_abilities"))
            return parsed
    except Exception:
        pass
    return _rule_extract_profile(text, data)


@profile_bp.route("/submit", methods=["POST"])
def submit_profile():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    text = "\n".join(str(data.get(k, "")) for k in ["education", "work", "project", "skills_certs", "summary"])
    ability = _extract_with_llm(text, data)
    major = data.get("major") or ability.get("education", {}).get("major", "")

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO student (
                user_id, name, major, grade, skills, certificates, internships,
                interests, completeness, competitiveness, phone, email,
                education_text, work_text, project_text, skills_certs_text, summary,
                soft_abilities, education_json, work_json, project_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data.get("name"),
                major,
                data.get("grade") or ability.get("education", {}).get("degree", ""),
                json.dumps(ability.get("skills", []), ensure_ascii=False),
                json.dumps(ability.get("certificates", []), ensure_ascii=False),
                data.get("work", ""),
                json.dumps(data.get("interests", []), ensure_ascii=False),
                80,
                70,
                data.get("phone"),
                data.get("email"),
                data.get("education", ""),
                data.get("work", ""),
                data.get("project", ""),
                data.get("skills_certs", ""),
                data.get("summary", ""),
                json.dumps(ability.get("soft_abilities", {}), ensure_ascii=False),
                json.dumps(ability.get("education", {}), ensure_ascii=False),
                json.dumps(ability.get("work_experience", []), ensure_ascii=False),
                json.dumps(ability.get("project_experience", []), ensure_ascii=False),
            ),
        )
        conn.commit()
        student_id = cur.lastrowid
    finally:
        conn.close()

    return jsonify({
        "student_id": student_id,
        "skills": ability.get("skills", []),
        "certificates": ability.get("certificates", []),
        "soft_abilities": ability.get("soft_abilities", {}),
    })


@profile_bp.route("/upload", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "缺少文件"}), 400
    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "不支持的文件类型"}), 400
    filename = secure_filename(file.filename)
    suffix = filename.rsplit(".", 1)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        file.save(tmp.name)
        temp_path = tmp.name
    try:
        text = _read_resume_text(temp_path, suffix)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
    ability = _extract_with_llm(text)
    return jsonify({
        "text": text,
        "skills": ability.get("skills", []),
        "certificates": ability.get("certificates", []),
        "soft_abilities": ability.get("soft_abilities", {}),
        "education_json": ability.get("education", {}),
        "work_json": ability.get("work_experience", []),
        "project_json": ability.get("project_experience", []),
    })


def _read_resume_text(path, suffix):
    if suffix in {"txt", "md"}:
        return open(path, "r", encoding="utf-8", errors="ignore").read()
    if suffix == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:
            raise RuntimeError(f"PDF 解析失败: {exc}")
    if suffix in {"doc", "docx"}:
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as exc:
            raise RuntimeError(f"Word 解析失败: {exc}")
    return ""


@profile_bp.route("/<int:student_id>", methods=["GET"])
def get_profile(student_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM student WHERE id = ?", (student_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "学生不存在"}), 404
    data = dict(row)
    for key, default in [
        ("skills", []),
        ("certificates", []),
        ("soft_abilities", {}),
        ("education_json", {}),
        ("work_json", []),
        ("project_json", []),
        ("interest_scores", {}),
    ]:
        data[key] = _json_loads(data.get(key), default)
    return jsonify(data)
