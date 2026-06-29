-- Starway current backend schema reference.
-- Runtime initialization is implemented in db.py and services/data_importer.py.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1,
    avatar TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    completeness INTEGER,
    competitiveness INTEGER,
    phone TEXT,
    email TEXT,
    education_text TEXT,
    work_text TEXT,
    project_text TEXT,
    skills_certs_text TEXT,
    summary TEXT,
    soft_abilities TEXT,
    education_json TEXT,
    work_json TEXT,
    project_json TEXT,
    interest_scores TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE,
    job_title TEXT,
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
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT UNIQUE,
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
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT UNIQUE,
    job_id TEXT,
    candidate_id TEXT,
    application_date TEXT,
    skill_match_score REAL,
    salary_match_score REAL,
    education_match_score REAL,
    experience_match_score REAL,
    total_match_score REAL,
    is_matched INTEGER,
    status TEXT
);

CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    location TEXT,
    salary_range TEXT,
    company TEXT,
    industry TEXT,
    company_size TEXT,
    company_type TEXT,
    job_code TEXT,
    job_description TEXT,
    updated_at TEXT,
    company_info TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT UNIQUE,
    skills TEXT,
    certificates TEXT,
    soft_abilities TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_job TEXT,
    to_job TEXT,
    relation_type TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS assessment_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    dimension TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS assessment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_id TEXT,
    dimension_scores TEXT,
    recommendation TEXT,
    raw_answers TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS match_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    job_name TEXT,
    match_score REAL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES student(id)
);

CREATE TABLE IF NOT EXISTS report_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    job_name TEXT,
    content TEXT,
    format_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES student(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    img_url TEXT,
    stage TEXT,
    type TEXT,
    category TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_browse_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_type TEXT,
    item_id INTEGER,
    title TEXT,
    description TEXT,
    cover TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
