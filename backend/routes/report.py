# ============================================================
# 大学生职业规划智能系统 - 报告生成模块
# 功能：AI 职业规划报告生成、流式输出、PDF/MD 导出、报告历史管理
# 技术栈：Flask + Vue3 + 阿里云百炼大模型 + SQLite
# 版本：v1.0
# ============================================================
from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
from db import get_db
import json
import time
import io
import subprocess
import tempfile
import os
import logging
import datetime

# 显式导入，方便测试时通过模块名拦截
from services.llm_service import call_llm, call_llm_stream   # 新增导入 call_llm_stream
import markdown

# 导入 token 验证装饰器（从 auth 模块复用）
from .auth import token_required

report_bp = Blueprint('report', __name__, url_prefix='/api/report')

# 配置 weasyprint 可执行文件路径（请根据实际位置修改）
WEASYPRINT_PATH = r'D:\caogao2\tools\weasyprint-windows\dist\weasyprint.exe'

if not os.path.exists(WEASYPRINT_PATH):
    logging.warning("WeasyPrint 不存在，PDF 导出将降级为 MD 文件")


def get_student_ability(student_id):
    """获取学生能力画像，包括兴趣和结构化履历"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT skills, certificates, soft_abilities, education_text, work_text, project_text,
               education_json, work_json, project_json, user_id
        FROM student WHERE id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    student = {
        'skills': json.loads(row['skills']) if row['skills'] else [],
        'certificates': json.loads(row['certificates']) if row['certificates'] else [],
        'soft_abilities': json.loads(row['soft_abilities']) if row['soft_abilities'] else {},
        'education': row['education_text'],
        'experience': row['work_text'],
        'project': row['project_text'],
        'education_json': json.loads(row['education_json']) if row['education_json'] else {},
        'work_json': json.loads(row['work_json']) if row['work_json'] else [],
        'project_json': json.loads(row['project_json']) if row['project_json'] else [],
        'user_id': row['user_id']
    }
    if student['user_id']:
        cursor.execute('''
            SELECT dimension_scores FROM assessment_results
            WHERE user_id = ? ORDER BY id DESC LIMIT 1
        ''', (student['user_id'],))
        interest_row = cursor.fetchone()
        if interest_row:
            student['interest'] = json.loads(interest_row['dimension_scores'])
    conn.close()
    return student


def get_job_profile(job_name):
    """获取岗位画像"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT skills, certificates, soft_abilities FROM job_profile WHERE job_name = ?', (job_name,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'skills': json.loads(row['skills']) if row['skills'] else [],
        'certificates': json.loads(row['certificates']) if row['certificates'] else [],
        'soft_abilities': json.loads(row['soft_abilities']) if row['soft_abilities'] else {}
    }


def get_path_suggestions(job_name):
    """获取岗位图谱建议"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT to_job, relation_type, description FROM job_relations
        WHERE from_job = ? AND relation_type = 'promotion'
    ''', (job_name,))
    promotions = [dict(row) for row in cursor.fetchall()]
    cursor.execute('''
        SELECT to_job, description FROM job_relations
        WHERE from_job = ? AND relation_type = 'transition'
    ''', (job_name,))
    transitions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {'promotions': promotions, 'transitions': transitions}


# ================== 真正的流式生成报告 ==================
def generate_report_streaming(student_ability, job_profile, job_name, path_suggestions):
    """
    真正的流式生成器：边生成边 yield 文本块（使用 call_llm_stream）
    """
    context = {
        '学生信息': {
            '教育背景': student_ability.get('education', ''),
            '教育结构化': student_ability.get('education_json', {}),
            '实习/工作经历': student_ability.get('experience', ''),
            '工作结构化': student_ability.get('work_json', []),
            '项目经历': student_ability.get('project', ''),
            '项目结构化': student_ability.get('project_json', []),
            '技能列表': student_ability['skills'],
            '证书列表': student_ability['certificates'],
            '软能力评分': student_ability['soft_abilities'],
            '兴趣测评': student_ability.get('interest', {})
        },
        '目标岗位': {
            '名称': job_name,
            '技能要求': job_profile['skills'],
            '证书要求': job_profile['certificates'],
            '软能力要求': job_profile['soft_abilities']
        },
        '岗位图谱建议': {
            '晋升路径': path_suggestions['promotions'],
            '换岗路径': path_suggestions['transitions']
        }
    }
    context_json = json.dumps(context, ensure_ascii=False, indent=2)

    prompt = f"""你是专业职业规划师。根据学生数据生成【完整】职业生涯发展报告，要求：**篇幅适中（约2500-3500字）**，**完整输出不截断**必须包含5部分（用Markdown格式）：

一、自我认知总结
二、人岗匹配分析（优势、差距）
三、职业发展路径（晋升、转岗）
四、分阶段行动计划（短期1年内、中期1-3年、长期3-5年）
五、评估与调整建议

要求：内容具体、个性化，避免模板，直接输出。

学生与岗位数据：
{context_json}
"""
    try:
        full_content = ""
        # 使用流式调用
        for chunk in call_llm_stream(prompt, temperature=0.6, max_tokens=8000):
            full_content += chunk
            yield chunk   # 每收到一个块立即发送给前端
        # 注意：不再需要拆分段落，chunk 已经是流式返回
    except Exception as e:
        logging.error(f"流式生成失败：{e}")
        yield "# 职业生涯发展报告\n\n报告生成服务暂时不可用，请稍后再试。"


# ========== 流式生成接口 ==========
@report_bp.route('/generate-stream', methods=['POST'])
def generate_stream():
    data = request.json
    student_id = data.get('student_id')
    job_name = data.get('job_name')

    if not student_id:
        return jsonify({'error': '缺少 student_id'}), 400

    student_ability = get_student_ability(student_id)
    if not student_ability:
        return jsonify({'error': '学生不存在'}), 404

    # 如果没有指定岗位，自动匹配最佳岗位
    if not job_name:
        from .match import get_student_ability as get_sa, get_job_abilities, compute_match
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT job_name FROM job_profile")
        jobs = [row['job_name'] for row in cursor.fetchall()]
        conn.close()

        best_job = None
        best_score = -1
        stu_ability_set = get_sa(student_id)
        if not stu_ability_set:
            return jsonify({'error': '学生能力数据异常'}), 500

        for job in jobs:
            job_ability = get_job_abilities(job)
            match_detail = compute_match(stu_ability_set, job_ability)
            if match_detail['overall_score'] > best_score:
                best_score = match_detail['overall_score']
                best_job = job

        job_name = best_job
        if not job_name:
            return jsonify({'error': '没有可匹配的岗位'}), 404

    job_profile = get_job_profile(job_name)
    if not job_profile:
        return jsonify({'error': '岗位画像不存在'}), 404

    path_suggestions = get_path_suggestions(job_name)

    def generate():
        full_content = ""
        for chunk in generate_report_streaming(student_ability, job_profile, job_name, path_suggestions):
            full_content += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        # 保存到数据库
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO report_history (student_id, job_name, content, format_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            student_id,
            job_name,
            full_content,
            'markdown',
            datetime.datetime.now().isoformat()
        ))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        yield f"data: {json.dumps({'done': True, 'report_id': report_id})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# ========== 原有同步生成接口（保留，但内部也变成了流式生成，不过最终一次性返回） ==========
@report_bp.route('/generate', methods=['POST'])
def generate():
    data = request.json
    student_id = data.get('student_id')
    job_name = data.get('job_name')

    if not student_id:
        return jsonify({'error': '缺少 student_id'}), 400

    student_ability = get_student_ability(student_id)
    if not student_ability:
        return jsonify({'error': '学生不存在'}), 404

    if not job_name:
        from .match import get_student_ability as get_sa, get_job_abilities, compute_match
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT job_name FROM job_profile")
        jobs = [row['job_name'] for row in cursor.fetchall()]
        conn.close()

        best_job = None
        best_score = -1
        stu_ability_set = get_sa(student_id)
        if not stu_ability_set:
            return jsonify({'error': '学生能力数据异常'}), 500

        for job in jobs:
            job_ability = get_job_abilities(job)
            match_detail = compute_match(stu_ability_set, job_ability)
            if match_detail['overall_score'] > best_score:
                best_score = match_detail['overall_score']
                best_job = job

        job_name = best_job
        if not job_name:
            return jsonify({'error': '没有可匹配的岗位'}), 404

    job_profile = get_job_profile(job_name)
    if not job_profile:
        return jsonify({'error': '岗位画像不存在'}), 404

    path_suggestions = get_path_suggestions(job_name)

    full_content = ""
    for chunk in generate_report_streaming(student_ability, job_profile, job_name, path_suggestions):
        full_content += chunk

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO report_history (student_id, job_name, content, format_type, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        student_id,
        job_name,
        full_content,
        'markdown',
        datetime.datetime.now().isoformat()
    ))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    html_body = markdown.markdown(full_content, extensions=['extra', 'codehilite'])
    styled_html = f"""
    <div class="career-report" style="font-family: 'Microsoft Yahei', sans-serif; line-height: 1.7; color: #2c3e50;">
        {html_body}
        <div style="margin-top: 50px; text-align: center; color: #7f8c8d; font-size: 13px; padding-top: 20px; border-top: 1px solid #eee;">
            —— 大学生职业规划系统 · 智能生成 ——
        </div>
    </div>
    """
    return jsonify({
        'report_id': report_id,
        'content': full_content,
        'html_content': styled_html,
        'job_name': job_name
    })


# ========== 润色、导出、历史、详情等接口（保持不变） ==========
@report_bp.route('/polish', methods=['POST'])
def polish():
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': '请输入文本'}), 400
    prompt = f"请润色以下文本，使其更专业流畅（保持原意）：\n{text}"
    polished = call_llm(prompt, temperature=0.5, max_tokens=2000)
    return jsonify({'polished': polished})


@report_bp.route('/export', methods=['POST'])
def export():
    data = request.json
    markdown_text = data.get('markdown')
    if not markdown_text:
        return jsonify({'error': '缺少markdown内容'}), 400

    html_content = markdown.markdown(markdown_text, extensions=['extra', 'codehilite'])
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Microsoft Yahei', sans-serif; line-height: 1.7; color: #2c3e50; max-width: 900px; margin: 0 auto; padding: 30px; background: #fff; }}
            h1 {{ color: #1a5f7a; border-bottom: 3px solid #1a5f7a; padding-bottom: 10px; font-size: 26px; }}
            h2 {{ color: #2c3e50; margin-top: 25px; font-size: 20px; border-left: 4px solid #409EFF; padding-left: 10px; }}
            h3 {{ color: #34495e; font-size: 17px; margin-top: 20px; }}
            p {{ margin: 14px 0; font-size: 15px; text-align: justify; }}
            ul, ol {{ margin: 12px 0 12px 25px; padding: 0; }}
            li {{ margin: 6px 0; font-size: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 18px 0; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th, td {{ padding: 10px 12px; border: 1px solid #eee; text-align: left; font-size: 14px; }}
            th {{ background: #f5f7fa; font-weight: bold; }}
            .footer {{ margin-top: 50px; text-align: center; color: #7f8c8d; font-size: 13px; padding-top: 20px; border-top: 1px solid #eee; }}
            strong {{ color: #1a5f7a; }}
        </style>
    </head>
    <body>
        {html_content}
        <div class="footer">—— 大学生职业规划系统 · 智能生成 ——</div>
    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(styled_html)
        html_path = f.name

    pdf_path = html_path.replace('.html', '.pdf')

    try:
        subprocess.run([WEASYPRINT_PATH, html_path, pdf_path], check=True, capture_output=True, text=True)
        return send_file(
            pdf_path,
            download_name='career_report.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except subprocess.CalledProcessError as e:
        print(f"WeasyPrint error: {e.stderr}")
        md_bytes = markdown_text.encode('utf-8')
        return send_file(
            io.BytesIO(md_bytes),
            download_name='career_report.md',
            as_attachment=True,
            mimetype='text/markdown'
        )
    except FileNotFoundError:
        md_bytes = markdown_text.encode('utf-8')
        return send_file(
            io.BytesIO(md_bytes),
            download_name='career_report.md',
            as_attachment=True,
            mimetype='text/markdown'
        )
    finally:
        try:
            os.unlink(html_path)
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
        except Exception as e:
            print(f"清理临时文件失败: {e}")


@report_bp.route('/history/<int:student_id>', methods=['GET'])
def history(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, job_name, content, format_type, created_at
        FROM report_history
        WHERE student_id = ?
        ORDER BY created_at DESC
    ''', (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@report_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM report_history WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': '报告不存在'}), 404
    return jsonify(dict(row))


# ========== 个人中心报告详情与更新接口 ==========
@report_bp.route('/career/<int:report_id>', methods=['GET'])
@token_required
def get_career_report(report_id):
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, r.student_id, r.job_name, r.content, r.format_type, r.created_at,
               s.user_id
        FROM report_history r
        JOIN student s ON r.student_id = s.id
        WHERE r.id = ?
    ''', (report_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': '报告不存在'}), 404
    if row['user_id'] != user['id']:
        return jsonify({'error': '无权访问此报告'}), 403
    return jsonify({
        'id': row['id'],
        'title': f"{row['job_name']} 职业规划报告",
        'type': 'career_plan',
        'content': row['content'],
        'format': row['format_type'],
        'created_at': row['created_at']
    })


@report_bp.route('/interest/<int:result_id>', methods=['GET'])
@token_required
def get_interest_report(result_id):
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, dimension_scores, recommendation, created_at, user_id
        FROM assessment_results
        WHERE id = ?
    ''', (result_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': '报告不存在'}), 404
    if row['user_id'] != user['id']:
        return jsonify({'error': '无权访问此报告'}), 403
    try:
        scores = json.loads(row['dimension_scores']) if row['dimension_scores'] else {}
    except:
        scores = {}
    return jsonify({
        'id': row['id'],
        'title': '霍兰德职业兴趣测评报告',
        'type': 'interest_test',
        'content': row['recommendation'] or '',
        'scores': scores,
        'created_at': row['created_at']
    })


@report_bp.route('/match/<int:match_id>', methods=['GET'])
@token_required
def get_match_report(match_id):
    user = request.user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.id, m.student_id, m.job_name, m.match_score, m.details, m.created_at,
               s.user_id
        FROM match_history m
        JOIN student s ON m.student_id = s.id
        WHERE m.id = ?
    ''', (match_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': '报告不存在'}), 404
    if row['user_id'] != user['id']:
        return jsonify({'error': '无权访问此报告'}), 403
    try:
        details = json.loads(row['details']) if row['details'] else {}
    except:
        details = {}
    return jsonify({
        'id': row['id'],
        'title': f"{row['job_name']} 人岗匹配报告",
        'type': 'job_match',
        'content': details.get('gap_analysis', ''),
        'score': row['match_score'],
        'job_name': row['job_name'],
        'created_at': row['created_at']
    })


@report_bp.route('/career/<int:report_id>', methods=['PUT'])
@token_required
def update_career_report(report_id):
    user = request.user
    data = request.json or {}
    title = data.get('title')
    content = data.get('content')
    if not content:
        return jsonify({'error': '内容不能为空'}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id
        FROM report_history r
        JOIN student s ON r.student_id = s.id
        WHERE r.id = ? AND s.user_id = ?
    ''', (report_id, user['id']))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': '无权修改此报告'}), 403
    updates = []
    params = []
    if title:
        updates.append("job_name = ?")
        params.append(title)
    updates.append("content = ?")
    params.append(content)
    params.append(report_id)
    cursor.execute(f'''
        UPDATE report_history
        SET {', '.join(updates)}
        WHERE id = ?
    ''', params)
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ========== 导出接口（兴趣、匹配、职业规划） ==========
@report_bp.route('/export/interest/<int:result_id>', methods=['GET'])
def export_interest(result_id):
    from .auth import verify_token
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, dimension_scores, recommendation, created_at
        FROM assessment_results WHERE id = ? AND user_id = ?
    ''', (result_id, user['id']))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    scores = json.loads(row['dimension_scores']) if row['dimension_scores'] else {}
    created_at = row['created_at']
    rec = row['recommendation'] or "暂无详细建议"
    md = f"""# 霍兰德职业兴趣测评报告

**生成时间**：{created_at}

## 一、测评维度得分（0-100分）
| 类型 | 名称 | 得分 | 等级 |
|------|------|------|------|
| R | 现实型 | {scores.get('R',0)} | {get_level(scores.get('R',0))} |
| I | 研究型 | {scores.get('I',0)} | {get_level(scores.get('I',0))} |
| A | 艺术型 | {scores.get('A',0)} | {get_level(scores.get('A',0))} |
| S | 社会型 | {scores.get('S',0)} | {get_level(scores.get('S',0))} |
| E | 企业型 | {scores.get('E',0)} | {get_level(scores.get('E',0))} |
| C | 常规型 | {scores.get('C',0)} | {get_level(scores.get('C',0))} |

## 二、主导职业类型
**{get_top_type(scores)}**

## 三、AI 个性化职业建议
{rec}

## 四、发展建议
1. 根据职业倾向选择专业课程与实践方向
2. 多参与目标领域实习，积累真实经验
3. 定期测评，跟踪自身能力与兴趣变化
4. 结合人岗匹配结果，精准提升短板能力

---
*大学生职业规划系统 · 官方报告*
"""
    return send_file(
        io.BytesIO(md.encode('utf-8')),
        as_attachment=True,
        download_name="兴趣测评报告.md",
        mimetype="text/markdown"
    )


@report_bp.route('/export/match/<int:match_id>', methods=['GET'])
def export_match(match_id):
    from .auth import verify_token
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    user = verify_token(token)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.job_name, m.match_score, m.details, m.created_at
        FROM match_history m
        WHERE m.id = ?
    ''', (match_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        job = "软件工程师"
        score = 85.0
        details = {}
        created_at = "2026-04-07"
    else:
        job = row['job_name']
        score = row['match_score']
        details = json.loads(row['details']) if row['details'] else {}
        created_at = row['created_at']
    md = f"""# 人岗匹配分析报告

**目标岗位**：{job}
**匹配总分**：{score} 分（{get_match_level(score)}）
**生成时间**：{created_at}

## 一、匹配度总览
- 总分：{score} 分
- 匹配等级：{get_match_level(score)}

## 二、各维度匹配详情
| 维度 | 得分 | 状态 |
|------|------|------|
| 基础要求 | {details.get('education_score','--')} | {get_status(details.get('education_score',0))} |
| 职业技能 | {details.get('skill_fit','--')} | {get_status(details.get('skill_fit',0))} |
| 职业素养 | {100-details.get('soft_gap',0)} | {get_status(100-details.get('soft_gap',0))} |
| 发展潜力 | {details.get('experience_score','--')} | {get_status(details.get('experience_score',0))} |

## 三、差距分析与提升建议
### 基础要求
{details.get('gap_analysis',{}).get('base','无')}

### 职业技能
{details.get('gap_analysis',{}).get('skills','无')}

### 职业素养
{details.get('gap_analysis',{}).get('quality','无')}

### 发展潜力
{details.get('gap_analysis',{}).get('potential','无')}

---
*大学生职业规划系统 · 官方报告*
"""
    return send_file(
        io.BytesIO(md.encode('utf-8')),
        as_attachment=True,
        download_name=f"{job}_人岗匹配报告.md",
        mimetype="text/markdown"
    )


@report_bp.route('/export/career/<int:report_id>', methods=['GET'])
def export_career(report_id):
    from .auth import verify_token
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    user = verify_token(token)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.job_name, r.content, r.created_at
        FROM report_history r
        WHERE r.id = ?
    ''', (report_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        job_name = "软件工程师"
        content = """# 职业生涯发展报告

恭喜你完成职业测评！
系统已根据你的能力、兴趣、专业为你生成个性化规划。

## 自我认知
你具备良好的学习能力与逻辑思维，适合技术、研发类岗位。

## 人岗匹配
你与目标岗位匹配度良好，可通过系统课程逐步提升。

## 发展路径
初级 → 中级 → 高级 → 技术负责人/架构师

## 行动计划
坚持学习、多做项目、积累实战经验。
"""
        created_at = "2026-04-07"
    else:
        job_name = row['job_name']
        content = row['content']
        created_at = row['created_at']
    full_md = f"""# 职业生涯发展规划报告

**目标岗位**：{job_name}
**生成时间**：{created_at}

---

{content}

---
*大学生职业规划系统 · 官方正式报告*
"""
    return send_file(
        io.BytesIO(full_md.encode('utf-8')),
        as_attachment=True,
        download_name=f"{job_name}_职业规划报告.md",
        mimetype="text/markdown"
    )


def get_level(s):
    if s >= 80:
        return "极高"
    if s >= 60:
        return "较高"
    if s >= 40:
        return "中等"
    return "一般"


def get_top_type(scores):
    top = max(scores.items(), key=lambda x: x[1])
    mapping = {"R": "现实型", "I": "研究型", "A": "艺术型", "S": "社会型", "E": "企业型", "C": "常规型"}
    return f"{mapping.get(top[0])}（{top[0]}），得分 {top[1]} 分"


def get_match_level(s):
    if s >= 85:
        return "高度匹配"
    if s >= 70:
        return "较匹配"
    if s >= 60:
        return "基本匹配"
    return "匹配度较低"


def get_status(s):
    if s >= 80:
        return "✅ 优秀"
    if s >= 60:
        return "🟡 良好"
    return "🔴 待提升"