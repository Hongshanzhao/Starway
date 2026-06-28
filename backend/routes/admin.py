"""
管理员后台接口蓝图（admin_bp）
功能：提供管理员登录、用户管理、岗位管理、报告管理、AI 岗位聚类/画像/图谱构建等后台接口。

重要说明：
1. 本文件包含项目迭代过程中的所有后台管理接口，部分接口为历史版本或废弃功能，未实际使用；
2. 文件中涉及【短信验证码】相关逻辑已废弃，当前系统未启用，仅保留代码不删除；
3. 部分 AI 聚类、岗位分类功能为早期设计，当前主程序未使用；
4. 核心在用接口：管理员登录、用户增删改查、岗位管理、报告管理；
5. 废弃/未使用：验证码发送、部分 AI 自动分类接口；
6. 所有代码均为历史迭代保留，不影响当前系统正常运行。
"""
from flask import Blueprint, request, jsonify
from db import get_db
from .auth import admin_required, verify_token
from services.llm_service import (
    cluster_categories_with_zhipu,
    assign_categories_by_keywords,
    generate_category_profile_with_zhipu
)
from services.llm_service import rebuild_job_graph
import json
import time

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ====================== 登录 ======================
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'credentials required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()
    if not user:
        return jsonify({'error': 'user not found'}), 404
    from werkzeug.security import check_password_hash
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'invalid credentials'}), 401

    # 统一返回 user.id，普通用户也能拿到
    token = f"mock-token-{user['id']}"
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
    })


# ====================== 用户管理 ======================
@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, phone, role, is_active, created_at FROM users')
    rows = cur.fetchall()
    conn.close()
    users = [dict(r) for r in rows]
    return jsonify({'total': len(users), 'users': users})


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, phone, role, is_active, created_at FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(row))


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.json or {}
    fields = []
    vals = []
    for k in ('username', 'phone', 'role', 'is_active'):
        if k in data:
            fields.append(f"{k} = ?")
            vals.append(data[k])
    if not fields:
        return jsonify({'error': 'no fields provided'}), 400
    vals.append(user_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", tuple(vals))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

# ====================== 岗位大类管理 ======================
@admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description FROM job_categories")
    rows = cur.fetchall()
    conn.close()
    list_data = [dict(row) for row in rows]
    return jsonify({"list": list_data})


@admin_bp.route('/categories', methods=['POST'])
@admin_required
def add_category():
    data = request.json or {}
    name = data.get("name")
    desc = data.get("description", "")
    if not name:
        return jsonify({"error": "name required"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO job_categories (name, description) VALUES (?, ?)", (name, desc))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@admin_bp.route('/categories/<int:cid>', methods=['DELETE'])
@admin_required
def delete_category(cid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM job_categories WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


# ====================== 岗位数据管理 ======================
@admin_bp.route('/jobs', methods=['GET'])
@admin_required
def get_all_jobs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT 
            job.rowid as id,
            job.job_name,
            job.location,
            job.salary_range,
            job.company,
            job.industry,
            job.company_size,
            job.company_type,
            job.job_code,
            job.job_description,
            job.updated_at,
            job.company_info,
            job.source_url,
            job.category_id,
            job_categories.name as category_name
        FROM job
        LEFT JOIN job_categories ON job.category_id = job_categories.id
    ''')
    rows = cur.fetchall()
    conn.close()
    jobs = [dict(r) for r in rows]
    return jsonify({"list": jobs})


@admin_bp.route('/jobs', methods=['POST'])
@admin_required
def add_job():
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO job (
            job_name, location, salary_range, company, industry,
            company_size, company_type, job_code, job_description,
            company_info, source_url, updated_at, category_id
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        data.get('job_name'),
        data.get('location'),
        data.get('salary_range'),
        data.get('company'),
        data.get('industry'),
        data.get('company_size'),
        data.get('company_type'),
        data.get('job_code'),
        data.get('job_description'),
        data.get('company_info'),
        data.get('source_url'),
        data.get('updated_at'),
        data.get('category_id')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@admin_bp.route('/jobs/<int:jid>', methods=['PUT'])
@admin_required
def update_job(jid):
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE job SET
            job_name=?, location=?, salary_range=?, company=?, industry=?,
            company_size=?, company_type=?, job_code=?, job_description=?,
            company_info=?, source_url=?, updated_at=?, category_id=?
        WHERE rowid=?
    ''', (
        data.get('job_name'),
        data.get('location'),
        data.get('salary_range'),
        data.get('company'),
        data.get('industry'),
        data.get('company_size'),
        data.get('company_type'),
        data.get('job_code'),
        data.get('job_description'),
        data.get('company_info'),
        data.get('source_url'),
        data.get('updated_at'),
        data.get('category_id'),
        jid
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@admin_bp.route('/jobs/<int:jid>', methods=['DELETE'])
@admin_required
def delete_job(jid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM job WHERE rowid = ?", (jid,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


# ====================== AI 自动聚类 ======================
@admin_bp.route('/cluster-categories', methods=['POST'])
@admin_required
def cluster_categories():
    data = request.get_json() or {}
    sample_size = data.get('sample_size', 500)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM job_categories")
    conn.commit()
    conn.close()

    categories = cluster_categories_with_zhipu(sample_size)
    if not categories:
        return jsonify({'error': '聚类失败，未获得有效结果'}), 500

    conn = get_db()
    cursor = conn.cursor()
    category_job_titles_map = {}
    for cat in categories:
        cat_name = cat.get('category_name')
        job_titles = cat.get('job_titles', [])
        if not cat_name:
            continue
        cursor.execute("INSERT INTO job_categories (name) VALUES (?)", (cat_name,))
        conn.commit()
        cat_id = cursor.lastrowid
        category_job_titles_map[cat_name] = job_titles
    conn.close()

    assigned_count = assign_categories_by_keywords(category_job_titles_map)

    return jsonify({
        'message': f'聚类完成，生成了 {len(categories)} 个大类，已为 {assigned_count} 个岗位分配类别',
        'categories': categories
    })

# ====================== AI 生成所有大类画像 ======================
@admin_bp.route('/generate-all-category-profiles', methods=['POST'])
@admin_required
def generate_all_category_profiles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM job_categories")
    cat_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()

    success = []
    for cat_id in cat_ids:
        if generate_category_profile_with_zhipu(cat_id):
            success.append(cat_id)

    return jsonify({
        'message': f'成功生成 {len(success)} 个大类画像',
        'success_ids': success
    })
# ====================== AI 构建晋升&换岗图谱 ======================
@admin_bp.route('/build-job-graph', methods=['POST'])
@admin_required
def build_job_graph():
    try:
        v_count, l_count = rebuild_job_graph()
        return jsonify({
            'success': True,
            'message': f'图谱重建完成，新增垂直路径 {v_count} 条，横向路径 {l_count} 条'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== 报告管理接口 ==========
@admin_bp.route('/reports', methods=['GET'])
@admin_required
def list_reports():
    """获取所有报告列表（分页，可按学生筛选）"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    student_id = request.args.get('student_id', type=int)

    if page < 1 or size < 1:
        return jsonify({'error': '分页参数无效'}), 400

    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []
    if student_id:
        conditions.append("student_id = ?")
        params.append(student_id)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    count_sql = f"SELECT COUNT(*) as total FROM report_history {where_clause}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()['total']

    offset = (page - 1) * size
    sql = f"""
        SELECT id, student_id, job_name, content, format_type, created_at
        FROM report_history {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(sql, params + [size, offset])
    rows = cursor.fetchall()
    conn.close()

    reports = [dict(row) for row in rows]
    return jsonify({
        'total': total,
        'page': page,
        'size': size,
        'items': reports
    })


@admin_bp.route('/reports/<int:report_id>', methods=['GET'])
@admin_required
def get_report(report_id):
    """获取单个报告详情"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM report_history WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': '报告不存在'}), 404
    return jsonify(dict(row))


@admin_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@admin_required
def delete_report(report_id):
    """删除报告"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM report_history WHERE id = ?", (report_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': '报告不存在'}), 404
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})


@admin_bp.route('/users/<int:user_id>/reports', methods=['GET'])
@admin_required
def get_user_reports(user_id):
    """获取指定用户的所有报告（分页）"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)

    if page < 1 or size < 1:
        return jsonify({'error': '分页参数无效'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM report_history WHERE student_id = ?", (user_id,))
    total = cursor.fetchone()['total']

    offset = (page - 1) * size
    cursor.execute("""
        SELECT id, student_id, job_name, content, format_type, created_at
        FROM report_history
        WHERE student_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, size, offset))
    rows = cursor.fetchall()
    conn.close()

    reports = [dict(row) for row in rows]
    return jsonify({
        'total': total,
        'page': page,
        'size': size,
        'items': reports
    })