from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from db import get_db


JOB_SELECT = """
    rowid AS id,
    job_id AS job_code,
    job_title AS job_name,
    job_title,
    job_category AS industry,
    job_category,
    company_name AS company,
    company_name,
    company_size,
    company_type,
    city AS location,
    city,
    education,
    experience,
    salary_min,
    salary_max,
    salary_avg,
    salary_min AS _salary_min,
    salary_max AS _salary_max,
    skills,
    TRIM(COALESCE(job_description, '') || CASE
        WHEN requirements IS NOT NULL AND requirements != '' THEN char(10) || requirements
        ELSE ''
    END) AS job_description,
    requirements,
    publish_date AS updated_at,
    publish_date,
    views,
    applications,
    company_name AS company_info,
    job_id AS source_url
"""


def format_salary(value) -> str:
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


def normalize_job(row: Dict) -> Dict:
    result = dict(row)
    salary_min = format_salary(result.pop("_salary_min", result.get("salary_min")))
    salary_max = format_salary(result.pop("_salary_max", result.get("salary_max")))
    salary_avg = format_salary(result.get("salary_avg"))
    if salary_min and salary_max:
        result["salary_range"] = f"{salary_min}-{salary_max}"
    elif salary_avg:
        result["salary_range"] = salary_avg
    else:
        result["salary_range"] = ""
    return result


def row_to_dict(row) -> Optional[Dict]:
    return normalize_job(dict(row)) if row else None


def _quality_score(row: Dict) -> int:
    score = 0
    if str(row.get("skills") or "").strip():
        score += 34
    if int(row.get("description_len") or 0) > 30:
        score += 33
    if int(row.get("requirements_len") or 0) > 20:
        score += 33
    return score


def clear_cache():
    _cached_all_jobs.cache_clear()
    _cached_list_job_names.cache_clear()
    _cached_list_industries.cache_clear()
    try:
        from routes import job as job_route

        if hasattr(job_route, "clear_job_feature_cache"):
            job_route.clear_job_feature_cache()
    except Exception:
        pass


def get_job_by_rowid(rowid: int) -> Optional[Dict]:
    conn = get_db()
    try:
        row = conn.execute(f"SELECT {JOB_SELECT} FROM jobs WHERE rowid = ?", (rowid,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_job_by_name(job_name: str, fuzzy: bool = False) -> Optional[Dict]:
    conn = get_db()
    try:
        if fuzzy:
            row = conn.execute(
                f"SELECT {JOB_SELECT} FROM jobs WHERE LOWER(job_title) LIKE LOWER(?) LIMIT 1",
                (f"%{job_name}%",),
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT {JOB_SELECT} FROM jobs WHERE LOWER(job_title) = LOWER(?) LIMIT 1",
                (job_name,),
            ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def normalize_job_name(job_name: str) -> str:
    row = get_job_by_name(job_name) or get_job_by_name(job_name, fuzzy=True)
    return row["job_name"] if row else job_name


def list_job_names() -> List[str]:
    return list(_cached_list_job_names())


@lru_cache(maxsize=1)
def _cached_list_job_names() -> Tuple[str, ...]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT job_title FROM jobs WHERE job_title IS NOT NULL AND job_title != '' ORDER BY job_title"
        ).fetchall()
        return tuple(row["job_title"] for row in rows)
    finally:
        conn.close()


def list_industries() -> List[str]:
    return list(_cached_list_industries())


@lru_cache(maxsize=1)
def _cached_list_industries() -> Tuple[str, ...]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT job_category FROM jobs WHERE job_category IS NOT NULL AND job_category != '' ORDER BY job_category"
        ).fetchall()
        return tuple(row["job_category"] for row in rows)
    finally:
        conn.close()


GROUP_KEYWORDS = {
    "tech": {"industries": ["技术"], "keywords": []},
    "product": {"industries": ["产品"], "keywords": []},
    "data": {
        "industries": ["技术"],
        "title_keywords": ["数据", "分析", "算法", "机器学习", "深度学习", "BI", "大数据"],
        "keywords": ["数据", "分析", "算法", "机器学习", "深度学习", "BI", "Python", "SQL", "Pandas", "NumPy", "TensorFlow", "PyTorch", "大数据"],
    },
    "operation": {"industries": ["运营"], "keywords": []},
    "business": {"industries": ["市场"], "keywords": ["商务", "销售", "市场", "客户", "渠道"]},
}


def search_jobs(keyword: str = "", industry: str = "", company_size: str = "",
                page: int = 1, size: int = 10, order: str = "asc", group: str = "") -> Tuple[int, List[Dict]]:
    conditions = []
    params = []
    if keyword:
        conditions.append("(job_title LIKE ? OR company_name LIKE ? OR job_description LIKE ? OR requirements LIKE ? OR skills LIKE ?)")
        params.extend([f"%{keyword}%"] * 5)
    if industry:
        conditions.append("job_category = ?")
        params.append(industry)
    group_rule = GROUP_KEYWORDS.get(str(group or "").lower())
    if group_rule:
        group_conditions = []
        industries = group_rule.get("industries") or []
        if industries:
            placeholders = ", ".join(["?"] * len(industries))
            group_conditions.append(f"job_category IN ({placeholders})")
            params.extend(industries)
        title_keywords = group_rule.get("title_keywords") or []
        keywords = group_rule.get("keywords") or []
        if keywords:
            keyword_parts = []
            for item in title_keywords:
                keyword_parts.append("job_title LIKE ?")
                params.append(f"%{item}%")
            for item in keywords:
                keyword_parts.append("(job_title LIKE ? OR skills LIKE ?)")
                params.extend([f"%{item}%"] * 2)
            group_conditions.append("(" + " OR ".join(keyword_parts) + ")")
        if group_conditions:
            conditions.append("(" + " AND ".join(group_conditions) + ")")
    if company_size:
        conditions.append("company_size = ?")
        params.append(company_size)
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    order_sql = "ASC" if str(order).lower() == "asc" else "DESC"
    order_clause = f"rowid {order_sql}"
    if str(group or "").lower() == "data":
        order_clause = f"""
            CASE
                WHEN job_title LIKE '%数据%' OR job_title LIKE '%分析%' OR job_title LIKE '%算法%'
                  OR job_title LIKE '%机器学习%' OR job_title LIKE '%深度学习%' OR job_title LIKE '%BI%'
                  OR job_title LIKE '%大数据%' THEN 0
                ELSE 1
            END ASC,
            rowid {order_sql}
        """
    offset = (page - 1) * size

    conn = get_db()
    try:
        total = conn.execute(f"SELECT COUNT(*) AS total FROM jobs {where_clause}", params).fetchone()["total"]
        rows = conn.execute(
            f"""
            SELECT {JOB_SELECT}
            FROM jobs {where_clause}
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
            """,
            params + [size, offset],
        ).fetchall()
        return total, [normalize_job(dict(row)) for row in rows]
    finally:
        conn.close()


def admin_list_jobs(keyword: str = "", industry: str = "", city: str = "",
                    page: int = 1, size: int = 20) -> Tuple[int, List[Dict]]:
    conditions = []
    params = []
    keyword = str(keyword or "").strip()
    if keyword:
        conditions.append("(job_title LIKE ? OR company_name LIKE ? OR job_category LIKE ? OR city LIKE ? OR skills LIKE ?)")
        params.extend([f"%{keyword}%"] * 5)
    if industry:
        conditions.append("job_category = ?")
        params.append(industry)
    if city:
        conditions.append("city = ?")
        params.append(city)

    page = max(int(page or 1), 1)
    size = min(max(int(size or 20), 1), 100)
    offset = (page - 1) * size
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    conn = get_db()
    try:
        total = conn.execute(f"SELECT COUNT(*) AS total FROM jobs {where_clause}", params).fetchone()["total"]
        rows = conn.execute(
            f"""
            SELECT
              rowid AS id,
              job_id AS job_code,
              job_title AS job_name,
              job_title,
              job_category AS industry,
              job_category,
              company_name AS company,
              company_name,
              city AS location,
              city,
              company_size,
              company_type,
              salary_min,
              salary_max,
              salary_avg,
              salary_min AS _salary_min,
              salary_max AS _salary_max,
              skills,
              SUBSTR(COALESCE(job_description, ''), 1, 180) AS job_description,
              SUBSTR(COALESCE(requirements, ''), 1, 180) AS requirements,
              LENGTH(COALESCE(job_description, '')) AS description_len,
              LENGTH(COALESCE(requirements, '')) AS requirements_len,
              publish_date AS updated_at,
              publish_date
            FROM jobs {where_clause}
            ORDER BY rowid DESC
            LIMIT ? OFFSET ?
            """,
            params + [size, offset],
        ).fetchall()
        result = []
        for row in rows:
            item = normalize_job(dict(row))
            item["quality_score"] = _quality_score(item)
            result.append(item)
        return total, result
    finally:
        conn.close()


def all_jobs(limit: Optional[int] = None) -> List[Dict]:
    if limit is None:
        return [dict(row) for row in _cached_all_jobs()]
    sql = f"SELECT {JOB_SELECT} FROM jobs ORDER BY rowid"
    params: List = []
    sql += " LIMIT ?"
    params.append(limit)
    conn = get_db()
    try:
        return [normalize_job(dict(row)) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


@lru_cache(maxsize=1)
def _cached_all_jobs() -> Tuple[Tuple[Tuple[str, object], ...], ...]:
    conn = get_db()
    try:
        rows = [normalize_job(dict(row)) for row in conn.execute(f"SELECT {JOB_SELECT} FROM jobs ORDER BY rowid").fetchall()]
        return tuple(tuple(row.items()) for row in rows)
    finally:
        conn.close()


def jobs_by_category(category: str, exclude_name: str = "") -> List[Dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            f"""
            SELECT {JOB_SELECT}
            FROM jobs
            WHERE job_category = ? AND job_title != ?
            """,
            (category, exclude_name),
        ).fetchall()
        return [normalize_job(dict(row)) for row in rows]
    finally:
        conn.close()


def jobs_except(job_name: str) -> List[Dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            f"SELECT {JOB_SELECT} FROM jobs WHERE job_title != ?",
            (job_name,),
        ).fetchall()
        return [normalize_job(dict(row)) for row in rows]
    finally:
        conn.close()


def rows_to_similarity_input(rows: Sequence[Dict]) -> List[Dict]:
    return [
        {
            "id": row["id"],
            "job_id": row["id"],
            "job_name": row["job_name"],
            "industry": row.get("industry") or "",
            "salary_range": row.get("salary_range") or "",
            "job_description": row.get("job_description") or "",
        }
        for row in rows
    ]
