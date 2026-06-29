import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List

from db import get_db


JOB_COLUMNS = [
    "job_id", "job_title", "job_category", "company_name", "company_size",
    "company_type", "city", "education", "experience", "salary_min",
    "salary_max", "salary_avg", "skills", "job_description", "requirements",
    "publish_date", "views", "applications",
]

CANDIDATE_COLUMNS = [
    "candidate_id", "name", "age", "gender", "education", "experience",
    "current_city", "preferred_cities", "preferred_categories", "skills",
    "expected_salary_min", "expected_salary_max", "expected_salary_avg",
    "self_introduction", "registration_date",
]

APPLICATION_COLUMNS = [
    "application_id", "job_id", "candidate_id", "application_date",
    "skill_match_score", "salary_match_score", "education_match_score",
    "experience_match_score", "total_match_score", "is_matched", "status",
]


def _read_csv(path: Path) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"missing data file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _ensure_columns(cursor, table: str, columns: Iterable[str]):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row["name"] for row in cursor.fetchall()}
    for column in columns:
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")


def ensure_core_tables(conn=None):
    own_conn = conn is None
    conn = conn or get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            job_category TEXT,
            company_name TEXT,
            company_size TEXT,
            company_type TEXT,
            city TEXT,
            education TEXT,
            experience TEXT,
            salary_min REAL,
            salary_max REAL,
            salary_avg REAL,
            skills TEXT,
            job_description TEXT,
            requirements TEXT,
            publish_date TEXT,
            views INTEGER,
            applications INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            education TEXT,
            experience TEXT,
            current_city TEXT,
            preferred_cities TEXT,
            preferred_categories TEXT,
            skills TEXT,
            expected_salary_min REAL,
            expected_salary_max REAL,
            expected_salary_avg REAL,
            self_introduction TEXT,
            registration_date TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            application_date TEXT,
            skill_match_score REAL,
            salary_match_score REAL,
            education_match_score REAL,
            experience_match_score REAL,
            total_match_score REAL,
            is_matched INTEGER,
            status TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(job_id),
            FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
        )
    """)
    if own_conn:
        conn.commit()
        conn.close()


def _replace_rows(cursor, table: str, columns: List[str], rows: List[dict]):
    if not rows:
        return 0
    placeholders = ",".join("?" for _ in columns)
    sql = f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    values = [[row.get(col, "") for col in columns] for row in rows]
    cursor.executemany(sql, values)
    return len(values)


def import_tianchi_dataset(data_dir: str = None, reset: bool = False) -> Dict[str, int]:
    data_root = Path(data_dir or os.getenv("TIANCHI_DATA_DIR", r"D:\caogao6\岗位数据"))
    jobs = _read_csv(data_root / "jobs.csv")
    candidates = _read_csv(data_root / "candidates.csv")
    applications = _read_csv(data_root / "applications.csv")

    conn = get_db()
    try:
        ensure_core_tables(conn)
        cursor = conn.cursor()
        if reset:
            cursor.execute("DELETE FROM applications")
            cursor.execute("DELETE FROM candidates")
            cursor.execute("DELETE FROM jobs")
        job_count = _replace_rows(cursor, "jobs", JOB_COLUMNS, jobs)
        candidate_count = _replace_rows(cursor, "candidates", CANDIDATE_COLUMNS, candidates)
        application_count = _replace_rows(cursor, "applications", APPLICATION_COLUMNS, applications)
        conn.commit()
        try:
            from services import job_repository

            job_repository.clear_cache()
        except Exception:
            pass
        return {
            "jobs": job_count,
            "candidates": candidate_count,
            "applications": application_count,
        }
    finally:
        conn.close()
