import random
import string
from functools import wraps

from captcha.image import ImageCaptcha
from flask import Blueprint, Response, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db


auth_bp = Blueprint("auth", __name__, url_prefix="/api")


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


def _validate_captcha(captcha_input):
    if not captcha_input:
        return "请输入图形验证码"
    expected = session.pop("captcha", None)
    if not expected or expected.lower() != captcha_input.lower():
        return "图形验证码错误"
    return None


@auth_bp.route("/captcha", methods=["GET"])
def get_captcha():
    captcha_text = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    session["captcha"] = captcha_text
    image = ImageCaptcha(width=120, height=40)
    data = image.generate(captcha_text)
    return Response(data.read(), mimetype="image/png")


@auth_bp.route("/send_code", methods=["POST"])
def send_code():
    return jsonify({"error": "sms verification is disabled"}), 410


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    phone = data.get("phone")
    password = data.get("password")

    captcha_error = _validate_captcha(data.get("captcha"))
    if captcha_error:
        return jsonify({"error": captcha_error}), 400
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR phone = ?",
            (username, phone or ""),
        ).fetchone()
        if existing:
            return jsonify({"error": "用户名或手机号已被注册"}), 400
        cur = conn.execute(
            "INSERT INTO users (username, phone, password_hash) VALUES (?, ?, ?)",
            (username, phone, generate_password_hash(password)),
        )
        conn.commit()
        return jsonify({"id": cur.lastrowid, "username": username})
    finally:
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get("username") or data.get("phone")
    password = data.get("password")

    captcha_error = _validate_captcha(data.get("captcha"))
    if captcha_error:
        return jsonify({"error": captcha_error}), 400
    if not identifier or not password:
        return jsonify({"error": "credentials required"}), 400

    user = _get_user_by_identifier(identifier)
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
