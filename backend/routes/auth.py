import json
import random
import uuid
import time
from functools import wraps

from captcha.image import ImageCaptcha
from flask import Blueprint, Response, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db


auth_bp = Blueprint("auth", __name__, url_prefix="/api")

CAPTCHA_TTL_SECONDS = 300
CAPTCHA_STORE = {}
# Keep only characters that stay readable after image distortion. The validator
# also accepts common visual confusions for older captcha rows already in SQLite.
CAPTCHA_CHARS = "ACDEFHJKLMNPRTUVWXY"
CAPTCHA_EQUIVALENTS = str.maketrans({
    "0": "O",
    "Q": "O",
    "1": "I",
    "L": "I",
    "2": "Z",
    "5": "S",
    "8": "B",
    "6": "G",
})


def _get_user_by_identifier(identifier):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE username = ? OR phone = ?",
            (identifier, identifier),
        ).fetchone()
    finally:
        conn.close()


def verify_token(token: str):
    if not token or not token.startswith("mock-token-"):
        return None
    try:
        user_id = int(token.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return None

    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def _token_from_request():
    auth = request.headers.get("Authorization", "")
    return auth.split(" ", 1)[1] if auth.startswith("Bearer ") else auth


def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = verify_token(_token_from_request())
        if not user:
            return jsonify({"error": "unauthorized"}), 401
        request.user = user
        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = verify_token(_token_from_request())
        if not user or user["role"] != "admin":
            return jsonify({"error": "admin required"}), 403
        request.user = user
        return func(*args, **kwargs)

    return wrapper


def _cleanup_captcha_store(conn=None):
    now = time.time()
    expired = [key for key, value in CAPTCHA_STORE.items() if value["expires_at"] < now]
    for key in expired:
        CAPTCHA_STORE.pop(key, None)
    if conn:
        conn.execute(
            "DELETE FROM captcha_challenges WHERE expires_at < ? OR used_at IS NOT NULL",
            (now,),
        )


def _normalize_captcha(value):
    normalized = "".join(ch for ch in str(value or "").upper() if ch.isalnum())
    return normalized.translate(CAPTCHA_EQUIVALENTS)


def _validate_captcha(captcha_input, captcha_id=None):
    if not captcha_input:
        return "请输入图形验证码"
    _cleanup_captcha_store()
    expected = None
    if captcha_id:
        conn = get_db()
        try:
            _cleanup_captcha_store(conn)
            item = conn.execute(
                """
                SELECT code
                FROM captcha_challenges
                WHERE id = ? AND expires_at >= ? AND used_at IS NULL
                """,
                (str(captcha_id), time.time()),
            ).fetchone()
            conn.commit()
            expected = item["code"] if item else None
        finally:
            conn.close()
        if not expected:
            item = CAPTCHA_STORE.get(str(captcha_id))
            expected = item["text"] if item else None
    else:
        expected = session.get("captcha")
    if not expected:
        return "验证码已刷新或过期，请点击图片重新获取"
    if _normalize_captcha(expected) != _normalize_captcha(captcha_input):
        return "图形验证码错误，请按图片重新输入"
    return None


def _consume_captcha(captcha_id=None):
    if captcha_id:
        CAPTCHA_STORE.pop(str(captcha_id), None)
        conn = get_db()
        try:
            conn.execute(
                "UPDATE captcha_challenges SET used_at = ? WHERE id = ?",
                (time.time(), str(captcha_id)),
            )
            conn.commit()
        finally:
            conn.close()
    session.pop("captcha", None)


@auth_bp.route("/captcha", methods=["GET"])
def get_captcha():
    captcha_text = "".join(random.choices(CAPTCHA_CHARS, k=4))
    captcha_id = request.args.get("captcha_id") or uuid.uuid4().hex
    if captcha_id:
        _cleanup_captcha_store()
        CAPTCHA_STORE[str(captcha_id)] = {
            "text": captcha_text,
            "expires_at": time.time() + CAPTCHA_TTL_SECONDS,
        }
        conn = get_db()
        try:
            _cleanup_captcha_store(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO captcha_challenges (id, code, expires_at, used_at)
                VALUES (?, ?, ?, NULL)
                """,
                (str(captcha_id), captcha_text, time.time() + CAPTCHA_TTL_SECONDS),
            )
            conn.commit()
        finally:
            conn.close()
    session["captcha"] = captcha_text
    image = ImageCaptcha(width=132, height=46)
    data = image.generate(captcha_text)
    response = Response(data.read(), mimetype="image/png")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@auth_bp.route("/send_code", methods=["POST"])
def send_code():
    return jsonify({"error": "sms verification is disabled"}), 410


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip()
    phone = str(data.get("phone") or "").strip() or None
    password = data.get("password")

    captcha_id = data.get("captcha_id")
    captcha_error = _validate_captcha(data.get("captcha"), captcha_id)
    if captcha_error:
        return jsonify({"error": captcha_error}), 400
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR (? IS NOT NULL AND phone = ?)",
            (username, phone, phone),
        ).fetchone()
        if existing:
            return jsonify({"error": "用户名或手机号已被注册"}), 400
        cur = conn.execute(
            "INSERT INTO users (username, phone, password_hash) VALUES (?, ?, ?)",
            (username, phone, generate_password_hash(password)),
        )
        user_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO student (
                user_id, name, major, grade, skills, certificates, internships,
                completeness, competitiveness, phone, email, education_text,
                work_text, project_text, skills_certs_text, summary,
                soft_abilities, education_json, work_json, project_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                "",
                "",
                json.dumps([], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                "",
                12,
                20,
                phone,
                "",
                "",
                "",
                "",
                "",
                "刚刚加入 Starway，建议先完善学生画像。",
                json.dumps({
                    "创新能力": {"score": 3, "description": "待通过项目经历进一步识别。"},
                    "学习能力": {"score": 3, "description": "待通过技能和证书进一步识别。"},
                    "抗压能力": {"score": 3, "description": "待通过实习和项目经历进一步识别。"},
                    "沟通能力": {"score": 3, "description": "待通过协作经历进一步识别。"},
                    "实习能力": {"score": 2, "description": "建议补充实习或项目作品。"},
                }, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
            ),
        )
        conn.commit()
        _consume_captcha(captcha_id)
        return jsonify({"id": user_id, "username": username})
    finally:
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get("username") or data.get("phone")
    password = data.get("password")

    captcha_id = data.get("captcha_id")
    captcha_error = _validate_captcha(data.get("captcha"), captcha_id)
    if captcha_error:
        return jsonify({"error": captcha_error}), 400
    if not identifier or not password:
        return jsonify({"error": "请输入用户名和密码"}), 400

    user = _get_user_by_identifier(identifier)
    if not user:
        return jsonify({"error": "账号不存在，请检查用户名或手机号"}), 404
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "密码不正确，请重新输入"}), 401

    _consume_captcha(captcha_id)
    return jsonify({
        "token": f"mock-token-{user['id']}",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    })
