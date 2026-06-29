import re
from typing import Dict, Iterable, List


SKILL_SPLIT_RE = re.compile(r"[,，、/\s]+")
COMMON_SKILLS = [
    "Python", "Java", "SQL", "Flask", "Django", "Vue", "React", "Linux",
    "Docker", "Kubernetes", "Redis", "TensorFlow", "PyTorch", "Excel",
    "PPT", "数据分析", "机器学习", "沟通", "运营", "产品",
]


def split_skills(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = [str(v) for v in value]
    else:
        raw = [part for part in SKILL_SPLIT_RE.split(str(value)) if part]
    seen = set()
    result = []
    for item in raw:
        skill = item.strip()
        if not skill:
            continue
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            result.append(skill)
    return result


def extract_skills_from_text(text: str) -> List[str]:
    found = []
    lower = (text or "").lower()
    for skill in COMMON_SKILLS:
        if skill.lower() in lower or skill in (text or ""):
            found.append(skill)
    return found


def build_job_profile(job: Dict) -> Dict:
    explicit = split_skills(job.get("skills"))
    text = " ".join([
        str(job.get("job_title", "")),
        str(job.get("job_description", "")),
        str(job.get("requirements", "")),
    ])
    skills = explicit or extract_skills_from_text(text)
    soft_abilities = {
        "学习能力": {"score": 4, "description": "需要持续学习岗位相关工具和业务知识"},
        "沟通能力": {"score": 4 if "沟通" in text else 3, "description": "需要跨角色协作并清晰表达问题"},
        "抗压能力": {"score": 3, "description": "需要在项目节点内稳定交付"},
    }
    return {
        "job_id": job.get("job_id"),
        "job_name": job.get("job_title") or job.get("job_name"),
        "category": job.get("job_category") or job.get("industry"),
        "skills": skills,
        "certificates": [],
        "soft_abilities": soft_abilities,
        "source": "ml_rules",
    }


def _salary_score(candidate: Dict, job: Dict) -> float:
    try:
        c_min = float(candidate.get("expected_salary_min") or 0)
        c_max = float(candidate.get("expected_salary_max") or 0)
        j_min = float(job.get("salary_min") or 0)
        j_max = float(job.get("salary_max") or 0)
    except (TypeError, ValueError):
        return 0.5
    if not any([c_min, c_max, j_min, j_max]):
        return 0.5
    overlap = max(0.0, min(c_max, j_max) - max(c_min, j_min))
    span = max(c_max, j_max) - min(c_min, j_min)
    return overlap / span if span else 0.5


def score_candidate_job(candidate: Dict, job: Dict) -> Dict:
    candidate_skills = {s.lower() for s in split_skills(candidate.get("skills"))}
    profile = build_job_profile(job)
    job_skills = {s.lower() for s in profile["skills"]}
    overlap = candidate_skills & job_skills
    skill_score = len(overlap) / len(job_skills) if job_skills else 0.0

    preferred = str(candidate.get("preferred_categories") or "")
    category = str(job.get("job_category") or job.get("industry") or "")
    category_score = 1.0 if category and category in preferred else 0.4
    salary_score = _salary_score(candidate, job)
    score = 0.6 * skill_score + 0.2 * category_score + 0.2 * salary_score
    return {
        "job_id": job.get("job_id"),
        "job_name": job.get("job_title") or job.get("job_name"),
        "score": round(score, 4),
        "explain": {
            "skill_overlap": sorted(overlap),
            "skill_score": round(skill_score, 4),
            "category_score": round(category_score, 4),
            "salary_score": round(salary_score, 4),
        },
        "profile": profile,
    }


def recommend_jobs_for_candidate(candidate: Dict, jobs: Iterable[Dict], top_k: int = 10) -> List[Dict]:
    scored = [score_candidate_job(candidate, job) for job in jobs]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
