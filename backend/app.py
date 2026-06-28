import sys
import os
from dotenv import load_dotenv

# ✅ 先加载环境变量，再导入其他模块
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 把项目根目录（frontend）加入 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from db import get_db, init_db
from config import UPLOAD_FOLDER
from routes import register_blueprints

app = Flask(__name__)
# 设置 secret key（必须，用于 session 存储）
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

app.config['UPLOAD_FOLDER'] = 'uploads'
app.static_folder = 'uploads'
app.static_url_path = '/uploads'

# ✅ 修复 1：配置 CORS 允许 credentials（保留 Cookie/Session）
CORS(
    app,
    resources={r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],  # 允许前端所有可能的端口
        "supports_credentials": True  # 核心：允许跨域传递 Cookie/Session
    }}
)

# 初始化数据库
with app.app_context():
    init_db()

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 注册所有蓝图（路由）
register_blueprints(app)

# 保留根路由和测试路由（方便直接验证）
@app.route('/')
def home():
    return jsonify({"message": "后端运行成功，使用 SQLite 数据库"})

@app.route('/test-db')
def test_db():
    try:
        conn = get_db()
        return jsonify({"status": "数据库连接成功", "db_path": str(conn)})
    except Exception as e:
        return jsonify({"status": "连接失败", "error": str(e)})

# ====================== 【唯一头像修复：只加这一段，不动你任何代码】 ======================
@app.route('/uploads/avatars/<filename>')
def get_avatar(filename):
    return send_from_directory(UPLOAD_FOLDER + '/avatars', filename)
# =========================================================================================

if __name__ == '__main__':
    # ✅ 修复 2：关闭 debug 避免多进程 + 修复 3：绑定 IPv4
    app.run(
        host='127.0.0.1',  # 明确绑定 IPv4，和前端代理匹配
        port=5000,
        debug=False  # 必须关闭 debug，避免多进程会话混乱
    )