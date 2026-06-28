"""
岗位管理接口核心蓝图
功能：提供岗位相关的全部API接口，包括岗位查询、搜索、详情、画像生成、职业发展路径（垂直晋升/横向转型）、岗位关系图谱等

重要说明：
1. 本文件为系统核心岗位服务模块，所有前端岗位相关请求均由此处理；
2. 包含标准化岗位名称、AI动态生成岗位画像、自动生成职业晋升/转型路径、数据库缓存AI结果等核心功能；
3. 依赖llm_service服务完成AI画像生成、技能提取、职业路径规划；
4. 接口遵循RESTful风格，统一前缀 /api/jobs，返回格式均为JSON；
5. 数据库表依赖：job、job_categories、job_profile、job_relations，所有表均会自动读写与缓存；
6. 职业路径支持数据库已有路径优先 + AI动态生成兜底，已兼容 C/C++、C#、.NET 等带特殊符号的岗位名称，规避特殊字符导致AI生成、数据库查询、路由解析异常问题，保证全量岗位正常返回发展图谱。
"""
from flask import Blueprint, request, jsonify
from db import get_db
import json
import re
import time
from services.llm_service import generate_dynamic_job_profile, call_llm
from services.llm_service import get_job_skills, get_job_category
from services.dl_models import JobPathRecommender
import os

job_bp = Blueprint('job', __name__, url_prefix='/api/jobs')

# ========== 岗位名称安全清洗（兼容特殊符号：/ + # . 等，不改动原有业务） ==========
def _safe_job_name(job_name):
    """
    清洗岗位特殊字符，解决 C/C++、C#、.NET 等名称
    路由/数据库查询/AI解析失败问题，纯预处理，不修改原始展示名称
    """
    if not job_name:
        return job_name
    job_name = job_name.replace('/', ' ')
    job_name = job_name.replace('+', ' ')
    job_name = job_name.replace('#', ' ')
    job_name = job_name.replace('.', ' ')
    job_name = job_name.replace('&', ' ')
    job_name = job_name.replace('(', ' ')
    job_name = job_name.replace(')', ' ')
    job_name = re.sub(r'\s+', ' ', job_name).strip()
    return job_name

# ========== 岗位名称标准化函数 ==========
def _normalize_job_name(job_name):
    """标准化岗位名称，用于数据库查询（不区分大小写）"""
    if not job_name:
        return job_name
    job_name = _safe_job_name(job_name)
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT job_name FROM job WHERE LOWER(job_name) = LOWER(?) LIMIT 1", (job_name,))
        row = cursor.fetchone()
        if row:
            return row['job_name']
        cursor.execute("SELECT job_name FROM job WHERE LOWER(job_name) LIKE LOWER(?) LIMIT 1", (f'%{job_name}%',))
        row = cursor.fetchone()
        if row:
            return row['job_name']
        return job_name
    except Exception as e:
        print(f"标准化岗位名称失败: {e}")
        return job_name
    finally:
        if conn:
            conn.close()

# ========== 深度学习路径推荐模型（懒加载） ==========
_dl_path_recommender = None

def get_path_recommender():
    global _dl_path_recommender
    if _dl_path_recommender is None:
        model_path = 'data/models/job2vec_model.pkl'
        if os.path.exists(model_path):
            try:
                _dl_path_recommender = JobPathRecommender(model_path)
                print("✅ Job2Vec 路径推荐模型加载成功")
            except Exception as e:
                print(f"⚠️ 加载Job2Vec模型失败: {e}")
    return _dl_path_recommender

# ========== 原有接口 ==========
@job_bp.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, icon, description, skills, certificates, soft_abilities
        FROM job_categories ORDER BY id
    ''')
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'name': row['name'],
            'icon': row['icon'],
            'description': row['description'],
            'skills': json.loads(row['skills']) if row['skills'] else [],
            'certificates': json.loads(row['certificates']) if row['certificates'] else [],
            'soft_abilities': json.loads(row['soft_abilities']) if row['soft_abilities'] else {}
        })
    conn.close()
    return jsonify(result)

@job_bp.route('/<int:job_id>', methods=['GET'])
def get_job_detail(job_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rowid as id, job_name, location, salary_range, company, industry,
               company_size, company_type, job_code, job_description,
               updated_at, company_info, source_url
        FROM job WHERE rowid = ?
    ''', (job_id,))
    job = cursor.fetchone()
    conn.close()
    if not job:
        return jsonify({'error': '岗位不存在'}), 404
    return jsonify(dict(job))

@job_bp.route('/profile/<path:job_name>', methods=['GET'])
def get_job_profile_by_name(job_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rowid as id, job_name, location, salary_range, company, industry,
               company_size, company_type, job_code, job_description,
               updated_at, company_info, source_url, category_id
        FROM job WHERE job_name = ? LIMIT 1
    ''', (job_name,))
    job = cursor.fetchone()
    if not job:
        conn.close()
        return jsonify({'error': '岗位不存在'}), 404
    job_dict = dict(job)

    if job_dict.get('category_id'):
        cursor.execute('''
            SELECT name, skills, certificates, soft_abilities
            FROM job_categories WHERE id = ?
        ''', (job_dict['category_id'],))
        category = cursor.fetchone()
        if category:
            job_dict['category_profile'] = {
                'name': category['name'],
                'skills': json.loads(category['skills']) if category['skills'] else [],
                'certificates': json.loads(category['certificates']) if category['certificates'] else [],
                'soft_abilities': json.loads(category['soft_abilities']) if category['soft_abilities'] else {}
            }
    conn.close()
    return jsonify(job_dict)

@job_bp.route('/graph', methods=['GET'])
def get_job_graph():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT from_job, to_job, relation_type, description FROM job_relations')
    edges = cursor.fetchall()
    nodes_set = set()
    for e in edges:
        nodes_set.add(e['from_job'])
        nodes_set.add(e['to_job'])
    nodes = [{'id': n, 'label': n} for n in nodes_set]
    conn.close()
    return jsonify({'nodes': nodes, 'edges': [dict(e) for e in edges]})

@job_bp.route('/industries', methods=['GET'])
def get_industries():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT industry FROM job WHERE industry IS NOT NULL AND industry != "" ORDER BY industry')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([row['industry'] for row in rows])

@job_bp.route('/search', methods=['GET'])
def search_jobs():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '', type=str)
    industry = request.args.get('industry', '', type=str)
    company_size = request.args.get('company_size', '', type=str)
    order = request.args.get('order', 'asc')

    if page < 1 or size < 1:
        return jsonify({'error': '分页参数无效'}), 400

    order_sql = 'ASC' if order.lower() == 'asc' else 'DESC'
    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []
    if keyword:
        conditions.append("(job_name LIKE ? OR company LIKE ?)")
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if industry:
        conditions.append("industry = ?")
        params.append(industry)
    if company_size:
        conditions.append("company_size = ?")
        params.append(company_size)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    count_sql = f"SELECT COUNT(*) as total FROM job {where_clause}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()['total']

    sql = f"""
        SELECT rowid as id, job_name, location, salary_range, company,
               industry, company_size, company_type
        FROM job {where_clause}
        ORDER BY rowid {order_sql}
        LIMIT ? OFFSET ?
    """
    offset = (page - 1) * size
    cursor.execute(sql, params + [size, offset])
    rows = cursor.fetchall()
    conn.close()
    items = [dict(row) for row in rows]
    return jsonify({'total': total, 'page': page, 'size': size, 'items': items})

@job_bp.route('/simple_search', methods=['GET'])
def simple_search():
    keyword = request.args.get('keyword', '', type=str)
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    offset = (page - 1) * size

    conn = get_db()
    cursor = conn.cursor()
    if keyword:
        cursor.execute('''
            SELECT rowid as id, job_name, company, salary_range, location
            FROM job WHERE job_name LIKE ? OR company LIKE ?
            ORDER BY rowid LIMIT ? OFFSET ?
        ''', (f'%{keyword}%', f'%{keyword}%', size, offset))
    else:
        cursor.execute('''
            SELECT rowid as id, job_name, company, salary_range, location
            FROM job ORDER BY rowid LIMIT ? OFFSET ?
        ''', (size, offset))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ========== 岗位画像 ==========
@job_bp.route('/<int:job_id>/profile', methods=['GET'])
def get_job_profile(job_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rowid as id, job_name, job_description, category_id
            FROM job WHERE rowid = ?
        ''', (job_id,))
        job = cursor.fetchone()
        if not job:
            return jsonify({'error': '岗位不存在'}), 404

        job_name = job['job_name']
        category_id = job['category_id']

        cursor.execute('''
            SELECT skills, certificates, soft_abilities
            FROM job_profile WHERE job_name = ?
        ''', (job_name,))
        existing = cursor.fetchone()

        if existing:
            profile = {
                'job_name': job_name,
                'skills': json.loads(existing['skills']) if existing['skills'] else [],
                'certificates': json.loads(existing['certificates']) if existing['certificates'] else [],
                'soft_abilities': json.loads(existing['soft_abilities']) if existing['soft_abilities'] else {},
                'source': 'job_profile'
            }
        else:
            dynamic = generate_dynamic_job_profile(job_name)
            if not dynamic:
                return jsonify({'error': '无法生成画像'}), 404

            cursor.execute('''
                INSERT OR REPLACE INTO job_profile (job_name, skills, certificates, soft_abilities)
                VALUES (?, ?, ?, ?)
            ''', (
                job_name,
                json.dumps(dynamic.get('skills', [])),
                json.dumps(dynamic.get('certificates', [])),
                json.dumps(dynamic.get('soft_abilities', {}))
            ))
            conn.commit()
            profile = {
                'job_name': job_name,
                'skills': dynamic.get('skills', []),
                'certificates': dynamic.get('certificates', []),
                'soft_abilities': dynamic.get('soft_abilities', {}),
                'source': 'dynamic'
            }

        if category_id:
            cursor.execute('''
                SELECT name, skills, certificates, soft_abilities
                FROM job_categories WHERE id = ?
            ''', (category_id,))
            cat = cursor.fetchone()
            if cat:
                profile['category_reference'] = {
                    'category_name': cat['name'],
                    'skills': json.loads(cat['skills']) if cat['skills'] else [],
                    'certificates': json.loads(cat['certificates']) if cat['certificates'] else [],
                    'soft_abilities': json.loads(cat['soft_abilities']) if cat['soft_abilities'] else {}
                }
        return jsonify(profile)
    except Exception as e:
        print(f"获取岗位画像失败: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ========== 垂直发展路径 ==========
def _get_career_path_internal(job_name):
    """内部函数：获取完整垂直发展路径"""
    safe_name = _safe_job_name(job_name)
    normalized_name = _normalize_job_name(safe_name)
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        chain = []
        current = normalized_name
        visited = set()
        while current and current not in visited:
            visited.add(current)
            cursor.execute('''
                SELECT to_job, description FROM job_relations
                WHERE from_job = ? AND relation_type = 'promotion' LIMIT 1
            ''', (current,))
            row = cursor.fetchone()
            if not row:
                break
            chain.append({
                'from_job': current,
                'to_job': row['to_job'],
                'description': row['description']
            })
            current = row['to_job']

        if chain:
            return {'success': True, 'source': 'database', 'job_name': normalized_name, 'path': chain}

        print(f"🤖 正在为岗位 [{normalized_name}] 动态生成垂直晋升路径...")
        prompt = f"""
你是一位资深的职业规划专家。请为【{normalized_name}】岗位生成一条完整的、连续的晋升发展路径。
要求：
1. 输出一个JSON数组，包含从当前岗位开始的连续晋升路径
2. 每个元素包含：job_name（岗位名称）、description（该岗位的简要描述）
3. 路径长度：3-5个节点（包含当前岗位）
4. 必须是真实存在、行业通用的岗位名称
只返回JSON数组，不要其他文字。
"""
        result = call_llm(prompt, temperature=0.3, max_tokens=1500)
        if not result:
            raise ValueError("AI 返回空结果")
        json_match = re.search(r'\[\s\S]*?\]', result)
        if json_match:
            result = json_match.group(0)
        path_data = json.loads(result)
        if not isinstance(path_data, list) or len(path_data) < 2:
            raise ValueError("返回格式不正确")

        formatted_path = []
        current = normalized_name
        for i, item in enumerate(path_data):
            if i == 0:
                continue
            formatted_path.append({
                'from_job': current,
                'to_job': item['job_name'],
                'description': item.get('description', '')
            })
            current = item['job_name']

        conn2 = None
        cursor2 = None
        try:
            conn2 = get_db()
            cursor2 = conn2.cursor()
            for item in formatted_path:
                cursor2.execute('''
                    INSERT OR REPLACE INTO job_relations (from_job, to_job, relation_type, description)
                    VALUES (?, ?, ?, ?)
                ''', (item['from_job'], item['to_job'], 'promotion', item['description']))
            conn2.commit()
        finally:
            if cursor2:
                cursor2.close()
            if conn2:
                conn2.close()
        return {'success': True, 'source': 'ai_generated', 'job_name': normalized_name, 'path': formatted_path}
    except Exception as e:
        print(f"❌ 生成垂直路径失败: {e}")
        default_path = [
            {'from_job': normalized_name, 'to_job': f'高级{normalized_name}', 'description': f'从{normalized_name}晋升至高级{normalized_name}'},
            {'from_job': f'高级{normalized_name}', 'to_job': f'{normalized_name}专家', 'description': f'从高级{normalized_name}晋升至{normalized_name}专家'}
        ]
        return {'success': True, 'source': 'default', 'job_name': normalized_name, 'path': default_path}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ========== 横向发展路径 ==========
def _get_lateral_path_internal(job_name):
    """内部函数：获取横向发展路径，确保至少2条"""
    safe_name = _safe_job_name(job_name)
    normalized_name = _normalize_job_name(safe_name)
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT to_job, description FROM job_relations
            WHERE from_job = ? AND relation_type = 'transition' ORDER BY id
        ''', (normalized_name,))
        existing = cursor.fetchall()
        existing_paths = []
        for row in existing:
            existing_paths.append({
                'job_name': row['to_job'],
                'description': row['description']
            })

        # 如果已有路径 >= 2 条，直接返回
        if len(existing_paths) >= 2:
            return {'success': True, 'source': 'database', 'job_name': normalized_name, 'lateral_paths': existing_paths}

        # ---------- 集成深度学习模型推荐 ----------
        recommender = get_path_recommender()
        if recommender and len(existing_paths) < 2:
            try:
                dl_paths = recommender.get_transition_paths(normalized_name, top_n=5)
                for job, sim in dl_paths:
                    if job not in [p['job_name'] for p in existing_paths]:
                        existing_paths.append({
                            'job_name': job,
                            'description': f"基于向量相似度推荐（相似度{sim:.2f}），技能可迁移"
                        })
                if len(existing_paths) >= 2:
                    # 存入数据库
                    conn2 = get_db()
                    cursor2 = conn2.cursor()
                    for item in existing_paths:
                        cursor2.execute('''
                            INSERT OR IGNORE INTO job_relations (from_job, to_job, relation_type, description)
                            VALUES (?, ?, ?, ?)
                        ''', (normalized_name, item['job_name'], 'transition', item['description']))
                    conn2.commit()
                    conn2.close()
                    return {'success': True, 'source': 'dl_model', 'job_name': normalized_name, 'lateral_paths': existing_paths[:3]}
            except Exception as e:
                print(f"⚠️ 深度学习路径推荐失败: {e}")
        # -----------------------------------------

        print(f"🤖 正在为岗位 [{normalized_name}] 动态生成横向发展路径（已有{len(existing_paths)}条）...")
        try:
            current_skills = get_job_skills(normalized_name)
            skills_str = '、'.join(current_skills[:10]) if current_skills else '未知'
        except:
            skills_str = '未知'

        prompt = f"""
你是一位资深的职业规划专家。请为【{normalized_name}】岗位推荐3-5个相关的横向发展（换岗/转型）方向。
当前岗位的核心技能：{skills_str}
要求：
1. 输出一个JSON数组，每个元素包含：job_name（目标岗位名称）、description（转型需要的条件和建议）
2. 推荐的岗位必须是同一行业/领域内，技能可迁移的岗位
只返回JSON数组，不要其他文字。
"""
        result = call_llm(prompt, temperature=0.3, max_tokens=1200)
        if not result:
            raise ValueError("AI 返回空结果")
        json_match = re.search(r'\[\s\S]*?\]', result)
        if json_match:
            result = json_match.group(0)
        new_paths = json.loads(result)
        if not isinstance(new_paths, list):
            raise ValueError("返回格式不正确")

        conn2 = None
        cursor2 = None
        try:
            conn2 = get_db()
            cursor2 = conn2.cursor()
            for item in new_paths:
                to_job = item.get('job_name', '')
                description = item.get('description', '')
                if to_job:
                    cursor2.execute('''
                        INSERT OR IGNORE INTO job_relations (from_job, to_job, relation_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (normalized_name, to_job, 'transition', description))
            conn2.commit()
            time.sleep(0.2)
            cursor2.execute('''
                SELECT to_job, description FROM job_relations
                WHERE from_job = ? AND relation_type = 'transition' ORDER BY id
            ''', (normalized_name,))
            fresh_rows = cursor2.fetchall()
            all_paths = []
            for row in fresh_rows:
                all_paths.append({
                    'job_name': row['to_job'],
                    'description': row['description']
                })
            print(f"✅ 横向路径生成完成，共 {len(all_paths)} 条")
        finally:
            if cursor2:
                cursor2.close()
            if conn2:
                conn2.close()
        return {'success': True, 'source': 'ai_generated', 'job_name': normalized_name, 'lateral_paths': all_paths}
    except Exception as e:
        print(f"❌ 生成横向路径失败: {e}")
        import traceback
        traceback.print_exc()
        default_paths = existing_paths.copy() if 'existing_paths' in locals() else []
        if len(default_paths) < 2:
            default_paths.append({"job_name": f"高级{job_name}", "description": f"在{job_name}岗位上深耕，提升专业深度"})
        if len(default_paths) < 3:
            default_paths.append({"job_name": f"{job_name}顾问", "description": f"从{job_name}转型为顾问方向"})
        return {'success': True, 'source': 'default', 'job_name': job_name, 'lateral_paths': default_paths[:3]}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ========== 获取完整的职业发展图谱 ==========
@job_bp.route('/<job_name>/full-path', methods=['GET'])
def get_full_career_path(job_name):
    """获取岗位的完整发展路径（垂直+横向）"""
    normalized_name = _normalize_job_name(job_name)
    vertical_result = _get_career_path_internal(normalized_name)
    vertical_path = vertical_result.get('path', []) if vertical_result.get('success') else []
    lateral_result = _get_lateral_path_internal(normalized_name)
    lateral_paths = lateral_result.get('lateral_paths', []) if lateral_result.get('success') else []

    formatted_vertical = []
    for item in vertical_path:
        formatted_vertical.append({
            'from_job': item.get('from_job', normalized_name),
            'to_job': item.get('to_job', ''),
            'description': item.get('description', '')
        })
    formatted_lateral = []
    for item in lateral_paths:
        formatted_lateral.append({
            'job_name': item.get('job_name', ''),
            'description': item.get('description', '')
        })
    print(f"📊 返回数据: 垂直路径 {len(formatted_vertical)} 条, 横向路径 {len(formatted_lateral)} 条")
    return jsonify({
        'success': True,
        'job_name': normalized_name,
        'vertical_path': formatted_vertical,
        'lateral_paths': formatted_lateral
    })

# ========== 简单路径查询接口 ==========
@job_bp.route('/<job_name>/vertical', methods=['GET'])
def get_vertical_path_simple(job_name):
    normalized_name = _normalize_job_name(job_name)
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        chain = []
        current = normalized_name
        visited = set()
        while current and current not in visited:
            visited.add(current)
            cursor.execute(
                "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'promotion' LIMIT 1",
                (current,)
            )
            row = cursor.fetchone()
            if not row:
                break
            chain.append({
                'from_job': current,
                'to_job': row['to_job'],
                'description': row['description']
            })
            current = row['to_job']
        return jsonify(chain)
    finally:
        if conn:
            conn.close()

@job_bp.route('/<job_name>/lateral', methods=['GET'])
def get_lateral_path_simple(job_name):
    normalized_name = _normalize_job_name(job_name)
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'transition'",
            (normalized_name,)
        )
        rows = cursor.fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        if conn:
            conn.close()

@job_bp.route('/names', methods=['GET'])
def get_all_job_names():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT job_name FROM job WHERE job_name IS NOT NULL AND job_name != '' ORDER BY job_name")
        rows = cursor.fetchall()
        job_names = [row['job_name'] for row in rows]
        return jsonify(job_names)
    finally:
        if conn:
            conn.close()


# ========== 模型一：岗位相似度检索（懒加载，基于 Word2Vec） ==========
_similarity_model = None


class _Word2VecSimilarityWrapper:
    """轻量包装器：加载 Word2Vec 岗位向量并支持余弦相似度检索"""
    def __init__(self, pkl_path):
        import pickle
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        self.job_ids = data['job_ids']
        self.vectors = data['vectors']  # 已 L2 归一化
        self.raw_names = data['raw_names']
        self._id_to_idx = {jid: i for i, jid in enumerate(self.job_ids)}

    def search_similar(self, job_id, top_k=10):
        import numpy as np
        if job_id not in self._id_to_idx:
            return []
        idx = self._id_to_idx[job_id]
        scores = np.dot(self.vectors, self.vectors[idx])
        top_indices = np.argsort(scores)[::-1]
        results = []
        for i in top_indices:
            if i == idx:
                continue
            results.append({
                'job_id': int(self.job_ids[i]),
                'similarity': round(float(scores[i]), 4)
            })
            if len(results) >= top_k:
                break
        return results


def _get_similarity_model():
    global _similarity_model
    if _similarity_model is None:
        p = 'data/embeddings/job_vectors_word2vec.pkl'
        if os.path.exists(p):
            try:
                _similarity_model = _Word2VecSimilarityWrapper(p)
                print(f"✅ Word2Vec 岗位相似度模型加载成功 ({len(_similarity_model.job_ids)} 条)")
            except Exception as e:
                print(f"⚠️ 加载相似度模型失败: {e}")
    return _similarity_model


@job_bp.route('/<int:job_id>/similar', methods=['GET'])
def get_similar_jobs(job_id):
    """查询与指定岗位最相似的岗位列表"""
    model = _get_similarity_model()
    if model is None:
        return jsonify({'success': True, 'data': [], 'message': '相似度模型尚未生成'})

    top_k = request.args.get('top_k', 10, type=int)
    try:
        results = model.search_similar(job_id, top_k=top_k)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 模型二：岗位技能标签预测（懒加载） ==========
_skill_predictor = None


def _get_skill_predictor():
    global _skill_predictor
    if _skill_predictor is None:
        paths = [
            'data/models/skill_predictor.pth',
            'data/models/skill_text_processor.pkl',
            'data/models/skill_label_extractor.pkl',
        ]
        if all(os.path.exists(p) for p in paths):
            try:
                from services.dl_models.skill_predictor_model import SkillPredictor
                _skill_predictor = SkillPredictor(*paths)
                print("✅ 技能标签预测模型加载成功")
            except Exception as e:
                print(f"⚠️ 加载技能预测模型失败: {e}")
    return _skill_predictor


@job_bp.route('/skills', methods=['POST'])
def predict_job_skills():
    """从岗位描述预测技能标签"""
    data = request.get_json(silent=True) or {}
    job_description = data.get('job_description', '').strip()
    if not job_description:
        return jsonify({'success': False, 'error': '请提供 job_description'}), 400

    predictor = _get_skill_predictor()
    if predictor is None:
        return jsonify({'success': True, 'data': [], 'message': '技能预测模型尚未训练'})

    try:
        results = predictor.predict(job_description, top_k=data.get('top_k', 5))
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500