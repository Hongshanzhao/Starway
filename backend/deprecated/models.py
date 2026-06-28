"""
数据库实体类与字段说明（dataclasses 形式，便于前后端对接）

包含实体：User, Student, Job, JobProfile, MatchHistory, ReportHistory, AdminLog

说明：项目当前使用原生 sqlite3 操作，以下实体类用于文档与快速序列化/反序列化，
也可在未来替换为 SQLAlchemy ORM 映射类。
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class User:
    id: Optional[int] = None
    username: str = ''        # 登录名（唯一）
    phone: Optional[str] = None
    password_hash: str = ''   # 密码哈希
    role: str = 'user'        # user | admin
    is_active: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Student:
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: Optional[str] = None
    major: Optional[str] = None
    grade: Optional[str] = None
    skills: List[str] = field(default_factory=list)        # 技能列表
    certificates: List[str] = field(default_factory=list)  # 证书列表
    internships: Optional[str] = None
    interests: List[str] = field(default_factory=list)
    completeness: Optional[int] = None
    competitiveness: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class Job:
    id: Optional[int] = None
    job_name: str = ''
    company: Optional[str] = None
    industry: Optional[str] = None
    salary_range: Optional[str] = None
    job_description: Optional[str] = None
    company_info: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class JobProfile:
    id: Optional[int] = None
    job_name: str = ''
    skills: List[str] = field(default_factory=list)
    certificates: List[str] = field(default_factory=list)
    soft_abilities: Dict[str, int] = field(default_factory=dict)  # 例如 {'communication':80}
    created_at: Optional[str] = None


@dataclass
class MatchHistory:
    id: Optional[int] = None
    student_id: Optional[int] = None
    job_name: str = ''
    match_score: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None


@dataclass
class ReportHistory:
    id: Optional[int] = None
    student_id: Optional[int] = None
    job_name: Optional[str] = None
    content: Optional[str] = None
    format_type: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class AdminLog:
    id: Optional[int] = None
    admin_id: Optional[int] = None
    action: str = ''
    target: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[str] = None
