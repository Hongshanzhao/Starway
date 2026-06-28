"""
Compatibility facade for older Starway imports.

New runtime code should prefer career_ai_service, llm_client, and
ml_recommender directly. This module keeps historical function names available
without carrying the removed vendor implementation.
"""

import json
from typing import Any, Dict, Iterable, List, Tuple

from db import get_db
from services import career_ai_service
from services.ml_recommender import build_job_profile


def call_llm(prompt: str, temperature=0.3, max_tokens=2000, thinking=False, max_retries=1) -> str:
    return career_ai_service.call_llm(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        thinking=thinking,
        max_retries=max_retries,
    )


def call_llm_stream(prompt: str, temperature=0.7, max_tokens=2000) -> Iterable[str]:
    return career_ai_service.call_llm_stream(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def chat_qa(question: str, context: str = "") -> str:
    return career_ai_service.chat_qa(question, context)


def generate_plan_suggestion(student: Dict[str, Any], job_name: str) -> str:
    return career_ai_service.generate_plan_suggestion(student, job_name)


def intelligent_recommendation(student: Dict[str, Any], jobs: List[Dict[str, Any]], top_n: int = 5):
    return career_ai_service.intelligent_recommendation(student, jobs, top_n)


def generate_dynamic_job_profile(job_name: str):
    return career_ai_service.generate_dynamic_job_profile(job_name)


def get_job_skills(job_name: str) -> List[str]:
    return career_ai_service.get_job_skills(job_name)


def get_job_category(job_name: str) -> str:
    return career_ai_service.get_job_category(job_name)


def rebuild_job_graph() -> Tuple[int, int]:
    return career_ai_service.rebuild_job_graph()


def build_category_profiles():
    return career_ai_service.build_category_profiles()


def assign_jobs_to_categories():
    return career_ai_service.assign_jobs_to_categories()


def parse_resume(file_path: str) -> Dict[str, Any]:
    text = ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        pass
    profile = build_job_profile({"job_title": "candidate", "job_description": text, "skills": text})
    return {
        "name": "",
        "major": "",
        "grade": "",
        "skills": profile.get("skills", []),
        "certificates": [],
        "internships": "",
        "interests": [],
        "completeness": 70 if text else 30,
        "competitiveness": 60 if profile.get("skills") else 40,
    }


def get_job_description(job_name: str) -> str:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT job_description FROM job WHERE job_name = ? LIMIT 1",
            (job_name,),
        ).fetchone()
        return row["job_description"] if row and row["job_description"] else ""
    finally:
        conn.close()


def get_job_certificates(job_name: str) -> List[str]:
    conn = get_db()
    try:
        row = conn.execute("SELECT certificates FROM job_profile WHERE job_name = ?", (job_name,)).fetchone()
        if not row or not row["certificates"]:
            return []
        return json.loads(row["certificates"])
    except Exception:
        return []
    finally:
        conn.close()


def get_job_soft_abilities(job_name: str) -> Dict[str, Any]:
    conn = get_db()
    try:
        row = conn.execute("SELECT soft_abilities FROM job_profile WHERE job_name = ?", (job_name,)).fetchone()
        if not row or not row["soft_abilities"]:
            return {}
        return json.loads(row["soft_abilities"])
    except Exception:
        return {}
    finally:
        conn.close()


def get_all_job_names() -> List[str]:
    conn = get_db()
    try:
        rows = conn.execute("SELECT DISTINCT job_name FROM job ORDER BY job_name").fetchall()
        return [row["job_name"] for row in rows]
    finally:
        conn.close()


def get_jobs_with_profile() -> List[str]:
    conn = get_db()
    try:
        rows = conn.execute("SELECT job_name FROM job_profile ORDER BY job_name").fetchall()
        return [row["job_name"] for row in rows]
    finally:
        conn.close()

