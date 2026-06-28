import json
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from db import get_db
from services.llm_client import LLMClient, local_answer
from services.ml_recommender import build_job_profile, recommend_jobs_for_candidate, split_skills


def call_llm(prompt: str, temperature=0.3, max_tokens=2000, thinking=False, max_retries=1) -> str:
    try:
        return LLMClient().chat(
            [{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception:
        return local_answer([{"role": "user", "content": prompt}])


def call_llm_stream(prompt: str, temperature=0.7, max_tokens=2000) -> Iterator[str]:
    try:
        yield from LLMClient().stream_chat(
            [{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception:
        yield local_answer([{"role": "user", "content": prompt}])


def chat_qa(question: str, context: str = "") -> str:
    prompt = f"问题：{question}\n背景：{context}\n请给出职业规划相关的具体建议。"
    return call_llm(prompt, temperature=0.3, max_tokens=1200)


def generate_plan_suggestion(student: Dict[str, Any], job_name: str) -> str:
    prompt = (
        f"请为大学生生成面向「{job_name or '目标岗位'}」的职业规划建议，"
        "包含技能提升、项目实践、简历优化和面试准备。\n"
        f"学生信息：{json.dumps(student or {}, ensure_ascii=False)}"
    )
    return call_llm(prompt, temperature=0.4, max_tokens=1800)


def intelligent_recommendation(student: Dict[str, Any], jobs: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    candidate = {
        "candidate_id": student.get("id") or student.get("candidate_id"),
        "skills": student.get("skills") or student.get("skill") or "",
        "preferred_categories": student.get("preferred_categories") or student.get("interests") or "",
        "expected_salary_min": student.get("expected_salary_min") or 0,
        "expected_salary_max": student.get("expected_salary_max") or 0,
        "education": student.get("education") or student.get("grade") or "",
    }
    normalized_jobs = []
    for job in jobs:
        normalized_jobs.append({
            "job_id": job.get("job_id") or job.get("job_code") or job.get("id"),
            "job_title": job.get("job_title") or job.get("job_name"),
            "job_category": job.get("job_category") or job.get("industry"),
            "skills": job.get("skills") or "",
            "job_description": job.get("job_description") or "",
            "requirements": job.get("requirements") or "",
            "salary_min": job.get("salary_min") or 0,
            "salary_max": job.get("salary_max") or 0,
        })
    recs = recommend_jobs_for_candidate(candidate, normalized_jobs, top_k=top_n)
    return [{"job": rec, "match": {"overall_score": round(rec["score"] * 100, 1), **rec["explain"]}} for rec in recs]


def generate_dynamic_job_profile(job_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT
                job.job_code as job_id,
                COALESCE(jobs.job_title, job.job_name) as job_title,
                COALESCE(jobs.job_category, job.industry) as job_category,
                job.salary_range,
                job.job_description,
                job.company,
                jobs.skills,
                jobs.requirements,
                jobs.salary_min,
                jobs.salary_max
            FROM job
            LEFT JOIN jobs ON jobs.job_id = job.job_code
            WHERE job.job_name = ? LIMIT 1
        """, (job_name,)).fetchone()
        if not row:
            return None
        return build_job_profile(dict(row))
    finally:
        conn.close()


def get_job_skills(job_name: str) -> List[str]:
    conn = get_db()
    try:
        row = conn.execute("SELECT skills FROM job_profile WHERE job_name = ?", (job_name,)).fetchone()
        if row and row["skills"]:
            return json.loads(row["skills"])
        job = conn.execute("""
            SELECT job.job_name as job_title, job.industry as job_category,
                   job.job_description, jobs.skills, jobs.requirements
            FROM job
            LEFT JOIN jobs ON jobs.job_id = job.job_code
            WHERE job.job_name = ? LIMIT 1
        """, (job_name,)).fetchone()
        if job and job["job_description"]:
            return build_job_profile(dict(job))["skills"]
        return []
    finally:
        conn.close()


def get_job_category(job_name: str) -> str:
    conn = get_db()
    try:
        row = conn.execute("SELECT industry FROM job WHERE job_name = ? LIMIT 1", (job_name,)).fetchone()
        return row["industry"] if row and row["industry"] else ""
    finally:
        conn.close()


def rebuild_job_graph() -> Tuple[int, int]:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM job_relations")
        rows = cursor.execute("SELECT DISTINCT job_name, industry FROM job WHERE job_name IS NOT NULL LIMIT 50").fetchall()
        by_category: Dict[str, List[str]] = {}
        for row in rows:
            by_category.setdefault(row["industry"] or "通用", []).append(row["job_name"])
        lateral_count = 0
        for names in by_category.values():
            for left, right in zip(names, names[1:]):
                cursor.execute(
                    "INSERT INTO job_relations (from_job, to_job, relation_type, description) VALUES (?, ?, ?, ?)",
                    (left, right, "transition", f"{left} 与 {right} 属于相近岗位方向，可按技能差距转型。"),
                )
                lateral_count += 1
        conn.commit()
        return 0, lateral_count
    finally:
        conn.close()


def build_category_profiles():
    conn = get_db()
    try:
        rows = conn.execute("SELECT DISTINCT job_category AS industry FROM jobs WHERE job_category IS NOT NULL AND job_category != ''").fetchall()
        return [row["industry"] for row in rows]
    finally:
        conn.close()


def assign_jobs_to_categories():
    return 0
