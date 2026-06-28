"""
霍兰德职业兴趣测评接口（核心功能）
提供题目获取、答案提交、维度计分、AI职业推荐、测评记录查询。
说明：包含测试模式与LLM调用控制，全部为当前在用逻辑，无废弃代码。
"""
from flask import Blueprint, request, jsonify, session
from db import get_db
import json
import random
import os
from services.llm_service import call_llm

assessment_bp = Blueprint('assessment', __name__, url_prefix='/api/assessment')

@assessment_bp.route('/questions', methods=['GET'])
def get_questions():
    """获取所有测评题目，按 sort_order 排序后随机打乱"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, question, dimension FROM assessment_questions ORDER BY sort_order')
    questions = cur.fetchall()
    conn.close()

    question_list = [{'id': q['id'], 'question': q['question'], 'dimension': q['dimension']} for q in questions]
    random.shuffle(question_list)

    return jsonify(question_list)

@assessment_bp.route('/submit', methods=['POST'])
def submit_assessment():
    """提交测评答案，计算维度得分，生成推荐并保存结果"""
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({'error': 'answers required'}), 400

    answers = data['answers']
    
    # ===================== 自动获取当前登录用户ID =====================
    auth_header = request.headers.get('Authorization', '')
    user_id = data.get('user_id')
    
    # 从 token 解析用户ID
    if auth_header.startswith('Bearer mock-token-'):
        user_id = int(auth_header.replace('Bearer mock-token-', '').strip())
    
    # 从 session 获取用户ID
    if not user_id and 'user_id' in session:
        user_id = session['user_id']
    
    # 兜底
    if not user_id:
        user_id = 6
    # ================================================================

    session_id = data.get('session_id', 'guest')
    test_mode = data.get('test_mode', False)

    if not answers:
        return jsonify({'error': 'answers cannot be empty'}), 400

    dimension_totals = {}
    dimension_counts = {}

    conn = get_db()
    cur = conn.cursor()

    for answer in answers:
        question_id = answer.get('question_id')
        score = answer.get('score')
        if not question_id or not isinstance(score, int) or score < 0 or score > 5:
            continue

        cur.execute('SELECT dimension FROM assessment_questions WHERE id = ?', (question_id,))
        row = cur.fetchone()
        if row:
            dimension = row['dimension']
            if dimension not in dimension_totals:
                dimension_totals[dimension] = 0
                dimension_counts[dimension] = 0
            dimension_totals[dimension] += score
            dimension_counts[dimension] += 1

    dimension_scores = {}
    for dim in dimension_totals:
        if dimension_counts[dim] > 0:
            dimension_scores[dim] = round(dimension_totals[dim] / dimension_counts[dim], 2)
        else:
            dimension_scores[dim] = 0.0

    if test_mode or not should_call_llm_api():
        recommendation = "【测试模式】推荐功能已启用，正式使用时将生成个性化职业建议。"
        print(f"⚠️  当前为测试模式，未调用 LLM API")
    else:
        print(f"✅ 正式模式，正在调用 LLM API 生成推荐...")
        recommendation = generate_career_recommendation(dimension_scores)

    # 保存到对应用户ID
    cur.execute('''
        INSERT INTO assessment_results (user_id, session_id, dimension_scores, recommendation, raw_answers)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, session_id, json.dumps(dimension_scores), recommendation, json.dumps(answers)))
    conn.commit()
    result_id = cur.lastrowid
    conn.close()

    return jsonify({
        'success': True,
        'result_id': result_id,
        'dimension_scores': dimension_scores,
        'recommendation': recommendation
    })

@assessment_bp.route('/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    """获取用户的最近10条测评记录"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, dimension_scores, recommendation, created_at
        FROM assessment_results
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,))
    results = cur.fetchall()
    conn.close()

    history = []
    for row in results:
        history.append({
            'id': row['id'],
            'dimension_scores': json.loads(row['dimension_scores']),
            'recommendation': row['recommendation'],
            'created_at': row['created_at']
        })

    return jsonify(history)

def generate_career_recommendation(dimension_scores):
    """根据维度得分生成职业推荐报告"""
    holland_types = {
        'R': '实际型 (Realistic)',
        'I': '研究型 (Investigative)',
        'A': '艺术型 (Artistic)',
        'S': '社会型 (Social)',
        'E': '企业型 (Enterprising)',
        'C': '常规型 (Conventional)'
    }

    if not dimension_scores:
        return "未获取到有效测评得分，无法生成职业推荐。"
        
    sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)

    prompt = f"""
基于霍兰德职业兴趣理论，以下是用户的维度得分（1-5 分）：
{sorted_dims}

请生成一份职业推荐报告，包括：
1. 维度得分解读
2. 主要兴趣类型分析
3. 推荐职业方向（3-5 个具体职业）
4. 职业发展建议

请使用 Markdown 格式输出。
"""

    try:
        print(f"🔍 正在调用阿里云 LLM 生成推荐...")
        response = call_llm(prompt)
        if response:
            print(f"✅ LLM 调用成功，返回 {len(response)} 字符")
            return response.strip()
        else:
            print(f"⚠️ LLM 返回空内容，使用默认推荐")
            return "生成推荐失败，请稍后重试。"
    except Exception as e:
        print(f"❌ LLM 调用异常：{e}")
        return "生成推荐失败，请稍后重试。"

def should_call_llm_api():
    """检查是否应该调用 LLM API"""
    if os.getenv('ENABLE_LLM_RECOMMENDATION', 'false').lower() != 'true':
        print(f"⚠️ ENABLE_LLM_RECOMMENDATION 未开启")
        return False
    
    max_calls = int(os.getenv('MAX_DAILY_API_CALLS', '100'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT COUNT(*) as cnt FROM assessment_results 
        WHERE DATE(created_at) = DATE('now') 
        AND recommendation NOT LIKE '%测试模式%'
    ''')
    today_count = cur.fetchone()['cnt']
    conn.close()
    
    print(f"📊 今日已调用 LLM {today_count}/{max_calls} 次")
    
    if today_count >= max_calls:
        print(f"⚠️ 已达到每日调用上限")
        return False
    
    return True