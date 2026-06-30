import os
import sqlite3
from typing import Iterable

from config import SQLITE_DB_PATH, UPLOAD_FOLDER


def get_db():
    db_dir = os.path.dirname(SQLITE_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _table_columns(cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row["name"] for row in cursor.fetchall()}


def _add_missing_columns(cursor, table: str, columns: Iterable[tuple[str, str]]):
    existing = _table_columns(cursor, table)
    for name, column_type in columns:
        if name not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {column_type}")


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    from services.data_importer import ensure_core_tables

    ensure_core_tables(conn)
    _create_business_tables(cursor)
    _migrate_business_tables(cursor)
    _drop_removed_tables(cursor)

    conn.commit()
    conn.close()

    try:
        from services import job_repository

        job_repository.clear_cache()
    except Exception:
        pass

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, "avatars"), exist_ok=True)
    print("数据库初始化完成，文件位置：", SQLITE_DB_PATH)


def _create_business_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            major TEXT,
            grade TEXT,
            skills TEXT,
            certificates TEXT,
            internships TEXT,
            interests TEXT,
            completeness INTEGER DEFAULT 0,
            competitiveness INTEGER DEFAULT 0,
            phone TEXT,
            email TEXT,
            education_text TEXT,
            work_text TEXT,
            project_text TEXT,
            skills_certs_text TEXT,
            summary TEXT,
            soft_abilities TEXT,
            interest_scores TEXT,
            education_json TEXT,
            work_json TEXT,
            project_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT UNIQUE,
            skills TEXT,
            certificates TEXT,
            soft_abilities TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            job_name TEXT,
            match_score REAL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            job_name TEXT,
            content TEXT,
            format_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            dimension TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT DEFAULT 'guest',
            dimension_scores TEXT NOT NULL,
            recommendation TEXT,
            raw_answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS captcha_challenges (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL,
            expires_at REAL NOT NULL,
            used_at REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            type TEXT,
            format TEXT,
            content TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            img_url TEXT,
            stage TEXT,
            type TEXT,
            category TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            name TEXT,
            gender TEXT,
            grade TEXT,
            major TEXT,
            target TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_browse_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER,
            title TEXT,
            cover TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_job TEXT NOT NULL,
            to_job TEXT NOT NULL,
            relation_type TEXT CHECK(relation_type IN ('promotion', 'transition')),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _migrate_business_tables(cursor):
    _add_missing_columns(cursor, "users", [
        ("phone", "TEXT"),
        ("role", "TEXT DEFAULT 'user'"),
        ("is_active", "INTEGER DEFAULT 1"),
        ("avatar", "TEXT"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ])
    _add_missing_columns(cursor, "student", [
        ("user_id", "INTEGER"),
        ("phone", "TEXT"),
        ("email", "TEXT"),
        ("education_text", "TEXT"),
        ("work_text", "TEXT"),
        ("project_text", "TEXT"),
        ("skills_certs_text", "TEXT"),
        ("summary", "TEXT"),
        ("soft_abilities", "TEXT"),
        ("interest_scores", "TEXT"),
        ("education_json", "TEXT"),
        ("work_json", "TEXT"),
        ("project_json", "TEXT"),
    ])
    if _table_exists(cursor, "job"):
        _add_missing_columns(cursor, "job", [
            ("company_size", "TEXT"),
            ("company_type", "TEXT"),
            ("job_code", "TEXT"),
            ("updated_at", "TEXT"),
            ("source_url", "TEXT"),
        ])
        _remove_legacy_job_category_id(cursor)


def _table_exists(cursor, table: str) -> bool:
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _remove_legacy_job_category_id(cursor):
    legacy_columns = _table_columns(cursor, "job")
    if "category_id" not in legacy_columns:
        return
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.execute("ALTER TABLE job RENAME TO job_legacy_with_category")
    cursor.execute("""
        CREATE TABLE job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            company TEXT,
            industry TEXT,
            salary_range TEXT,
            job_description TEXT,
            company_info TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            company_size TEXT,
            company_type TEXT,
            job_code TEXT,
            updated_at TEXT,
            source_url TEXT
        )
    """)
    target_columns = [
        "id", "job_name", "company", "industry", "salary_range",
        "job_description", "company_info", "location", "created_at",
        "company_size", "company_type", "job_code", "updated_at", "source_url",
    ]
    select_exprs = []
    for column in target_columns:
        if column in legacy_columns:
            select_exprs.append(column)
        elif column == "job_name":
            select_exprs.append("'未命名岗位'")
        else:
            select_exprs.append("NULL")
    cursor.execute(f"""
        INSERT INTO job ({', '.join(target_columns)})
        SELECT {', '.join(select_exprs)}
        FROM job_legacy_with_category
    """)
    cursor.execute("DROP TABLE job_legacy_with_category")
    cursor.execute("PRAGMA foreign_keys = ON")


def _drop_removed_tables(cursor):
    try:
        from services.db_cleanup import DROP_TABLES, LEGACY_UNUSED_TABLES

        for table in sorted(LEGACY_UNUSED_TABLES | DROP_TABLES):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
    except Exception as exc:
        print(f"legacy table cleanup skipped: {exc}")
