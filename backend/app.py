import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory

try:
    from flask_cors import CORS
except ImportError:
    def CORS(*args, **kwargs):
        return None

from config import UPLOAD_FOLDER
from db import get_db, init_db
from routes import register_blueprints


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "..")))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["UPLOAD_FOLDER"] = "uploads"
app.static_folder = "uploads"
app.static_url_path = "/uploads"

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002",
            ],
            "supports_credentials": True,
        }
    },
)

with app.app_context():
    init_db()

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

register_blueprints(app)


@app.route("/")
def home():
    return jsonify({"message": "Starway backend is running", "database": "SQLite"})


@app.route("/test-db")
def test_db():
    try:
        conn = get_db()
        conn.close()
        return jsonify({"status": "ok", "message": "database connected"})
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@app.route("/uploads/avatars/<filename>")
def get_avatar(filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, "avatars"), filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
