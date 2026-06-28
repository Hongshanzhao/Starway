"""
大模型服务接口蓝图
功能：提供AI相关接口，包括DeepSeek连接测试、智能岗位推荐、学习计划生成、智能问答等

重要说明：
1. 本文件封装所有AI大模型调用能力，依赖llm_service服务层；
2. 核心能力：智能岗位推荐、个性化学习计划生成、知识库问答；
3. 敏感接口均添加token_required鉴权，保证接口安全；
4. 统一前缀 /api/llm，返回格式均为标准JSON；
5. 依赖环境变量：DEEPSEEK_API_KEY，用于大模型API调用。
项目正式环境底层实际接入【阿里云大模型】，DeepSeek 接口仅作测试、调试使用；
"""

from flask import Blueprint, request, jsonify
from services import llm_service
from db import get_db
from .auth import token_required
import os

llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')


@llm_bp.route('/test_connection', methods=['GET'])
def test_connection():
    """✅ 测试 DeepSeek 连接状态"""
    api_key = llm_service._get_deepseek_key()
    if api_key:
        test_prompt = "请用一句话回答：1+1 等于几"
        result = llm_service._call_deepseek(test_prompt)
        if result:
            return jsonify({
                'status': 'ok',
                'message': 'DeepSeek 连接成功',
                'response': result[:100]
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': 'API Key 存在但调用失败，请检查网络和 API Key 有效性'
            })
    else:
        return jsonify({
            'status': 'error',
            'message': 'DEEPSEEK_API_KEY 未配置'
        }), 400


@llm_bp.route('/recommend', methods=['POST'])
@token_required
def recommend():
    data = request.json or {}
    student = data.get('student')
    top_n = int(data.get('top_n', 5))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM job')
    jobs = [dict(r) for r in cur.fetchall()]
    conn.close()
    recs = llm_service.intelligent_recommendation(student or {}, jobs, top_n)
    return jsonify({'results': recs})


@llm_bp.route('/generate_plan', methods=['POST'])
@token_required
def generate_plan():
    data = request.json or {}
    student = data.get('student')
    job_name = data.get('job_name')
    text = llm_service.generate_plan_suggestion(student or {}, job_name or '')
    return jsonify({'plan': text})


@llm_bp.route('/qa', methods=['POST'])
def qa():
    data = request.json or {}
    q = data.get('question', '')
    context = data.get('context', '')
    ans = llm_service.chat_qa(q, context)
    return jsonify({'answer': ans})