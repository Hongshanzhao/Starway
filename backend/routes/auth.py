"""
用户认证与个人中心核心模块 (Auth & Profile Core Module)

本模块是整个系统的**身份验证网关**与**用户数据中枢**，负责处理用户从注册到登录的全生命周期权限管理，
同时聚合用户的档案、简历、测评报告、浏览历史等核心业务数据。

核心功能：
1. 【认证安全】提供登录、注册、验证码（功能已删）、图形验证、密码修改、头像上传等基础身份服务
2. 【权限控制】基于 Mock Token 的身份验证装饰器 (@token_required) 与管理员权限 (@admin_required)
3. 【个人中心】用户档案读写、简历解析/存储、个人信息完善
4. 【数据聚合】统一获取用户的兴趣测评、人岗匹配、职业规划等各类报告历史
5. 【行为追踪】管理用户的浏览历史记录与系统使用统计数据

废弃说明：
- 以下接口已被注释或临时禁用，属于备用/未使用代码，不会影响系统正常运行：
  1. `/user/students` (获取用户学生列表) - 已注释，无外部调用

注意事项：
- 本模块依赖 `db.py` 数据库连接及 `services/llm_service.py` 用于简历文本智能解析
- 所有接口均经过严格的权限校验，请谨慎移除装饰器
"""
import io
import random
import string
import datetime
import time
import os
import uuid
from flask import Blueprint, request, jsonify, session, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from captcha.image import ImageCaptcha
from db import get_db
from functools import wraps
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# 用于记录短信发送频率（简单内存存储，生产环境应使用Redis）
last_send_time = {}

def _get_user_by_identifier(identifier):
    """根据用户名或手机号查找用户"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR phone = ?", (identifier, identifier)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def verify_token(token: str):
    """简单的 token 验证：token 格式为 mock-token-<user_id>。返回 user row 或 None"""
    if not token or not token.startswith('mock-token-'):
        return None
    try:
        uid = int(token.split('-')[-1])
    except Exception:
        return None
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (uid,))
    user = cur.fetchone()
    conn.close()
    return user


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]
        else:
            token = auth
        user = verify_token(token)
        if not user:
            return jsonify({'error': 'unauthorized'}), 401
        # attach user to request context
        request.user = user
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]
        else:
            token = auth
        user = verify_token(token)
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'admin required'}), 403
        request.user = user
        return f(*args, **kwargs)
    return wrapper

# ---------- 图形验证码 ----------
@auth_bp.route('/captcha', methods=['GET'])
def get_captcha():
    """生成图形验证码图片"""
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    session['captcha'] = captcha_text
    image = ImageCaptcha(width=120, height=40)
    data = image.generate(captcha_text)
    return Response(data.read(), mimetype='image/png')

# ---------- 短信验证码（模拟） ----------
@auth_bp.route('/send_code', methods=['POST'])
def send_code():
    data = request.json or {}
    phone = data.get('phone')
    if not phone:
        return jsonify({'error': 'phone required'}), 400

    now = time.time()
    if phone in last_send_time and now - last_send_time[phone] < 60:
        return jsonify({'error': '发送过于频繁，请稍后再试'}), 429
    last_send_time[phone] = now

    code = f"{random.randint(0, 999999):06d}"
    expires = datetime.datetime.now() + datetime.timedelta(minutes=5)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO verification_codes (phone, code, expires_at) VALUES (?, ?, ?)",
        (phone, code, expires.isoformat())
    )
    conn.commit()
    conn.close()

    print(f"验证码 {code} 已发送至手机 {phone}")
    return jsonify({'code': code, 'message': '验证码已发送'})

# ---------- 注册 ----------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username')
    phone = data.get('phone')
    password = data.get('password')
    sms_code = data.get('code')
    captcha_input = data.get('captcha')

    if not captcha_input:
        return jsonify({'error': '请输入图形验证码'}), 400
    session_captcha = session.pop('captcha', None)
    if not session_captcha or session_captcha.lower() != captcha_input.lower():
        return jsonify({'error': '图形验证码错误'}), 400

    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    if phone and not sms_code:
        return jsonify({'error': '短信验证码不能为空'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR phone = ?",
        (username, phone if phone else '')
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({'error': '用户名或手机号已被注册'}), 400

    if phone and sms_code:
        cursor.execute(
            "SELECT code, expires_at FROM verification_codes WHERE phone = ? ORDER BY id DESC LIMIT 1",
            (phone,)
        )
        row = cursor.fetchone()
        if not row or row['code'] != sms_code:
            conn.close()
            return jsonify({'error': '短信验证码错误'}), 400
        try:
            exp = datetime.datetime.fromisoformat(row['expires_at'])
            if datetime.datetime.now() > exp:
                conn.close()
                return jsonify({'error': '短信验证码已过期'}), 400
        except Exception:
            pass
        cursor.execute("DELETE FROM verification_codes WHERE phone = ? AND code = ?", (phone, sms_code))
        conn.commit()

    pw_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, phone, password_hash) VALUES (?, ?, ?)",
        (username, phone, pw_hash)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return jsonify({'id': user_id, 'username': username})

# ---------- 登录 ----------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    identifier = data.get('username') or data.get('phone')
    password = data.get('password')
    captcha_input = data.get('captcha')

    if not captcha_input:
        return jsonify({'error': '请输入图形验证码'}), 400
    session_captcha = session.pop('captcha', None)
    if not session_captcha or session_captcha.lower() != captcha_input.lower():
        return jsonify({'error': '图形验证码错误'}), 400

    if not identifier or not password:
        return jsonify({'error': 'credentials required'}), 400

    user = _get_user_by_identifier(identifier)
    if not user:
        return jsonify({'error': 'user not found'}), 404

    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'invalid credentials'}), 401

    token = f"mock-token-{user['id']}"
    return jsonify({'token': token, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})

# ---------- 获取当前登录用户信息 ----------
@auth_bp.route('/user', methods=['GET'])
@token_required
def get_current_user():
    user = request.user
    user_data = {
        'id': user['id'],
        'username': user['username'],
        'phone': user['phone'],
        'role': user['role'],
        'is_active': user['is_active'],
        'avatar': user.get('avatar') or '',
        'created_at': user['created_at']
    }
    return jsonify(user_data)
# @auth_bp.route('/user/students')
# @token_required
# def get_user_students():
#     # 从请求上下文获取已验证的用户
#     user = request.user
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute('SELECT id FROM student WHERE user_id = ?', (user['id'],))
#     rows = cursor.fetchall()
#     conn.close()
#     return jsonify([dict(row) for row in rows])
# ---------- 用户个人信息接口（扩展） ----------
@auth_bp.route('/user/profile', methods=['GET'])
@token_required
def get_user_profile():
    user = request.user
    conn = get_db()
    cursor = conn.cursor()

    # 查询用户基本信息
    cursor.execute("SELECT id, username, phone, role, avatar, created_at FROM users WHERE id = ?", (user['id'],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({'error': '用户不存在'}), 404

    # 查询学生能力画像（可能没有）
    cursor.execute("SELECT * FROM student WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user['id'],))
    student_row = cursor.fetchone()
    conn.close()

    profile = {
        'id': user_row['id'],
        'username': user_row['username'],
        'phone': user_row['phone'],
        'role': user_row['role'],
        'avatar': user_row['avatar'] or '',
        'joinTime': user_row['created_at'],
    }

    if student_row:
        profile.update({
            'name': student_row['name'] or '',
            'realName': student_row['name'] or '',
            'gender': '',  # 暂未存储
            'school': '',  # 暂未存储
            'major': '',   # 暂未存储
            'grade': '',   # 暂未存储
            'email': student_row['email'] or '',
            'introduction': student_row['summary'] or '',
            'education_text': student_row['education_text'] or '',
            'work_text': student_row['work_text'] or '',
            'project_text': student_row['project_text'] or '',
            'skills_certs_text': student_row['skills_certs_text'] or '',
            'summary': student_row['summary'] or '',
            'skills': student_row['skills'] or '',
            'certificates': student_row['certificates'] or '',
            'soft_abilities': student_row['soft_abilities'] or '',
            'completeness': student_row['completeness'] or 0,
            'created_at': student_row['created_at'] or ''
        })
    else:
        profile.update({
            'name': '', 'realName': '', 'gender': '', 'school': '', 'major': '', 'grade': '',
            'email': '', 'introduction': '', 'education_text': '', 'work_text': '', 'project_text': '',
            'skills_certs_text': '', 'summary': '', 'skills': '', 'certificates': '', 'soft_abilities': '',
            'completeness': 0, 'created_at': ''
        })

    return jsonify(profile)

@auth_bp.route('/user/profile', methods=['PUT'])
@token_required
def update_user_profile():
    data = request.json or {}
    user = request.user
    conn = get_db()
    cursor = conn.cursor()

    # 检查 student 记录是否存在
    cursor.execute("SELECT id FROM student WHERE user_id = ?", (user['id'],))
    student_row = cursor.fetchone()
    if not student_row:
        # 创建一条空记录
        cursor.execute('''
            INSERT INTO student (user_id, name, email, completeness)
            VALUES (?, ?, ?, ?)
        ''', (user['id'], data.get('name', ''), data.get('email', ''), 0))
        student_id = cursor.lastrowid
    else:
        student_id = student_row['id']

    # 更新 student 表中允许的字段
    update_fields = []
    params = []
    allowed_fields = ['name', 'email', 'education_text', 'work_text', 'project_text',
                      'skills_certs_text', 'summary']
    for field in allowed_fields:
        if field in data:
            update_fields.append(f"{field} = ?")
            params.append(data[field])
    if update_fields:
        params.append(student_id)
        cursor.execute(f"UPDATE student SET {', '.join(update_fields)} WHERE id = ?", params)

    # 更新 users 表中的手机号（如果提供）
    if 'phone' in data:
        cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (data['phone'], user['id']))

    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@auth_bp.route('/user/avatar', methods=['POST'])
@token_required
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'empty filename'}), 400

    if not file.content_type.startswith('image/'):
        return jsonify({'error': 'invalid image type'}), 400

    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, '..', 'uploads', 'avatars')
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    avatar_url = f"/uploads/avatars/{filename}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar_url, request.user['id']))
    conn.commit()
    conn.close()

    return jsonify({'avatar': avatar_url})


@auth_bp.route('/user/change-password', methods=['POST'])
@token_required
def change_password():
    data = request.json or {}
    old_pwd = data.get('oldPwd')
    new_pwd = data.get('newPwd')
    if not old_pwd or not new_pwd:
        return jsonify({'error': 'old password and new password required'}), 400

    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user['id'],))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'user not found'}), 404

    if not check_password_hash(row['password_hash'], old_pwd):
        conn.close()
        return jsonify({'error': 'invalid old password'}), 401

    new_hash = generate_password_hash(new_pwd)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@auth_bp.route('/user/bind-phone', methods=['POST'])
@token_required
def bind_phone():
    data = request.json or {}
    phone = data.get('phone')
    code = data.get('code')
    if not phone or not code:
        return jsonify({'error': 'phone and code required'}), 400

    # 模拟验证码验证，实际应查询 verification_codes 表
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, request.user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@auth_bp.route('/user/plans', methods=['GET'])
@token_required
def get_user_plans():
    """获取用户的职业规划报告（从 report_history 表）"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    # 先获取学生 ID
    cursor.execute("SELECT id FROM student WHERE user_id = ?", (user['id'],))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        return jsonify([])

    cursor.execute('''
        SELECT id, job_name, content, format_type, created_at
        FROM report_history WHERE student_id = ? ORDER BY created_at DESC
    ''', (student_row['id'],))
    rows = cursor.fetchall()
    conn.close()
    plans = []
    for row in rows:
        plans.append({
            'id': row['id'],
            'title': f"{row['job_name']} 职业规划报告",
            'targetJob': row['job_name'],
            'cycle': '1-3年',   # 可后续从报告内容提取
            'matchRate': 0,      # 匹配度不在 report_history 中，可忽略
            'createTime': row['created_at']
        })
    return jsonify(plans)


@auth_bp.route('/user/interest-reports', methods=['GET'])
@token_required
def get_interest_reports():
    """获取用户的兴趣测试报告（从 assessment_results 表）"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, dimension_scores, recommendation, created_at
        FROM assessment_results WHERE user_id = ? ORDER BY created_at DESC
    ''', (user['id'],))
    rows = cursor.fetchall()
    conn.close()
    reports = []
    for row in rows:
        # 简单解析，实际可解析 dimension_scores 生成更友好标题
        reports.append({
            'id': row['id'],
            'title': '霍兰德职业兴趣测评报告',
            'type': '霍兰德测试',
            'result': '根据您的得分，兴趣类型偏向...',  # 可解析
            'suitableJobs': '产品经理、人力资源、心理咨询师',
            'createTime': row['created_at']
        })
    return jsonify(reports)


@auth_bp.route('/user/match-reports', methods=['GET'])
@token_required
def get_match_reports():
    """获取用户的人岗匹配报告（从 match_history 表，关联 student 表）"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    # 先获取学生 ID
    cursor.execute("SELECT id FROM student WHERE user_id = ?", (user['id'],))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        return jsonify([])

    cursor.execute('''
        SELECT id, job_name, match_score, details, created_at
        FROM match_history WHERE student_id = ? ORDER BY created_at DESC
    ''', (student_row['id'],))
    rows = cursor.fetchall()
    conn.close()
    reports = []
    for row in rows:
        details = json.loads(row['details']) if row['details'] else {}
        gap = details.get('gap_analysis', {})
        reports.append({
            'id': row['id'],
            'title': f"{row['job_name']} 匹配报告",
            'targetJob': row['job_name'],
            'score': row['match_score'],
            'result': '高度匹配' if row['match_score'] >= 80 else ('中度匹配' if row['match_score'] >= 60 else '待提升'),
            'suggestion': gap.get('skills', '请完善技能'),
            'createTime': row['created_at']
        })
    return jsonify(reports)


# ---------- 浏览历史接口（需要表 user_browse_history） ----------
@auth_bp.route('/user/history', methods=['GET'])
@token_required
def get_browse_history():
    """获取用户浏览历史"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, description, cover, created_at
        FROM user_browse_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 50
    ''', (user['id'],))
    rows = cursor.fetchall()
    conn.close()
    history = []
    for row in rows:
        history.append({
            'id': row['id'],
            'title': row['title'],
            'desc': row['description'],
            'cover': row['cover'],
            'browseTime': row['created_at']
        })
    return jsonify(history)


@auth_bp.route('/user/history', methods=['POST'])
@token_required
def add_browse_history():
    """添加一条浏览记录"""
    data = request.json or {}
    user = request.user
    title = data.get('title')
    description = data.get('desc') or ''
    cover = data.get('cover') or ''
    item_type = data.get('type', 'job')
    item_id = data.get('itemId', 0)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_browse_history (user_id, item_type, item_id, title, description, cover)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user['id'], item_type, item_id, title, description, cover))
    conn.commit()
    conn.close()
    return jsonify({'status': 'added'})


@auth_bp.route('/user/history/<int:history_id>', methods=['DELETE'])
@token_required
def delete_browse_history(history_id):
    """删除单条浏览历史"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_browse_history WHERE id = ? AND user_id = ?", (history_id, user['id']))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})


@auth_bp.route('/user/history/clear', methods=['DELETE'])
@token_required
def clear_browse_history():
    """清空浏览历史"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_browse_history WHERE user_id = ?", (user['id'],))
    conn.commit()
    conn.close()
    return jsonify({'status': 'cleared'})

@auth_bp.route('/user/stats', methods=['GET'])
@token_required
def get_user_stats():
    """获取用户统计数据：测评次数、规划方案数"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. 测评次数（assessment_results 表）
    cursor.execute("SELECT COUNT(*) as cnt FROM assessment_results WHERE user_id = ?", (user['id'],))
    assessment_count = cursor.fetchone()['cnt']
    
    # 2. 规划方案数（report_history 表关联 student）
    cursor.execute("SELECT id FROM student WHERE user_id = ?", (user['id'],))
    student_row = cursor.fetchone()
    plan_count = 0
    if student_row:
        cursor.execute("SELECT COUNT(*) as cnt FROM report_history WHERE student_id = ?", (student_row['id'],))
        plan_count = cursor.fetchone()['cnt']
    
    conn.close()
    return jsonify({
        'assessmentCount': assessment_count,
        'planCount': plan_count
    })
# ---------- 统一获取用户所有报告列表 ----------
@auth_bp.route('/user/reports', methods=['GET'])
@token_required
def get_all_reports():
    """获取当前用户的所有报告（兴趣测试、人岗匹配、职业规划）"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()

    # 1. 获取学生ID（可能为空）
    cursor.execute("SELECT id FROM student WHERE user_id = ?", (user['id'],))
    student_row = cursor.fetchone()
    student_id = student_row['id'] if student_row else None

    reports = []

    # 2. 兴趣测试报告（assessment_results）
    cursor.execute('''
        SELECT id, dimension_scores, recommendation, created_at
        FROM assessment_results
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user['id'],))
    for row in cursor.fetchall():
        # 将时间戳转换为ISO字符串（如果数据库存储的是数字时间戳）
        created_at = row['created_at']
        if isinstance(created_at, (int, float)):
            created_at = datetime.datetime.fromtimestamp(created_at).isoformat()
        reports.append({
            'id': f"interest_{row['id']}",
            'title': '霍兰德职业兴趣测评报告',
            'type': 'interest_test',
            'summary': row['recommendation'][:100] if row['recommendation'] else '兴趣类型分析报告',
            'created_at': created_at,
            'original_id': row['id'],
            'original_table': 'assessment_results'
        })

    # # 3. 人岗匹配报告（match_history，需要student_id）
    # if student_id:
    #     cursor.execute('''
    #         SELECT id, job_name, match_score, details, created_at
    #         FROM match_history
    #         WHERE student_id = ?
    #         ORDER BY created_at DESC
    #     ''', (student_id,))
    #     for row in cursor.fetchall():
    #         created_at = row['created_at']
    #         if isinstance(created_at, (int, float)):
    #             created_at = datetime.datetime.fromtimestamp(created_at).isoformat()
    #         reports.append({
    #             'id': f"match_{row['id']}",
    #             'title': f"{row['job_name']} 人岗匹配报告",
    #             'type': 'job_match',
    #             'summary': f"匹配度: {row['match_score']}%",
    #             'created_at': created_at,
    #             'original_id': row['id'],
    #             'original_table': 'match_history'
    #         })

    # 4. 职业规划报告（report_history，需要student_id）
    if student_id:
        cursor.execute('''
            SELECT id, job_name, content, format_type, created_at
            FROM report_history
            WHERE student_id = ?
            ORDER BY created_at DESC
        ''', (student_id,))
        for row in cursor.fetchall():
            created_at = row['created_at']
            if isinstance(created_at, (int, float)):
                created_at = datetime.datetime.fromtimestamp(created_at).isoformat()
            content = row['content'] or ''
            summary = (content[:100] + '...') if len(content) > 100 else content
            reports.append({
                'id': f"plan_{row['id']}",
                'title': f"{row['job_name']} 职业规划报告",
                'type': 'career_plan',
                'summary': summary,
                'created_at': created_at,
                'original_id': row['id'],
                'original_table': 'report_history'
            })

    conn.close()

    # 按创建时间倒序排序（已按数据库顺序，但为了保险再排一次）
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(reports)
# ==========================
# ✅ 添加到 auth.py 末尾
# ==========================

# 1. 删除职业规划报告
@auth_bp.route('/user/report/career/<int:report_id>', methods=['DELETE'])
@token_required
def delete_career_report(report_id):
    """删除职业规划报告"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()

    try:
        # 验证报告属于当前用户
        cursor.execute('''
            SELECT r.id FROM report_history r
            JOIN student s ON r.student_id = s.id
            WHERE r.id = ? AND s.user_id = ?
        ''', (report_id, user['id']))
        
        if not cursor.fetchone():
            return jsonify({'error': '报告不存在或无权限'}), 404

        cursor.execute("DELETE FROM report_history WHERE id = ?", (report_id,))
        conn.commit()
        
        return jsonify({'status': 'deleted', 'message': '职业规划报告已删除'})
    
    except Exception as e:
        print(f"删除职业规划报告失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# 2. 删除兴趣测评报告
@auth_bp.route('/user/report/interest/<int:result_id>', methods=['DELETE'])
@token_required
def delete_interest_report(result_id):
    """删除兴趣测评报告"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id FROM assessment_results
            WHERE id = ? AND user_id = ?
        ''', (result_id, user['id']))
        
        if not cursor.fetchone():
            return jsonify({'error': '报告不存在或无权限'}), 404

        cursor.execute("DELETE FROM assessment_results WHERE id = ?", (result_id,))
        conn.commit()
        
        return jsonify({'status': 'deleted', 'message': '兴趣测评报告已删除'})
    
    except Exception as e:
        print(f"删除兴趣测评报告失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# 3. 删除人岗匹配报告
@auth_bp.route('/user/report/match/<int:match_id>', methods=['DELETE'])
@token_required
def delete_match_report(match_id):
    """删除人岗匹配报告"""
    user = request.user
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT m.id FROM match_history m
            JOIN student s ON m.student_id = s.id
            WHERE m.id = ? AND s.user_id = ?
        ''', (match_id, user['id']))
        
        if not cursor.fetchone():
            return jsonify({'error': '报告不存在或无权限'}), 404

        cursor.execute("DELETE FROM match_history WHERE id = ?", (match_id,))
        conn.commit()
        
        return jsonify({'status': 'deleted', 'message': '人岗匹配报告已删除'})
    
    except Exception as e:
        print(f"删除人岗匹配报告失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

    