"""
人岗智能匹配核心接口蓝图
功能：基于学生能力画像与岗位要求，实现多维度智能匹配、岗位推荐、差距分析、流式AI建议生成

重要说明：
1. 本模块为系统核心匹配引擎，采用权重化评分机制（职业技能50%、职业素养18%、基础要求12%、发展潜力20%）；
2. 支持专业相关性、学校层次、技能深度、证书覆盖、经验年限、学历要求等全维度精准计算；
3. 内置大类预筛选逻辑，根据学生专业/兴趣/技能自动推荐最相关岗位大类，提升匹配效率；
4. 提供完整匹配、批量推荐、历史记录、流式AI差距分析四大接口；
5. 正式环境底层使用阿里云大模型生成专业差距分析与学习建议；
6. 接口统一前缀 /api/match，支持标准JSON与SSE流式响应。
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
from db import get_db
import json
import time
import re
from functools import lru_cache
from services.llm_service import call_llm
from routes.auth import token_required
from services.dl_models import MatchingPredictor
import os

# 深度学习匹配模型（懒加载）
_dl_model = None

def get_dl_model():
    global _dl_model
    if _dl_model is None:
        model_path = 'data/models/matching_model_best.pth'
        processor_path = 'data/models/text_processor.pkl'
        if os.path.exists(model_path) and os.path.exists(processor_path):
            try:
                _dl_model = MatchingPredictor(model_path, processor_path)
                print("✅ 深度学习匹配模型加载成功")
            except Exception as e:
                print(f"⚠️ 加载深度学习模型失败: {e}")
        else:
            print("⚠️ 未找到深度学习模型，将使用传统评分")
    return _dl_model

match_bp = Blueprint('match', __name__, url_prefix='/api/match')

# ====================== 全局配置 ======================
DEFAULT_WEIGHTS = {
    "基础要求": 0.12,
    "职业技能": 0.50,
    "职业素养": 0.18,
    "发展潜力": 0.20
}

def get_weights():
    return DEFAULT_WEIGHTS.copy()


# ====================== 工具函数 ======================
def extract_years_from_text(text):
    if not text:
        return 0.0
    text = str(text)
    years = 0.0
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*(?:年|yrs?|years?)', text, flags=re.IGNORECASE):
        try:
            years += float(m)
        except ValueError:
            continue
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*(?:月|mos?|months?)', text, flags=re.IGNORECASE):
        try:
            years += float(m) / 12.0
        except ValueError:
            continue
    return round(years, 2)


def extract_experience_requirement(text):
    if not text:
        return None
    text = str(text)
    m = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*年', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r'(\d+(?:\.\d+)?)\s*年以上', text)
    if m:
        v = float(m.group(1))
        return v, None
    m = re.search(r'经验\s*(\d+(?:\.\d+)?)\s*年', text)
    if m:
        v = float(m.group(1))
        return v, None
    return None


def normalize_education_level(level):
    if not level:
        return None
    level = str(level).strip().lower()
    if '博士' in level or 'phd' in level:
        return 4
    if '硕士' in level or 'master' in level:
        return 3
    if '本科' in level or 'bachelor' in level:
        return 2
    if '大专' in level or '专科' in level or 'associate' in level:
        return 1
    if '高中' in level or '中专' in level or '高职' in level:
        return 0
    return None


# ====================== 学校层次加成 ======================
def get_school_level(school_name):
    """识别学校层次，返回加成系数"""
    if not school_name:
        return 1.0
    
    top_schools = ['清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学', 
                   '中国科学技术大学', '南京大学', '西安交通大学', '哈尔滨工业大学',
                   '华中科技大学', '武汉大学', '中山大学', '四川大学', '南开大学',
                   '天津大学', '山东大学', '东南大学', '吉林大学', '厦门大学', '同济大学',
                   '北京航空航天大学', '北京理工大学', '中国人民大学', '中南大学', '大连理工大学']
    
    for top in top_schools:
        if top in school_name:
            return 1.15
    
    if '大学' in school_name and len(school_name) <= 15:
        return 1.05
    
    return 1.0


# ====================== 大类预筛选（专业为主） ======================
def get_relevant_categories(student_ability):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM job_categories")
    all_cats = cursor.fetchall()
    conn.close()

    major = student_ability.get('major') or ''
    if major:
        major_lower = major.lower()
        major_to_cat = {
            '计算机': '技术研发', '软件': '技术研发', '人工智能': '技术研发',
            '数据科学': '技术研发', '电子信息': '技术研发', '通信': '技术研发',
            '自动化': '技术研发', '设计': '产品设计', '艺术': '产品设计',
            '视觉': '产品设计', '动画': '产品设计', '市场': '市场营销',
            '营销': '市场营销', '工商': '市场营销', '管理': '运营管理',
            '人力': '运营管理', '行政': '行政办公', '中文': '运营管理',
            '新闻': '运营管理', '传播': '运营管理', '英语': '行政办公',
            '法学': '行政办公'
        }
        for kw, cat_name in major_to_cat.items():
            if kw in major_lower:
                for cat in all_cats:
                    if cat['name'] == cat_name:
                        print(f"[大类筛选] 专业匹配: {major} → {cat_name}")
                        return [cat['id']]

    interest = student_ability.get('interest', {})
    if interest:
        interest_to_cat = {'I': '技术研发', 'R': '技术研发', 'A': '产品设计',
                           'E': '市场营销', 'S': '运营管理', 'C': '行政办公'}
        top_dim = max(interest.items(), key=lambda x: x[1])[0]
        pref_cat_name = interest_to_cat.get(top_dim, '')
        if pref_cat_name:
            for cat in all_cats:
                if cat['name'] == pref_cat_name:
                    print(f"[大类筛选] 兴趣匹配: 最高维度 {top_dim} → {pref_cat_name}")
                    return [cat['id']]

    skills = student_ability.get('skills', set())
    skill_to_cat = {
        '技术研发': ['python', 'java', 'javascript', 'vue', 'react', 'c++', 'sql', '算法', '开发', '编程', 'html', 'css'],
        '产品设计': ['ui', 'ux', '设计', 'figma', 'ps', 'ai', 'sketch', '产品'],
        '市场营销': ['市场', '营销', '销售', '推广', '品牌', '广告', 'crm'],
        '运营管理': ['运营', '管理', '项目', '协调', 'pm', 'excel', 'word'],
        '行政办公': ['行政', '办公', '人事', '招聘', '文员']
    }
    for cat_name, keywords in skill_to_cat.items():
        if any(kw in skill.lower() for skill in skills for kw in keywords):
            for cat in all_cats:
                if cat['name'] == cat_name:
                    print(f"[大类筛选] 技能匹配: {cat_name}")
                    return [cat['id']]

    for cat in all_cats:
        if cat['name'] == '软件开发类':
            print(f"[大类筛选] 默认（技术研发）")
            return [cat['id']]
    
    if all_cats:
        print(f"[大类筛选] 默认（第一个）: {all_cats[0]['name']}")
        return [all_cats[0]['id']]
    return []


# ====================== 专业相关度计算 ======================
def get_major_relevance(student_ability, job_ability):
    major = student_ability.get('major') or ''
    if not major:
        return 1.0
    
    major_lower = major.lower()
    job_skills = job_ability.get('skills', set())
    job_skills_str = ' '.join(job_skills).lower()
    
    if any(kw in major_lower for kw in ['计算机', '软件', '人工智能', '数据科学', '电子信息']):
        tech_keywords = ['python', 'java', 'javascript', 'vue', 'react', 'sql', '算法', '开发', '编程']
        tech_match = sum(1 for kw in tech_keywords if kw in job_skills_str)
        if tech_match >= 2:
            return 1.30
        return 1.15
    
    if any(kw in major_lower for kw in ['设计', '艺术', '视觉']):
        design_keywords = ['ui', 'ux', '设计', 'photoshop', 'figma', 'sketch']
        design_match = sum(1 for kw in design_keywords if kw in job_skills_str)
        if design_match >= 1:
            return 1.20
        return 1.0
    
    if any(kw in major_lower for kw in ['管理', '营销', '经济', '金融', '工商']):
        business_keywords = ['产品', '运营', '市场', '分析', '管理']
        business_match = sum(1 for kw in business_keywords if kw in job_skills_str)
        if business_match >= 1:
            return 1.15
        return 0.95
    
    return 0.85


# ====================== 核心技能覆盖固定加分 ======================
def get_core_skill_bonus(student_skills, job_skills):
    if not job_skills or not student_skills:
        return 0.0
    core_skills = list(job_skills)[:3] if len(job_skills) >= 3 else list(job_skills)
    if not core_skills:
        return 0.0
    covered = sum(1 for s in core_skills if s in student_skills)
    if covered >= 3:
        return 0.35
    elif covered == 2:
        return 0.25
    elif covered == 1:
        return 0.15
    else:
        return 0.0


# ====================== 技能深度固定加分 ======================
def get_skill_depth(student_ability, job_skills):
    project_techs = set()
    for proj in student_ability.get('project_json', []):
        tech_stack = proj.get('technology_stack', '')
        if tech_stack:
            if isinstance(tech_stack, list):
                for tech in tech_stack:
                    tech_clean = tech.lower().strip()
                    if tech_clean:
                        project_techs.add(tech_clean)
            elif isinstance(tech_stack, str):
                for tech in re.split(r'[,、，]', tech_stack):
                    tech_clean = tech.lower().strip()
                    if tech_clean:
                        project_techs.add(tech_clean)
    if not project_techs or not job_skills:
        return 0.0
    job_skills_lower = {s.lower() for s in job_skills}
    intersection = project_techs & job_skills_lower
    matched_count = len(intersection)
    if matched_count >= 5:
        return 0.30
    elif matched_count >= 3:
        return 0.20
    elif matched_count >= 1:
        return 0.10
    else:
        return 0.0


# ====================== 学生能力获取 ======================
def get_student_ability(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT skills, certificates, soft_abilities, user_id, major, grade, internships,
               education_json, work_json, project_json
        FROM student WHERE id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    skills = set(json.loads(row['skills']) if row['skills'] else [])
    certificates = set(json.loads(row['certificates']) if row['certificates'] else [])
    soft_abilities = json.loads(row['soft_abilities']) if row['soft_abilities'] else {}

    education_json = json.loads(row['education_json']) if row['education_json'] else {}
    degree = education_json.get('degree', '')
    school_name = education_json.get('school', '')
    if degree:
        student_edu = normalize_education_level(degree)
    else:
        student_edu = normalize_education_level(row['grade'] or row['major'])

    work_json = json.loads(row['work_json']) if row['work_json'] else []
    total_months = 0
    for exp in work_json:
        date_range = exp.get('date_range', '')
        match = re.search(r'(\d{4})\.(\d{1,2})-(\d{4})\.(\d{1,2})', date_range)
        if match:
            start_year, start_month, end_year, end_month = map(int, match.groups())
            total_months += (end_year - start_year) * 12 + (end_month - start_month)
    estimated_exp = total_months / 12.0
    if estimated_exp == 0:
        estimated_exp = extract_years_from_text(row['internships'] or '')

    project_json = json.loads(row['project_json']) if row['project_json'] else []

    student = {
        'skills': skills,
        'certificates': certificates,
        'soft_abilities': soft_abilities,
        'user_id': row['user_id'],
        'major': row['major'] or '',
        'grade': row['grade'] or '',
        'internships': row['internships'] or '',
        'experience_years': estimated_exp,
        'education_json': education_json,
        'work_json': work_json,
        'project_json': project_json,
        'school_name': school_name
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


def build_resume_text_from_ability(student_ability):
    """从 student_ability 字典构建完整简历文本，用于深度学习模型"""
    parts = []
    if student_ability.get('skills'):
        skills_str = "、".join(list(student_ability['skills'])[:20])
        parts.append(f"技能：{skills_str}")
    if student_ability.get('certificates'):
        certs_str = "、".join(list(student_ability['certificates'])[:10])
        parts.append(f"证书：{certs_str}")
    if student_ability.get('work_json'):
        for exp in student_ability['work_json'][:3]:
            company = exp.get('company', '')
            position = exp.get('position', '')
            achievements = exp.get('achievements', '')
            parts.append(f"工作：{company} {position} {achievements}")
    if student_ability.get('project_json'):
        for proj in student_ability['project_json'][:3]:
            name = proj.get('project_name', '')
            desc = proj.get('description', '')
            tech = proj.get('technology_stack', '')
            parts.append(f"项目：{name} {desc} 技术栈：{tech}")
    if student_ability.get('education_json'):
        edu = student_ability['education_json']
        school = edu.get('school', '')
        major = edu.get('major', '')
        degree = edu.get('degree', '')
        parts.append(f"教育：{school} {major} {degree}")
    return " ".join(parts)


# ====================== 岗位能力获取（带缓存） ======================
@lru_cache(maxsize=256)
def get_job_abilities(job_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT skills, certificates, soft_abilities FROM job_profile WHERE job_name = ?', (job_name,))
    row = cursor.fetchone()
    cursor.execute('SELECT job_description FROM job WHERE job_name = ?', (job_name,))
    job_row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            'skills': set(),
            'certificates': set(),
            'soft_abilities': {},
            'experience_requirement': None,
            'education_required': None
        }

    job_description = ''
    if job_row and 'job_description' in job_row.keys() and job_row['job_description']:
        job_description = job_row['job_description']
    
    exp_req = extract_experience_requirement(job_description)
    edu_req = None
    edu_match = re.search(r'(博士|硕士|本科|大专|专科|高中|phd|master|bachelor|associate)', job_description or '', flags=re.IGNORECASE)
    if edu_match:
        edu_req = normalize_education_level(edu_match.group(1))

    return {
        'skills': set(json.loads(row['skills']) if row['skills'] else []),
        'certificates': set(json.loads(row['certificates']) if row['certificates'] else []),
        'soft_abilities': json.loads(row['soft_abilities']) if row['soft_abilities'] else {},
        'experience_requirement': exp_req,
        'education_required': edu_req
    }


# ====================== 匹配度计算 ======================
def compute_match(student_ability, job_ability, generate_gap=False, job_name=None):
    # ========== 1. 技能匹配 ==========
    if student_ability['skills'] and job_ability['skills']:
        skill_inter = student_ability['skills'] & job_ability['skills']
        skill_union = student_ability['skills'] | job_ability['skills']
        base_skill_sim = len(skill_inter) / len(skill_union) if skill_union else 0.0
    else:
        base_skill_sim = 0.0
    
    core_bonus = get_core_skill_bonus(student_ability['skills'], job_ability['skills'])
    depth_bonus = get_skill_depth(student_ability, job_ability['skills'])
    
    skill_sim = min(1.0, base_skill_sim + core_bonus + depth_bonus)
    major_relevance = get_major_relevance(student_ability, job_ability)
    skill_sim = min(1.0, skill_sim * major_relevance)

    # ========== 2. 证书覆盖率 ==========
    if student_ability['certificates'] and job_ability['certificates']:
        cert_cov = len(student_ability['certificates'] & job_ability['certificates']) / len(job_ability['certificates'])
    else:
        cert_cov = 0.0

    # ========== 3. 软能力相似度 ==========
    stu_soft = student_ability.get('soft_abilities', {})
    job_soft = job_ability.get('soft_abilities', {})
    common_dims = set(stu_soft.keys()) & set(job_soft.keys())
    if common_dims:
        stu_vec = [float(stu_soft[d].get('score', 0)) for d in common_dims]
        job_vec = [float(job_soft[d].get('score', 0)) for d in common_dims]
        dot = sum(a * b for a, b in zip(stu_vec, job_vec))
        norm_stu = sum(a * a for a in stu_vec) ** 0.5
        norm_job = sum(b * b for b in job_vec) ** 0.5
        soft_sim = dot / (norm_stu * norm_job) if norm_stu and norm_job else 0.0
        soft_gap = 1 - soft_sim
    else:
        soft_sim = 0.0
        soft_gap = 1.0
    
    soft_score_raw = soft_sim * 100
    if soft_sim >= 0.9:
        soft_score = min(100, soft_score_raw + 5)
    elif soft_sim >= 0.7:
        soft_score = soft_score_raw
    elif soft_sim >= 0.5:
        soft_score = soft_score_raw - 10
    else:
        soft_score = soft_score_raw * 0.6
    soft_score = max(0, min(100, soft_score))

    # ========== 4. 教育背景匹配 ==========
    student_edu = None
    school_name = student_ability.get('school_name', '')
    if 'education_json' in student_ability and student_ability['education_json']:
        degree = student_ability['education_json'].get('degree', '')
        if degree:
            student_edu = normalize_education_level(degree)
    if student_edu is None:
        student_edu = normalize_education_level(student_ability.get('grade') or student_ability.get('major'))
    
    required_edu = job_ability.get('education_required')
    
    if student_edu is None:
        edu_base_score = 40
    elif student_edu >= 3:
        edu_base_score = 100
    elif student_edu >= 2:
        edu_base_score = 80
    elif student_edu >= 1:
        edu_base_score = 60
    else:
        edu_base_score = 40
    
    if required_edu is None:
        job_edu_score = 60
    elif required_edu >= 3:
        job_edu_score = 100
    elif required_edu >= 2:
        job_edu_score = 80
    elif required_edu >= 1:
        job_edu_score = 60
    else:
        job_edu_score = 40
    
    edu_match_score = edu_base_score
    if required_edu is not None and student_edu is not None:
        edu_gap = student_edu - required_edu
        if edu_gap < 0:
            edu_match_score = max(0, edu_base_score + edu_gap * 20)
        elif edu_gap > 0:
            edu_match_score = min(100, edu_base_score + min(edu_gap, 2) * 10)
    
    school_bonus = get_school_level(school_name)
    if school_bonus >= 1.15:
        school_bonus_score = 20
    elif school_bonus >= 1.05:
        school_bonus_score = 10
    else:
        school_bonus_score = 0
    education_score = min(100, edu_match_score + school_bonus_score)

    # ========== 5. 经验匹配 ==========
    stu_exp = float(student_ability.get('experience_years') or 0.0)
    exp_req = job_ability.get('experience_requirement')
    if exp_req:
        min_req, max_req = exp_req
        if min_req is not None and stu_exp < min_req:
            gap = min_req - stu_exp
            exp_score = max(0, 100 - int(gap * 20))
        elif max_req is not None and stu_exp > max_req:
            gap = stu_exp - max_req
            exp_score = max(0, 100 - int(gap * 10))
        else:
            exp_score = 100
    else:
        if stu_exp >= 2:
            exp_score = 100
        elif stu_exp >= 1:
            exp_score = 80
        elif stu_exp >= 0.5:
            exp_score = 60
        elif stu_exp > 0:
            exp_score = 40
        else:
            exp_score = 20

    # ========== 6. 证书匹配 ==========
    cert_score = cert_cov * 100

    # ========== 7. 综合得分 ==========
    weights = get_weights()
    total = (
        weights["职业技能"] * (skill_sim * 100) +
        weights["职业素养"] * soft_score +
        weights["基础要求"] * education_score +
        weights["发展潜力"] * exp_score +
        0.03 * cert_score
    ) / 100
    total = max(0.0, min(1.0, total))

    # ---------- 集成深度学习模型 ----------
    dl_score = None
    dl_model = get_dl_model()
    if dl_model is not None and job_name is not None:
        try:
            resume_text = build_resume_text_from_ability(student_ability)
            job_text = job_name + " " + job_ability.get('job_description', '')
            dl_score = dl_model.predict(resume_text, job_text)
            # 加权融合：传统评分0.4，深度学习0.6
            final_score = total * 0.4 + (dl_score / 100) * 0.6
            print(f"✅ 深度学习匹配分: {dl_score}, 融合后总分: {final_score:.3f}")
            total = final_score
        except Exception as e:
            print(f"⚠️ 深度学习预测失败: {e}")
    # ------------------------------------

    match_detail = {
        'overall_score': round(total * 100, 1),
        'dl_score': dl_score if dl_score is not None else None,
        'skill_fit': round(skill_sim * 100, 1),
        'soft_gap': round(soft_gap * 100, 1),
        'cert_coverage': round(cert_cov * 100, 1),
        'education_score': round(education_score, 1),
        'experience_score': round(exp_score, 1),
        'debug_info': {
            'base_skill_sim': round(base_skill_sim * 100, 1),
            'core_bonus': round(core_bonus * 100, 1),
            'depth_bonus': round(depth_bonus * 100, 1),
            'major_relevance': round(major_relevance, 2),
            'edu_base_score': edu_base_score,
            'edu_match_score': edu_match_score,
            'school_bonus_score': school_bonus_score,
            'soft_score': soft_score
        }
    }

    if generate_gap:
        match_detail['gap_analysis'] = generate_gap_analysis_with_llm(student_ability, job_ability, match_detail)
    else:
        match_detail['gap_analysis'] = {}
    return match_detail


# ====================== 差距分析生成 ======================
def generate_gap_analysis_with_llm(student_ability, job_ability, match_detail):
    need_skills = list(job_ability['skills'] - student_ability['skills'])
    need_certs = list(job_ability['certificates'] - student_ability['certificates'])
    soft_gaps = []
    for dim, job_val in job_ability['soft_abilities'].items():
        stu_val = student_ability['soft_abilities'].get(dim, {}).get('score', 0)
        job_score = job_val.get('score', 0)
        if isinstance(job_score, (int, float)) and job_score > stu_val + 1:
            soft_gaps.append(dim)

    prompt = f"""
你是一位专业的职业规划师。根据以下学生与目标岗位的匹配数据，为每个维度生成一段具体的、有针对性的改进建议。
要求：
- 每个维度一段话，直接针对缺失项给出建议，不要使用"根据您的情况"之类的开头。
- 语气专业、鼓励，长度适中（每段50-100字）。
- 基于实际缺失项，不要泛泛而谈。

匹配数据：
- 证书覆盖率：{match_detail['cert_coverage']}%
- 缺失的证书：{', '.join(need_certs) if need_certs else '无'}
- 技能匹配度：{match_detail['skill_fit']}%
- 缺失的技能：{', '.join(need_skills) if need_skills else '无'}
- 软能力差距维度：{', '.join(soft_gaps) if soft_gaps else '无'}
- 综合匹配度：{match_detail['overall_score']}%

请按以下 JSON 格式返回五个维度的建议（只返回 JSON，不要其他文字）：
{{
    "base": "证书方面的建议",
    "skills": "技能方面的建议",
    "quality": "软能力方面的建议",
    "potential": "发展潜力方面的建议",
    "recommended_resources": "学习资源建议（课程/书籍/项目）"
}}
"""
    try:
        result = call_llm(prompt, temperature=0.7, max_tokens=800)
        if not result:
            raise ValueError("LLM 返回空结果")
        json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        analysis = json.loads(result)
        required = ['base', 'skills', 'quality', 'potential', 'recommended_resources']
        for field in required:
            if field not in analysis or not analysis[field]:
                if field == 'recommended_resources':
                    analysis[field] = "推荐 Coursera、慕课网、书籍等学习资源，并结合项目实战提升。"
                else:
                    analysis[field] = f"请针对{field}加强学习。"
        return analysis
    except Exception as e:
        print(f"大模型生成差距分析失败：{e}")
        return {
            "base": "请根据岗位要求补充相关证书。",
            "skills": "建议针对缺失技能进行系统学习。",
            "quality": "可参加团队项目锻炼软能力。",
            "potential": "制定长期提升计划，逐步追赶岗位要求。",
            "recommended_resources": "推荐 Coursera、慕课网、书籍等学习资源，并结合项目实战提升。"
        }


# ====================== 接口：推荐岗位列表 ======================
@match_bp.route('/recommend', methods=['GET'])
def recommend():
    student_id = request.args.get('student_id', type=int)
    limit = request.args.get('limit', 10, type=int)

    if student_id is None:
        return jsonify({'error': '缺少 student_id 参数'}), 400

    student_ability = get_student_ability(student_id)
    if not student_ability:
        return jsonify({'error': '学生不存在'}), 404

    if not student_ability.get('skills'):
        return jsonify({'error': '学生能力数据不完整，请先完善技能信息'}), 400

    relevant_cat_ids = get_relevant_categories(student_ability)

    conn = get_db()
    cursor = conn.cursor()

    if relevant_cat_ids:
        placeholders = ','.join('?' for _ in relevant_cat_ids)
        cursor.execute(f"""
            SELECT DISTINCT job_name
            FROM job
            WHERE category_id IN ({placeholders})
        """, relevant_cat_ids)
    else:
        cursor.execute("SELECT DISTINCT job_name FROM job")

    unique_job_names = [row['job_name'] for row in cursor.fetchall()]
    conn.close()

    if not unique_job_names:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT job_name FROM job_profile")
        unique_job_names = [row['job_name'] for row in cursor.fetchall()]
        conn.close()

    if not unique_job_names:
        return jsonify({'message': '暂无岗位数据', 'results': []}), 200

    results = []
    for job_name in unique_job_names:
        job_ability = get_job_abilities(job_name)
        match_detail = compute_match(student_ability, job_ability, generate_gap=False, job_name=job_name)
        item = {'job_name': job_name, **match_detail}
        if 'interest' in student_ability:
            item['interest_scores'] = student_ability['interest']
        results.append(item)

    results.sort(key=lambda x: x['overall_score'], reverse=True)
    filtered = results[:limit]

    return jsonify({'results': filtered, 'total': len(results)})


# ====================== 接口：单岗位详细匹配 ======================
@match_bp.route('/match', methods=['POST'])
def match():
    data = request.json
    student_id = data.get('student_id')
    job_name = data.get('job_name')
    if not student_id or not job_name:
        return jsonify({'error': '缺少参数'}), 400

    student_ability = get_student_ability(student_id)
    if not student_ability:
        return jsonify({'error': '学生不存在'}), 404

    if not student_ability.get('skills'):
        return jsonify({'error': '学生能力数据不完整，请先完善技能信息'}), 400

    job_ability = get_job_abilities(job_name)
    match_detail = compute_match(student_ability, job_ability, generate_gap=True, job_name=job_name)

    try:
        conn = get_db()
        cursor = conn.cursor()
        details_json = json.dumps(match_detail, ensure_ascii=False)
        cursor.execute('''
            INSERT INTO match_history 
            (student_id, job_name, match_score, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            student_id,
            job_name,
            match_detail['overall_score'],
            details_json,
            int(time.time())
        ))
        conn.commit()
        print("✅ 匹配记录已保存")
    except Exception as e:
        print("❌ 保存失败：", e)
    finally:
        if 'conn' in locals():
            conn.close()

    return jsonify(match_detail)


# ====================== 接口：匹配历史 ======================
@match_bp.route('/history/<int:student_id>', methods=['GET'])
@token_required
def get_match_history(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, job_name, match_score, details, created_at
        FROM match_history
        WHERE student_id = ?
        ORDER BY created_at DESC
    ''', (student_id,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        history.append({
            'id': r['id'],
            'job_name': r['job_name'],
            'match_score': r['match_score'],
            'details': r['details'],
            'created_at': r['created_at']
        })
    return jsonify({'history': history})


# ====================== 流式匹配接口 ======================
@match_bp.route('/match-stream', methods=['POST'])
def match_stream():
    data = request.json
    student_id = data.get('student_id')
    job_name = data.get('job_name')
    if not student_id or not job_name:
        return jsonify({'error': '缺少参数'}), 400

    student_ability = get_student_ability(student_id)
    if not student_ability:
        return jsonify({'error': '学生不存在'}), 404
    if not student_ability.get('skills'):
        return jsonify({'error': '学生能力数据不完整，请先完善技能信息'}), 400

    job_ability = get_job_abilities(job_name)
    match_detail = compute_match(student_ability, job_ability, generate_gap=False, job_name=job_name)

    def generate():
        base_info = {
            'overall_score': match_detail['overall_score'],
            'skill_fit': match_detail['skill_fit'],
            'soft_gap': match_detail['soft_gap'],
            'cert_coverage': match_detail['cert_coverage'],
            'education_score': match_detail['education_score'],
            'experience_score': match_detail['experience_score'],
            'debug_info': match_detail.get('debug_info', {})
        }
        yield f"data: {json.dumps({'type': 'base', 'data': base_info})}\n\n"

        full_analysis = generate_gap_analysis_with_llm(student_ability, job_ability, match_detail)
        for key in ['base', 'skills', 'quality', 'potential', 'recommended_resources']:
            text = full_analysis.get(key, '')
            yield f"data: {json.dumps({'type': 'gap', 'field': key, 'text': text})}\n\n"
            time.sleep(0.03)

        match_detail['gap_analysis'] = full_analysis
        try:
            conn = get_db()
            cursor = conn.cursor()
            details_json = json.dumps(match_detail, ensure_ascii=False)
            cursor.execute('''
                INSERT INTO match_history 
                (student_id, job_name, match_score, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                student_id,
                job_name,
                match_detail['overall_score'],
                details_json,
                int(time.time())
            ))
            conn.commit()
        except Exception as e:
            print("保存失败", e)
        finally:
            if 'conn' in locals():
                conn.close()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')