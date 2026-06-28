"""
学生档案与简历解析核心接口蓝图
功能：支持手动填写档案、PDF/Word简历自动解析、AI结构化提取能力画像、专业与学历识别、学生信息查询

重要说明：
1. 本模块为系统核心数据来源，所有学生能力、专业、学历、经历均由此模块管理；
2. 支持PDF、DOC、DOCX格式简历上传，通过阿里云大模型自动结构化解析；
3. 自动识别专业、学历、学校层次、实习经历、技能证书；
4. 生成标准学生画像，供人岗匹配、智能推荐使用；
5. 接口统一前缀 /api/profile，是整个系统的数据基础。
"""

import os
import time
import json
import tempfile
import re
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from db import get_db
from services.llm_service import call_llm
import pdfplumber
from docx import Document

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024

# 默认软能力（改为数字，避免 NaN）
REQUIRED_SOFT_ABILITIES = {
    "创新能力": {"score": 3, "description": "未详细评估，默认中等水平"},
    "学习能力": {"score": 3, "description": "未详细评估，默认中等水平"},
    "抗压能力": {"score": 3, "description": "未详细评估，默认中等水平"},
    "沟通能力": {"score": 3, "description": "未详细评估，默认中等水平"},
    "实习能力": {"score": 3, "description": "未详细评估，默认中等水平"}
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_major_from_education(education_text, education_json):
    """从教育信息中解析专业（增强版）"""
    # 1. 优先从 education_json 获取
    if education_json and education_json.get('major'):
        return education_json.get('major')
    
    if education_text:
        # 2. 常见专业关键词列表（按优先级排序）
        majors = [
            '计算机科学与技术', '软件工程', '人工智能', '数据科学与大数据技术',
            '电子信息工程', '通信工程', '自动化', '物联网工程', '网络工程',
            '信息安全', '数字媒体技术', '智能科学与技术', '电子科学与技术',
            '微电子科学与工程', '光电信息科学与工程', '信息工程',
            '工商管理', '市场营销', '会计学', '财务管理', '人力资源管理',
            '金融学', '经济学', '国际经济与贸易', '电子商务',
            '法学', '英语', '汉语言文学', '新闻学', '广告学',
            '设计学', '视觉传达设计', '环境设计', '产品设计', '动画',
            '土木工程', '机械工程', '电气工程', '材料科学与工程'
        ]
        
        # 精确匹配
        for major in majors:
            if major in education_text:
                return major
        
        # 模糊匹配（关键词）
        major_keywords = {
            '计算机': '计算机科学与技术',
            '软件': '软件工程',
            '人工智能': '人工智能',
            '数据': '数据科学与大数据技术',
            '电子信息': '电子信息工程',
            '通信': '通信工程',
            '自动化': '自动化',
            '设计': '设计学',
            '市场': '市场营销',
            '工商': '工商管理',
            '金融': '金融学',
            '经济': '经济学',
            '法学': '法学',
            '英语': '英语',
            '中文': '汉语言文学',
            '新闻': '新闻学'
        }
        
        for kw, major_name in major_keywords.items():
            if kw in education_text:
                return major_name
        
        # 尝试从文本中提取“专业：xxx”格式
        match = re.search(r'专业[：:]\s*([^,，\s]{2,10})', education_text)
        if match:
            return match.group(1)
        
        # 尝试提取“XX专业”格式
        match = re.search(r'([\u4e00-\u9fa5]{2,6})专业', education_text)
        if match:
            return match.group(1) + '专业'
    
    return ''


def calculate_internship_score_from_work(work_json):
    """根据实习经历自动计算实习能力分数（1-5分）"""
    if not work_json:
        return 1
    
    total_months = 0
    company_count = 0
    has_achievement = False
    
    for exp in work_json:
        date_range = exp.get('date_range', '')
        match = re.search(r'(\d{4})\.(\d{1,2})-(\d{4})\.(\d{1,2})', date_range)
        if match:
            start_year, start_month, end_year, end_month = map(int, match.groups())
            total_months += (end_year - start_year) * 12 + (end_month - start_month)
            company_count += 1
        
        # 检查是否有量化成果
        achievements = exp.get('achievements', '')
        if achievements and any(kw in achievements for kw in ['提升', '优化', '增长', '改善', '完成', '开发']):
            has_achievement = True
    
    # 评分规则
    if total_months >= 12 and company_count >= 2 and has_achievement:
        return 5
    elif total_months >= 12 or (total_months >= 6 and has_achievement):
        return 4
    elif total_months >= 6:
        return 3
    elif total_months >= 3:
        return 2
    elif total_months > 0:
        return 2
    else:
        return 1


def get_school_level(school_name):
    """识别学校层次，返回加成系数"""
    if not school_name:
        return 1.0
    
    # C9/顶尖高校
    top_schools = ['清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学', 
                   '中国科学技术大学', '南京大学', '西安交通大学', '哈尔滨工业大学',
                   '华中科技大学', '武汉大学', '中山大学', '四川大学', '南开大学',
                   '天津大学', '山东大学', '东南大学', '吉林大学', '厦门大学', '同济大学']
    
    for top in top_schools:
        if top in school_name:
            return 1.15
    
    # 普通本科
    if '大学' in school_name and len(school_name) <= 10:
        return 1.05
    
    return 1.0


def _parse_education_text(education_text):
    """从简单文本抽取学校和学位"""
    if not education_text:
        return {'school': '', 'major': '', 'degree': ''}
    edu = str(education_text).strip()
    levels = ['博士', '硕士', '本科', '大专', '专科', '高中']
    found = ''
    for level in levels:
        if level in edu:
            found = level
            break
    school = edu.replace(found, '').strip() if found else edu
    return {
        'school': school,
        'major': '',
        'degree': found or ''
    }


def ensure_required_soft_abilities(soft_abilities):
    """统一保证：必须包含 5 个固定软能力"""
    result = REQUIRED_SOFT_ABILITIES.copy()
    if soft_abilities and isinstance(soft_abilities, dict):
        for key, value in soft_abilities.items():
            if key in result:
                result[key] = value
    return result


def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


@profile_bp.route('/submit', methods=['POST'])
def submit_profile():
    """提交手动填写的表单数据（包括个人信息和简历文本）"""
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    education = data.get('education', '')
    work = data.get('work', '')
    project = data.get('project', '')
    skills_certs = data.get('skills_certs', '')
    summary = data.get('summary', '')

    if not all([name, phone, email]):
        return jsonify({'error': '姓名、手机、邮箱为必填项'}), 400

    full_text = f"""
教育经历：{education}
工作经历：{work}
项目经历：{project}
技能与证书：{skills_certs}
自我总结：{summary}
    """.strip()

    prompt = f"""
请从以下用户输入的文本中提取能力信息，返回严格的JSON格式：
- skills：技能列表（字符串数组）
- certificates：证书列表（字符串数组）
- soft_abilities：软能力对象，**必须包含：创新能力、学习能力、抗压能力、沟通能力、实习能力**，可额外增加其他能力
  每个能力格式：{{"score": 1-5, "description": "详细描述体现"}}
- education：结构化教育经历对象：{{ "school", "major", "degree", "gpa", "ranking", "courses" }}
- work_experience：结构化工作经历数组，每个包含{{ "company", "position", "date_range", "responsibilities", "achievements" }}
- project_experience：结构化项目经历数组，每个包含{{ "project_name", "role", "technology_stack", "description", "outcome" }}

用户文本：
{full_text}

只返回JSON，不要其他文字。
"""
    result = call_llm(prompt, temperature=0.3, max_tokens=2000)
    
    if not result or not result.strip():
        education_info = _parse_education_text(education)
        ability = {
            'skills': [s.strip() for s in skills_certs.split(',') if s.strip()],
            'certificates': [s.strip() for s in skills_certs.split(',') if s.strip()],
            'soft_abilities': REQUIRED_SOFT_ABILITIES,
            'education': education_info,
            'work_experience': [],
            'project_experience': []
        }
    else:
        try:
            ability = json.loads(result)
            ability['soft_abilities'] = ensure_required_soft_abilities(ability.get('soft_abilities', {}))
        except Exception:
            education_info = _parse_education_text(education)
            ability = {
                'skills': [s.strip() for s in skills_certs.split(',') if s.strip()],
                'certificates': [s.strip() for s in skills_certs.split(',') if s.strip()],
                'soft_abilities': REQUIRED_SOFT_ABILITIES,
                'education': education_info,
                'work_experience': [],
                'project_experience': []
            }

    # 解析专业（增强版）
    major = parse_major_from_education(education, ability.get('education', {}))
    
    # 如果专业仍然为空，尝试从技能中推断
    if not major and ability.get('skills'):
        skills = ability.get('skills', [])
        skill_to_major = {
            'python': '计算机科学与技术',
            'java': '软件工程',
            'javascript': '计算机科学与技术',
            'vue': '软件工程',
            'react': '软件工程',
            'sql': '数据科学与大数据技术',
            'tensorflow': '人工智能',
            'pytorch': '人工智能',
            'sketch': '设计学',
            'figma': '设计学',
            'ps': '设计学'
        }
        for skill in skills:
            skill_lower = skill.lower()
            for kw, major_name in skill_to_major.items():
                if kw in skill_lower:
                    major = major_name
                    break
            if major:
                break
    
    # 计算实习能力分数（从 work_experience 自动计算）
    internship_score = calculate_internship_score_from_work(ability.get('work_experience', []))
    # 更新软能力中的实习能力分数
    if '实习能力' in ability.get('soft_abilities', {}):
        ability['soft_abilities']['实习能力']['score'] = internship_score
        ability['soft_abilities']['实习能力']['description'] = f"基于{len(ability.get('work_experience', []))}段实习经历，累计实习时长自动评估"
    
    completeness = 0
    total = 5
    if education: completeness += 1
    if work: completeness += 1
    if project: completeness += 1
    if skills_certs: completeness += 1
    if summary: completeness += 1
    completeness = round((completeness / total) * 100)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO student (
            user_id, name, phone, email, major,
            education_text, work_text, project_text, skills_certs_text, summary,
            skills, certificates, soft_abilities,
            education_json, work_json, project_json,
            completeness, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, name, phone, email, major,
        education, work, project, skills_certs, summary,
        json.dumps(ability.get('skills', []), ensure_ascii=False),
        json.dumps(ability.get('certificates', []), ensure_ascii=False),
        json.dumps(ability.get('soft_abilities', {}), ensure_ascii=False),
        json.dumps(ability.get('education', {}), ensure_ascii=False),
        json.dumps(ability.get('work_experience', []), ensure_ascii=False),
        json.dumps(ability.get('project_experience', []), ensure_ascii=False),
        completeness,
        int(time.time())
    ))
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'student_id': student_id,
        'completeness': completeness,
        'major': major,
        'skills': ability.get('skills', []),
        'certificates': ability.get('certificates', []),
        'soft_abilities': ability.get('soft_abilities', {})
    })


@profile_bp.route('/upload', methods=['POST'])
def upload_resume():
    """上传简历文件（PDF/Word）"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
    file = request.files['file']
    user_id = request.form.get('user_id', type=int)

    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型，仅支持 PDF、Word 文档'}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': '文件大小不能超过 10MB'}), 400

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext == 'pdf':
            text = extract_text_from_pdf(tmp_path)
        elif ext in ('doc', 'docx'):
            text = extract_text_from_docx(tmp_path)
        else:
            text = ""
    except Exception as e:
        os.unlink(tmp_path)
        return jsonify({'error': f'文件解析失败：{str(e)}'}), 500

    os.unlink(tmp_path)

    if not text.strip():
        return jsonify({'error': '无法从文件中提取文本内容'}), 400

    prompt = f"""
请从以下简历文本中提取能力信息，返回严格的JSON格式：
- skills：技能列表（字符串数组）
- certificates：证书列表（字符串数组）
- soft_abilities：软能力对象，**必须包含：创新能力、学习能力、抗压能力、沟通能力、实习能力**，可额外增加其他能力
  每个能力格式：{{"score": 1-5, "description": "详细描述体现"}}
- education：结构化教育经历对象：{{ "school", "major", "degree" }}
- work_experience：工作/实习经历数组

简历文本：
{text}

只返回JSON，不要其他文字。
"""
    result = call_llm(prompt, temperature=0.3, max_tokens=2000)
    
    if not result or not result.strip():
        ability = {
            'skills': [],
            'certificates': [],
            'soft_abilities': REQUIRED_SOFT_ABILITIES,
            'education': {},
            'work_experience': []
        }
    else:
        try:
            ability = json.loads(result)
            ability['soft_abilities'] = ensure_required_soft_abilities(ability.get('soft_abilities', {}))
        except Exception:
            ability = {
                'skills': [],
                'certificates': [],
                'soft_abilities': REQUIRED_SOFT_ABILITIES,
                'education': {},
                'work_experience': []
            }

    # 解析专业
    major = parse_major_from_education('', ability.get('education', {}))
    
    # 如果专业仍然为空，尝试从技能中推断
    if not major and ability.get('skills'):
        skills = ability.get('skills', [])
        skill_to_major = {
            'python': '计算机科学与技术',
            'java': '软件工程',
            'javascript': '计算机科学与技术',
            'vue': '软件工程',
            'react': '软件工程',
            'sql': '数据科学与大数据技术',
            'tensorflow': '人工智能',
            'pytorch': '人工智能',
            'sketch': '设计学',
            'figma': '设计学',
            'ps': '设计学'
        }
        for skill in skills:
            skill_lower = skill.lower()
            for kw, major_name in skill_to_major.items():
                if kw in skill_lower:
                    major = major_name
                    break
            if major:
                break
    
    # 计算实习能力分数
    internship_score = calculate_internship_score_from_work(ability.get('work_experience', []))
    if '实习能力' in ability.get('soft_abilities', {}):
        ability['soft_abilities']['实习能力']['score'] = internship_score
        ability['soft_abilities']['实习能力']['description'] = f"基于{len(ability.get('work_experience', []))}段实习经历自动评估"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO student (
            user_id, name, phone, email, major,
            education_text, work_text, project_text, skills_certs_text, summary,
            skills, certificates, soft_abilities,
            education_json, work_json, project_json,
            completeness, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, '', '', '', major,
        ability.get('education', {}).get('school', ''),
        json.dumps(ability.get('work_experience', []), ensure_ascii=False),
        '', '', '',
        json.dumps(ability.get('skills', []), ensure_ascii=False),
        json.dumps(ability.get('certificates', []), ensure_ascii=False),
        json.dumps(ability.get('soft_abilities', {}), ensure_ascii=False),
        json.dumps(ability.get('education', {}), ensure_ascii=False),
        json.dumps(ability.get('work_experience', []), ensure_ascii=False),
        json.dumps([], ensure_ascii=False),
        50,
        int(time.time())
    ))
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'student_id': student_id,
        'major': major,
        'skills': ability.get('skills', []),
        'certificates': ability.get('certificates', []),
        'soft_abilities': ability.get('soft_abilities', {}),
        'raw_text_preview': text[:500] + ('...' if len(text) > 500 else '')
    })


@profile_bp.route('/<int:student_id>', methods=['GET'])
def get_profile(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, name, phone, email, major,
               education_text, work_text, project_text, skills_certs_text, summary,
               skills, certificates, soft_abilities,
               education_json, work_json, project_json,
               completeness, created_at
        FROM student WHERE id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': '学生不存在'}), 404
    
    profile = dict(row)
    profile['skills'] = json.loads(profile['skills']) if profile.get('skills') else []
    profile['certificates'] = json.loads(profile['certificates']) if profile.get('certificates') else []
    profile['soft_abilities'] = json.loads(profile['soft_abilities']) if profile.get('soft_abilities') else {}
    profile['soft_abilities'] = ensure_required_soft_abilities(profile['soft_abilities'])
    
    profile['education_json'] = json.loads(profile['education_json']) if profile.get('education_json') else {}
    profile['work_json'] = json.loads(profile['work_json']) if profile.get('work_json') else []
    profile['project_json'] = json.loads(profile['project_json']) if profile.get('project_json') else []
    
    # 如果 major 为空，尝试从 education_json 中补全
    if not profile.get('major') and profile['education_json'].get('major'):
        profile['major'] = profile['education_json'].get('major')
        # 更新数据库
        cursor.execute("UPDATE student SET major = ? WHERE id = ?", (profile['major'], student_id))
        conn.commit()
    
    if profile['user_id']:
        cursor.execute('''
            SELECT dimension_scores FROM assessment_results
            WHERE user_id = ? ORDER BY id DESC LIMIT 1
        ''', (profile['user_id'],))
        interest_row = cursor.fetchone()
        if interest_row:
            profile['interest'] = json.loads(interest_row['dimension_scores'])
    conn.close()
    return jsonify(profile)