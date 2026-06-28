"""
算法模块：职业匹配、推荐与评分（基础实现）

说明：
- 本文件夹下的代码皆为临时所用，只做历史保留
- 提供可单元测试的函数：`compute_match_score`, `recommend_jobs`, `score_student_competitiveness`
- 为项目中其他服务（如 `services/llm_service.py`）提供稳定的接口
"""
from typing import List, Dict, Any, Tuple
import json
from difflib import SequenceMatcher


def _list_from_json(maybe_json):
    if maybe_json is None:
        return []
    if isinstance(maybe_json, list):
        return maybe_json
    try:
        return json.loads(maybe_json)
    except Exception:
        # assume comma-separated
        return [s.strip() for s in str(maybe_json).split(',') if s.strip()]


def compute_match_score(student: Dict[str, Any], job_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算学生与岗位画像的匹配分。
    输出包含 overall_score、skill_score、text_similarity、soft_score、skill_overlap、exp_bonus。
    """
    # 1) 技能匹配（考虑技能重要性）
    stu_skills = set([s.lower() for s in _list_from_json(student.get('skills'))])
    job_skills_list = _list_from_json(job_profile.get('skills'))
    # 支持岗位技能为 list 或 dict（带权重）
    job_skills = set()
    skill_weights = {}
    if isinstance(job_skills_list, dict):
        for k, v in job_skills_list.items():
            job_skills.add(str(k).lower())
            try:
                skill_weights[str(k).lower()] = float(v)
            except Exception:
                skill_weights[str(k).lower()] = 1.0
    else:
        for s in job_skills_list:
            job_skills.add(str(s).lower())
            skill_weights[str(s).lower()] = 1.0

    matched = stu_skills & job_skills
    if not job_skills:
        skill_score = 0.0
    else:
        matched_weight = sum(skill_weights.get(s, 1.0) for s in matched)
        total_weight = sum(skill_weights.get(s, 1.0) for s in job_skills)
        skill_score = matched_weight / max(total_weight, 1e-6)

    # 2) 文本相似度（兴趣+技能 与 岗位描述）
    text_a = ' '.join(_list_from_json(student.get('interests')) + _list_from_json(student.get('skills'))).lower()
    desc = (job_profile.get('job_description') or '') or (job_profile.get('company_info') or '')
    text_b = (job_profile.get('job_name') or '') + ' ' + str(desc)
    text_b = text_b.lower()
    txt_sim = 0.0
    if text_a.strip() and text_b.strip():
        txt_sim = SequenceMatcher(None, text_a, text_b).ratio()

    # 3) 软能力匹配：岗位需要的软能力 vs 学生竞争力/完整度
    soft = job_profile.get('soft_abilities') or {}
    if isinstance(soft, str):
        try:
            soft = json.loads(soft)
        except Exception:
            soft = {}
    avg_soft_req = 0.0
    if soft:
        vals = [v for v in soft.values() if isinstance(v, (int, float))]
        if vals:
            avg_soft_req = sum(vals) / (len(vals) * 100.0)

    competitiveness = (student.get('competitiveness') or 50) / 100.0
    completeness = (student.get('completeness') or 50) / 100.0
    soft_score = 1.0 - abs(competitiveness - avg_soft_req)
    soft_score = max(0.0, min(1.0, soft_score)) * 0.9 + completeness * 0.1

    # 经验加成
    exp_bonus = 0.0
    internships = student.get('internships') or ''
    if isinstance(internships, str) and internships:
        if '月' in internships or '年' in internships or 'month' in internships or 'year' in internships:
            exp_bonus = 0.05
        else:
            exp_bonus = 0.02

    # 合并得分（基础权重）
    w_skill = 0.55
    w_text = 0.25
    w_soft = 0.20
    overall = skill_score * w_skill + txt_sim * w_text + soft_score * w_soft + exp_bonus
    overall = max(0.0, min(1.0, overall))

    return {
        'overall_score': round(overall, 4),
        'skill_score': round(skill_score, 4),
        'text_similarity': round(txt_sim, 4),
        'soft_score': round(soft_score, 4),
        'skill_overlap': list(matched),
        'exp_bonus': round(exp_bonus, 4)
    }


def recommend_jobs(student: Dict[str, Any], jobs: List[Dict[str, Any]], top_n: int = 5) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    给定学生信息和岗位列表，返回按匹配分排序的前 top_n 个岗位及匹配详情
    返回列表元素为 (job, match_detail)
    """
    scored = []
    for job in jobs:
        job_profile = {
            'job_name': job.get('job_name') or job.get('jobName') or '',
            'skills': job.get('skills') or job.get('required_skills') or [],
            'industry': job.get('industry') or job.get('company') or '',
            'soft_abilities': job.get('soft_abilities') or {}
        }
        score = compute_match_score(student, job_profile)
        scored.append((job, score))
    scored.sort(key=lambda t: t[1]['overall_score'], reverse=True)
    return scored[:top_n]


def score_student_competitiveness(student: Dict[str, Any]) -> int:
    """
    根据简历信息给出一个 0-100 的竞争力评分（启发式）
    """
    skills = _list_from_json(student.get('skills'))
    certs = _list_from_json(student.get('certificates'))
    internships = student.get('internships')
    completeness = student.get('completeness') or 50

    score = 40.0
    score += min(30, len(skills) * 3)
    score += min(15, len(certs) * 2)
    if internships:
        score += 10
    score += (completeness / 100.0) * 5

    score = max(0, min(100, int(score)))
    return score


if __name__ == '__main__':
    student = {'skills': ['python', 'django'], 'interests': ['后端'], 'competitiveness': 70}
    jobs = [{'job_name': '后端开发工程师', 'skills': ['python', 'flask'], 'industry': '软件'}]
    print(recommend_jobs(student, jobs))
