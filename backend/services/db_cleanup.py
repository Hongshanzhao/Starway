from typing import Dict, List

from db import get_db


CORE_TABLES = {
    "jobs", "candidates", "applications",
    "job", "student", "users",
    "job_relations",
    "assessment_questions", "assessment_results",
    "match_history", "report_history", "reports",
    "content", "user_profiles", "user_browse_history",
    "verification_codes",
}

PURGE_DATA_TABLES = {
    "assessment_results",
    "match_history",
    "report_history",
    "job_profile",
    "job_relations",
}

DROP_TABLES = {
    "job_categories",
}

# Historical modules no longer used by the current Starway backend flow.
LEGACY_UNUSED_TABLES = {
    "interests",
    "user_interests",
    "ability_dimensions",
    "ability_assessments",
    "user_plans",
    "plan_stages",
    "plan_goals",
    "plan_milestones",
    "path_types",
    "path_stage_templates",
    "learning_resources",
    "mentors",
    "practices",
    "job_tags",
}


def list_tables() -> List[str]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [row["name"] for row in rows]
    finally:
        conn.close()


def cleanup_unused_tables(apply: bool = False, purge_data: bool = False) -> Dict[str, List[str]]:
    existing = set(list_tables())
    candidates = sorted(existing & (LEGACY_UNUSED_TABLES | DROP_TABLES))
    purge_candidates = sorted(existing & PURGE_DATA_TABLES) if purge_data else []
    protected = sorted(existing - set(candidates))
    dropped = []
    purged = []
    if apply and (candidates or purge_candidates):
        conn = get_db()
        try:
            cursor = conn.cursor()
            for table in purge_candidates:
                cursor.execute(f"DELETE FROM {table}")
                purged.append(table)
            for table in candidates:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                dropped.append(table)
            conn.commit()
        finally:
            conn.close()
    return {
        "candidates": candidates,
        "dropped": dropped,
        "purge_candidates": purge_candidates,
        "purged": purged,
        "protected": protected,
    }
