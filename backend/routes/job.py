import json
import re
from functools import lru_cache

from flask import Blueprint, jsonify, request

from db import get_db
from services import job_ml_service, job_repository
from services.ml_recommender import build_job_profile as build_ml_job_profile
from services.skill_normalizer import concepts_from_skills, display_concepts, match_concepts


job_bp = Blueprint("job", __name__, url_prefix="/api/jobs")


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _load_student_profile(student_id):
    if not student_id:
        return None
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM student WHERE id = ?", (student_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    data = dict(row)
    for key, default in [
        ("skills", []),
        ("certificates", []),
        ("soft_abilities", {}),
        ("education_json", {}),
        ("work_json", []),
        ("project_json", []),
    ]:
        data[key] = _json_loads(data.get(key), default)
    return data


def _tokens(value):
    text = str(value or "")
    return {
        item.strip().lower()
        for item in re.split(r"[,，、\s;/|]+", text)
        if len(item.strip()) > 1
    }


def _display_skills(value):
    if isinstance(value, (list, tuple, set)):
        raw = list(value)
    else:
        raw = re.split(r"[,，、\s;/|]+", str(value or ""))
    seen = set()
    result = []
    for item in raw:
        skill = str(item).strip()
        if not skill:
            continue
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            result.append(skill)
    return result


def _job_tokens(row):
    return set(_job_features(row)["tokens"])


def _salary_midpoint(value):
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", str(value or ""))]
    if not numbers:
        return 0.0
    if len(numbers) == 1:
        return numbers[0]
    return (numbers[0] + numbers[1]) / 2


def _row_signature(row):
    return (
        row.get("id"),
        row.get("job_name") or "",
        row.get("industry") or "",
        row.get("job_category") or "",
        row.get("skills") or "",
        row.get("job_description") or "",
        row.get("requirements") or "",
        row.get("salary_range") or "",
    )


def clear_job_feature_cache():
    _cached_job_features.cache_clear()


def _role_family_from_text(text, industry=""):
    best_family = "general"
    best_score = 0
    for family, rule in ROLE_FAMILIES.items():
        score = sum(1 for word in rule["positive"] if word.lower() in text)
        if score > best_score:
            best_family = family
            best_score = score
    if best_family == "general" and industry:
        industry_text = str(industry).lower()
        for family, rule in ROLE_FAMILIES.items():
            if any(word.lower() in industry_text for word in rule["positive"]):
                return family
    return best_family


@lru_cache(maxsize=20000)
def _cached_job_features(signature):
    row = {
        "id": signature[0],
        "job_name": signature[1],
        "industry": signature[2],
        "job_category": signature[3],
        "skills": signature[4],
        "job_description": signature[5],
        "requirements": signature[6],
        "salary_range": signature[7],
    }
    text = " ".join([
        str(row.get("job_name", "")),
        str(row.get("industry", "")),
        str(row.get("skills", "")),
        str(row.get("job_description", "")),
        str(row.get("requirements", "")),
    ]).lower()
    required_skills = _job_required_skills_uncached(row)
    concepts = concepts_from_skills(required_skills, extra_text=row.get("job_description", ""))
    return {
        "role_key": re.sub(r"[\s\-_/|·,，、;；:：()（）]+", "", str(row.get("job_name") or "").lower()),
        "job_text": text,
        "tokens": frozenset(_tokens(text)),
        "salary_midpoint": _salary_midpoint(row.get("salary_range", "")),
        "required_skills": tuple(required_skills),
        "concepts": frozenset(concepts),
        "role_family": _role_family_from_text(text, row.get("industry")),
    }


def _job_features(row):
    return _cached_job_features(_row_signature(row))


def _similarity_score(source, target):
    source_tokens = _job_tokens(source)
    target_tokens = _job_tokens(target)
    union = source_tokens | target_tokens
    skill_score = len(source_tokens & target_tokens) / len(union) if union else 0.0
    industry_score = 1.0 if source.get("industry") and source.get("industry") == target.get("industry") else 0.0

    source_salary = _job_features(source)["salary_midpoint"]
    target_salary = _job_features(target)["salary_midpoint"]
    if source_salary and target_salary:
        salary_score = 1 - min(abs(source_salary - target_salary) / max(source_salary, target_salary), 1)
    else:
        salary_score = 0.5

    return round(0.65 * skill_score + 0.25 * industry_score + 0.10 * salary_score, 4)


ROLE_FAMILIES = {
    "tech_backend": {
        "positive": [
            "java", "python", "go", "后端", "后台", "服务端", "开发工程师", "软件开发",
            "软件工程", "架构", "微服务", "spring", "flask", "django", "api",
        ],
        "adjacent": [
            "tech_backend", "tech_test", "tech_data", "tech_ops", "tech_frontend", "tech_product",
        ],
    },
    "tech_frontend": {
        "positive": ["前端", "web", "vue", "react", "javascript", "typescript", "小程序", "h5"],
        "adjacent": ["tech_frontend", "tech_backend", "tech_test", "tech_product"],
    },
    "tech_test": {
        "positive": ["测试", "质量", "qa", "自动化", "测开", "测试开发"],
        "adjacent": ["tech_test", "tech_backend", "tech_frontend", "tech_ops"],
    },
    "tech_data": {
        "positive": ["数据开发", "大数据", "数据分析", "数据挖掘", "算法", "机器学习", "深度学习", "spark", "flink", "sql"],
        "adjacent": ["tech_data", "tech_backend", "tech_product", "tech_ops"],
    },
    "tech_ops": {
        "positive": ["运维", "devops", "sre", "云计算", "linux", "部署", "平台工程"],
        "adjacent": ["tech_ops", "tech_backend", "tech_test", "tech_data"],
    },
    "tech_product": {
        "positive": ["产品经理", "产品专员", "需求分析", "项目经理", "技术产品"],
        "adjacent": ["tech_product", "tech_backend", "tech_data", "tech_frontend"],
    },
    "business_market": {
        "positive": ["市场", "营销", "品牌", "推广", "销售", "商务", "渠道"],
        "adjacent": ["business_market", "business_ops", "tech_product"],
    },
    "business_finance": {
        "positive": ["会计", "财务", "审计", "税务", "出纳", "成本"],
        "adjacent": ["business_finance", "business_ops"],
    },
    "business_ops": {
        "positive": ["运营", "客服", "行政", "人事", "hr", "内容运营", "用户运营"],
        "adjacent": ["business_ops", "business_market", "tech_product"],
    },
}

HARD_NEGATIVE_BY_FAMILY = {
    "tech_backend": ["市场", "营销", "销售", "会计", "财务", "审计", "出纳", "行政", "人事", "客服"],
    "tech_frontend": ["市场", "营销", "销售", "会计", "财务", "审计", "出纳", "行政", "人事", "客服"],
    "tech_test": ["市场", "营销", "销售", "会计", "财务", "审计", "出纳", "行政", "人事", "客服"],
    "tech_data": ["销售", "会计", "财务", "审计", "出纳", "行政", "人事", "客服"],
    "tech_ops": ["市场", "营销", "销售", "会计", "财务", "审计", "出纳", "行政", "人事", "客服"],
}

PROMOTION_LEVEL_KEYWORDS = [
    "总监", "经理", "负责人", "主管", "架构师", "专家", "leader", "lead",
    "manager", "director", "architect", "principal", "staff", "senior",
]


def _job_text(row):
    return _job_features(row)["job_text"]


def _role_family(row):
    return _job_features(row)["role_family"]


def _family_compatible(source, target):
    source_family = _role_family(source)
    target_family = _role_family(target)
    if source_family == "general" or target_family == "general":
        return source.get("industry") == target.get("industry")
    if any(word in _job_text(target) for word in HARD_NEGATIVE_BY_FAMILY.get(source_family, [])):
        return False
    return target_family in ROLE_FAMILIES.get(source_family, {}).get("adjacent", [source_family])


def _is_promotion_level_role(row):
    name = str(row.get("job_name", "")).lower()
    return any(keyword.lower() in name for keyword in PROMOTION_LEVEL_KEYWORDS)


def _lateral_score(source, target, vector_score=None):
    family_score = 1.0 if _family_compatible(source, target) else 0.0
    base_score = _similarity_score(source, target)
    vector = vector_score if vector_score is not None else 0.0
    same_industry = 1.0 if source.get("industry") == target.get("industry") else 0.0
    return round(0.45 * family_score + 0.30 * base_score + 0.15 * same_industry + 0.10 * vector, 4)


def _lateral_description(source, target, model_source):
    source_family = _role_family(source)
    target_family = _role_family(target)
    if source_family == target_family:
        return "同属相邻技术岗位，核心编程、工程实践和项目经验可直接迁移，适合作为横向发展方向。"
    if target_family == "tech_test":
        return "保留编码能力，同时补充自动化测试、接口测试和质量保障体系，转型路径清晰。"
    if target_family == "tech_data":
        return "可基于编程和 SQL 能力延伸到数据处理、数据平台或大数据开发方向。"
    if target_family == "tech_ops":
        return "可从后端开发延伸到部署、监控、云平台和 DevOps 工程能力。"
    if target_family == "tech_product":
        return "适合在保留技术理解的基础上补齐需求分析、产品设计和项目推进能力。"
    if model_source == "hybrid_word2vec":
        return "由职业族边界、技能重合度和 Word2Vec 相似度共同筛选，属于可解释的相邻转岗方向。"
    return "由职业族边界和技能重合度筛选，属于更贴近当前能力结构的横向转岗方向。"


@job_bp.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT job_category AS name, COUNT(*) AS job_count
            FROM jobs
            WHERE job_category IS NOT NULL AND job_category != ''
            GROUP BY job_category
            ORDER BY job_category
            """
        ).fetchall()
    finally:
        conn.close()
    return jsonify([
        {
            "id": index + 1,
            "name": row["name"],
            "icon": "",
            "description": f"{row['name']}类岗位，共 {row['job_count']} 个",
            "job_count": row["job_count"],
            "skills": [],
            "certificates": [],
            "soft_abilities": {},
        }
        for index, row in enumerate(rows)
    ])


@job_bp.route("/<int:job_id>", methods=["GET"])
def get_job_detail(job_id):
    row = job_repository.get_job_by_rowid(job_id)
    if not row:
        return jsonify({"error": "岗位不存在"}), 404
    return jsonify(row)


@job_bp.route("/profile/<path:job_name>", methods=["GET"])
def get_job_profile_by_name(job_name):
    row = job_repository.get_job_by_name(job_name)
    if not row:
        return jsonify({"error": "岗位不存在"}), 404
    return jsonify(row)


@job_bp.route("/graph", methods=["GET"])
def get_job_graph():
    conn = get_db()
    try:
        rows = conn.execute("SELECT from_job, to_job, relation_type, description FROM job_relations").fetchall()
    finally:
        conn.close()
    nodes = sorted({row["from_job"] for row in rows} | {row["to_job"] for row in rows})
    return jsonify({
        "nodes": [{"id": name, "label": name} for name in nodes],
        "edges": [dict(row) for row in rows],
    })


@job_bp.route("/industries", methods=["GET"])
def get_industries():
    return jsonify(job_repository.list_industries())


@job_bp.route("/search", methods=["GET"])
def search_jobs():
    page = max(1, request.args.get("page", 1, type=int))
    size = max(1, request.args.get("size", 10, type=int))
    keyword = request.args.get("keyword", "", type=str)
    industry = request.args.get("industry", "", type=str)
    company_size = request.args.get("company_size", "", type=str)
    order = request.args.get("order", "asc", type=str)

    total, rows = job_repository.search_jobs(
        keyword=keyword,
        industry=industry,
        company_size=company_size,
        page=page,
        size=size,
        order=order,
    )
    return jsonify({"total": total, "page": page, "size": size, "items": rows})


@job_bp.route("/simple_search", methods=["GET"])
def simple_search():
    keyword = request.args.get("keyword", "", type=str)
    page = max(1, request.args.get("page", 1, type=int))
    size = max(1, request.args.get("size", 10, type=int))
    _, rows = job_repository.search_jobs(keyword=keyword, page=page, size=size)
    return jsonify([
        {
            "id": row["id"],
            "job_name": row["job_name"],
            "company": row["company"],
            "salary_range": row["salary_range"],
            "location": row["location"],
        }
        for row in rows
    ])


@job_bp.route("/<int:job_id>/profile", methods=["GET"])
def get_job_profile(job_id):
    job = job_repository.get_job_by_rowid(job_id)
    if not job:
        return jsonify({"error": "岗位不存在"}), 404

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT skills, certificates, soft_abilities FROM job_profile WHERE job_name = ?",
            (job["job_name"],),
        ).fetchone()
        if existing:
            profile = {
                "job_id": job["job_code"],
                "job_name": job["job_name"],
                "skills": _json_loads(existing["skills"], []),
                "certificates": _json_loads(existing["certificates"], []),
                "soft_abilities": _json_loads(existing["soft_abilities"], {}),
                "category": job["job_category"] or job["industry"] or "",
                "source": "job_profile",
            }
        else:
            profile = build_ml_job_profile(job)
            conn.execute(
                """
                INSERT OR REPLACE INTO job_profile (job_name, skills, certificates, soft_abilities)
                VALUES (?, ?, ?, ?)
                """,
                (
                    profile["job_name"],
                    json.dumps(profile["skills"], ensure_ascii=False),
                    json.dumps(profile["certificates"], ensure_ascii=False),
                    json.dumps(profile["soft_abilities"], ensure_ascii=False),
                ),
            )
            conn.commit()
    finally:
        conn.close()
    return jsonify(profile)


def _career_path(job_name):
    normalized = job_repository.normalize_job_name(job_name)
    model_source = "rules"
    conn = get_db()
    try:
        stored = conn.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'promotion' ORDER BY id",
            (normalized,),
        ).fetchall()
        if stored:
            current = normalized
            path = []
            for row in stored:
                path.append({"from_job": current, "to_job": row["to_job"], "description": row["description"]})
                current = row["to_job"]
            return path, "job_relations"
    finally:
        conn.close()

    source = job_repository.get_job_by_name(normalized)
    peers = job_repository.jobs_by_category(source["industry"], normalized) if source else []
    word2vec_ranked = job_ml_service.rank_rows_with_word2vec(source["id"], peers) if source else None
    if word2vec_ranked:
        ranked = [item[0] for item in sorted(
            word2vec_ranked,
            key=lambda item: (_salary_midpoint(item[0]["salary_range"]), item[1]),
            reverse=True,
        )]
        model_source = "word2vec"
    else:
        ranked = sorted(
            peers,
            key=lambda row: (_salary_midpoint(row["salary_range"]), _similarity_score(source, row)),
            reverse=True,
        )

    path = []
    current = normalized
    for row in ranked[:2]:
        path.append({
            "from_job": current,
            "to_job": row["job_name"],
            "description": (
                "基于 Word2Vec 岗位向量、同赛道和薪资区间推导的纵向发展方向。"
                if model_source == "word2vec"
                else "基于同赛道、薪资区间和技能丰富度推导的纵向发展方向。"
            ),
        })
        current = row["job_name"]
    return path, model_source


def _job_required_skills_uncached(job):
    explicit = _display_skills(job.get("skills"))
    text_skills = []
    text = " ".join([
        str(job.get("job_name", "")),
        str(job.get("industry", "")),
        str(job.get("skills", "")),
        str(job.get("job_description", "")),
        str(job.get("requirements", "")),
    ]).lower()
    common = [
        "Java", "Spring", "Spring Boot", "Python", "Flask", "Django", "SQL", "MySQL", "Redis", "Linux",
        "Docker", "Kubernetes", "微服务", "API", "接口", "自动化测试", "测试", "Spark",
        "Flink", "大数据", "数据分析", "机器学习", "深度学习", "算法", "Vue", "React",
        "JavaScript", "DevOps",
    ]
    for skill in common:
        if skill.lower() in text or skill in str(job.get("job_description", "")):
            text_skills.append(skill)
    return list(dict.fromkeys(explicit + text_skills))


def _job_required_skills(job):
    return list(_job_features(job)["required_skills"])


def _student_skills(student):
    return _display_skills(student.get("skills") if student else [])


def _skill_sets(student, job):
    student_skills = _student_skills(student)
    required = _job_required_skills(job)
    required_concepts, matched_concepts, missing_concepts = match_concepts(
        student_skills,
        required,
        required_text=job.get("job_description", ""),
    )
    return (
        student_skills,
        display_concepts(required_concepts),
        display_concepts(matched_concepts),
        display_concepts(missing_concepts),
    )


def _learning_plan_for(job, missing_skills):
    family = _role_family(job)
    plan = []
    if missing_skills:
        plan.append("优先补齐 " + "、".join(missing_skills[:3]) + "，用一个小项目验证掌握程度。")
    if family == "tech_test":
        plan.append("完成接口测试和自动化测试练习，整理一份测试用例、缺陷定位和测试报告。")
    elif family == "tech_data":
        plan.append("完成一个 SQL + Spark/Flink 的数据处理项目，沉淀数据建模和任务调度经验。")
    elif family == "tech_ops":
        plan.append("补充 Linux、Docker、部署监控和故障排查流程，形成可展示的上线实践。")
    elif family == "tech_product":
        plan.append("补充需求分析、原型设计和项目推进方法，输出一份产品需求文档。")
    else:
        plan.append("把已有项目改造成目标岗位相关作品，突出工程实践和问题解决过程。")
    plan.append("在简历中量化项目结果，例如性能提升、接口数量、数据规模或缺陷收敛效果。")
    return list(dict.fromkeys(plan))[:3]


def _personalize_path_item(source, target, student, relation_type, model_source):
    _, required, transferable, missing = _skill_sets(student, target)
    skill_score = len(transferable) / len(required) if required else 0.0
    family_score = 1.0 if _family_compatible(source, target) else 0.5
    experience_bonus = 0.1 if (student.get("internships") or student.get("project_json")) else 0.0
    score = round(min((0.70 * skill_score + 0.20 * family_score + experience_bonus) * 100, 100), 1)
    if transferable:
        reason = f"你已有{'、'.join(transferable[:4])}，这些能力可以迁移到{target['job_name']}。"
    else:
        reason = f"{target['job_name']}与当前方向属于相邻职业族，但需要先补齐核心技能。"
    if missing:
        reason += " 主要差距是" + "、".join(missing[:4]) + "。"
    else:
        reason += " 当前技能覆盖度较高，可以优先用项目经历证明胜任度。"
    return {
        "job_name": target["job_name"],
        "to_job": target["job_name"],
        "description": reason,
        "match_score": score,
        "readiness_score": score,
        "why_recommended": reason,
        "transferable_skills": transferable,
        "required_skills": required,
        "missing_skills": missing,
        "learning_plan": _learning_plan_for(target, missing),
        "risk": "缺口技能较多，建议先做项目验证后再投递。" if len(missing) >= 4 else "转岗风险可控，重点是用项目材料证明能力迁移。",
        "model_source": model_source,
        "relation_type": relation_type,
    }


def _profile_fit_score(source, target, student, path_score):
    if not student:
        return path_score
    _, required, transferable, missing = _skill_sets(student, target)
    coverage = len(transferable) / len(required) if required else 0.0
    gap_penalty = min(len(missing) * 0.03, 0.18)
    source_family = _role_family(source)
    target_family = _role_family(target)
    if source_family == target_family:
        family_score = 1.0
    elif _family_compatible(source, target):
        family_score = 0.55
    else:
        family_score = 0.0
    return round(0.62 * coverage + 0.18 * path_score + 0.20 * family_score - gap_penalty, 4)


def _lateral_paths(job_name, student=None):
    normalized = job_repository.normalize_job_name(job_name)
    model_source = "rules"
    conn = get_db()
    try:
        stored = conn.execute(
            "SELECT to_job, description FROM job_relations WHERE from_job = ? AND relation_type = 'transition' ORDER BY id",
            (normalized,),
        ).fetchall()
        if stored:
            return [{"job_name": row["to_job"], "description": row["description"]} for row in stored], "job_relations"
    finally:
        conn.close()

    source = job_repository.get_job_by_name(normalized)
    if not source:
        return [], model_source

    rows = job_repository.jobs_except(normalized)
    candidates = [
        row for row in rows
        if _family_compatible(source, row) and not _is_promotion_level_role(row)
    ]
    if not candidates:
        candidates = [
            row for row in rows
            if row.get("industry") == source.get("industry") and not _is_promotion_level_role(row)
        ]

    word2vec_ranked = job_ml_service.rank_rows_with_word2vec(source["id"], candidates)
    vector_scores = {}
    if word2vec_ranked:
        vector_scores = {row["id"]: score for row, score in word2vec_ranked}
        model_source = "hybrid_word2vec"

    ranked_with_scores = []
    for row in candidates:
        path_score = _lateral_score(source, row, vector_scores.get(row["id"]))
        final_score = _profile_fit_score(source, row, student, path_score)
        ranked_with_scores.append((row, final_score))
    ranked_with_scores.sort(key=lambda item: item[1], reverse=True)

    return [
        _personalize_path_item(source, row, student, "transition", model_source)
        if student else {
            "job_name": row["job_name"],
            "description": _lateral_description(source, row, model_source),
        }
        for row, score in ranked_with_scores[:3]
        if score > 0
    ], model_source


def _personalize_vertical_path(source, path, student, model_source):
    if not source or not student:
        return path
    result = []
    current = source
    for item in path:
        target = job_repository.get_job_by_name(item.get("to_job")) or {
            **current,
            "job_name": item.get("to_job"),
            "job_description": current.get("job_description", ""),
        }
        personalized = _personalize_path_item(current, target, student, "promotion", model_source)
        personalized["from_job"] = item.get("from_job") or current.get("job_name")
        personalized["to_job"] = item.get("to_job")
        personalized["why_next"] = personalized["why_recommended"]
        result.append(personalized)
        current = target
    return result


def _normalized_role_key(row):
    name = row.get("job_name") if isinstance(row, dict) else row
    if isinstance(row, dict):
        return _job_features(row)["role_key"]
    return re.sub(r"[\s\-_/|·,，、;；:：()（）]+", "", str(name or "").lower())


def _job_concepts(job):
    return set(_job_features(job)["concepts"])


def _relation_type_for(source, target):
    if _normalized_role_key(source) == _normalized_role_key(target):
        return "same_role_posting"
    if _family_compatible(source, target):
        return "adjacent_role"
    return "distant_role"


def _career_similarity_components(source, target, vector_score=None):
    source_concepts = _job_concepts(source)
    target_concepts = _job_concepts(target)
    matched = source_concepts & target_concepts
    missing = target_concepts - source_concepts
    skill_score = len(matched) / len(target_concepts) if target_concepts else 0.0

    source_family = _role_family(source)
    target_family = _role_family(target)
    if source_family == target_family and source_family != "general":
        family_score = 1.0
    elif _family_compatible(source, target):
        family_score = 0.72
    elif source.get("industry") and source.get("industry") == target.get("industry"):
        family_score = 0.35
    else:
        family_score = 0.10

    rule_score = _similarity_score(source, target)
    vector = max(0.0, min(float(vector_score or 0), 1.0))
    score = 0.45 * skill_score + 0.25 * family_score + 0.20 * rule_score + 0.10 * vector
    if _normalized_role_key(source) == _normalized_role_key(target):
        score = max(score, 0.86)
    return {
        "score": round(score, 4),
        "required_skills": display_concepts(target_concepts),
        "matched_skills": display_concepts(matched),
        "missing_skills": display_concepts(missing),
        "source_family": source_family,
        "target_family": target_family,
    }


def _career_similarity_score(source, target, relation_type, vector_score=None):
    source_concepts = _job_concepts(source)
    target_concepts = _job_concepts(target)
    matched = source_concepts & target_concepts
    skill_score = len(matched) / len(target_concepts) if target_concepts else 0.0

    source_family = _role_family(source)
    target_family = _role_family(target)
    if source_family == target_family and source_family != "general":
        family_score = 1.0
    elif relation_type == "adjacent_role":
        family_score = 0.72
    elif source.get("industry") and source.get("industry") == target.get("industry"):
        family_score = 0.35
    else:
        family_score = 0.10

    rule_score = _similarity_score(source, target)
    vector = max(0.0, min(float(vector_score or 0), 1.0))
    score = 0.45 * skill_score + 0.25 * family_score + 0.20 * rule_score + 0.10 * vector
    if relation_type == "same_role_posting":
        score = max(score, 0.86)
    return round(score, 4)


def _why_similar(source, target, components, relation_type, model_source):
    matched = components["matched_skills"]
    missing = components["missing_skills"]
    if relation_type == "same_role_posting":
        lead = "为什么推荐：这是同一岗位方向的不同招聘样本，可用于比较城市、薪资、公司要求和技能表述差异。"
    elif relation_type == "adjacent_role":
        lead = f"为什么推荐：{target['job_name']}与{source['job_name']}处在相邻职业方向，能力迁移路径比较清晰。"
    else:
        lead = f"为什么推荐：{target['job_name']}与当前岗位存在部分技能或行业交集，但转向跨度较大，需要谨慎评估。"

    if matched:
        lead += " 可迁移能力包括" + "、".join(matched[:4]) + "。"
    else:
        lead += " 当前公开岗位信息中可直接迁移的技能较少。"
    if missing:
        lead += " 建议补充" + "、".join(missing[:4]) + "。"
    else:
        lead += " 核心技能覆盖较好，可以重点用项目经历证明胜任度。"
    if "word2vec" in model_source:
        lead += " 排序同时参考了 Word2Vec 岗位向量相似度。"
    return lead


def _similar_job_payload(row, similarity, model_source, source=None, vector_score=None):
    relation_type = _relation_type_for(source, row) if source else "similar_posting"
    components = _career_similarity_components(source, row, vector_score) if source else {
        "required_skills": _job_required_skills(row),
        "matched_skills": [],
        "missing_skills": [],
    }
    return {
        "job_id": row["id"],
        "job_code": row.get("job_code") or "",
        "job_name": row.get("job_name") or "",
        "company": row.get("company") or "",
        "job_category": row.get("job_category") or row.get("industry") or "",
        "industry": row.get("industry") or "",
        "salary_range": row.get("salary_range") or "",
        "location": row.get("location") or "",
        "skills": row.get("skills") or "",
        "similarity": round(float(similarity or 0), 4),
        "relation_type": relation_type,
        "required_skills": components["required_skills"],
        "matched_skills": components["matched_skills"],
        "missing_skills": components["missing_skills"],
        "why_similar": (
            _why_similar(source, row, components, relation_type, model_source)
            if source else (
                "Word2Vec 岗位向量相近，可作为机器学习召回的相似岗位候选。"
                if model_source == "word2vec"
                else "岗位类别、技能关键词和薪资区间相近，可作为规则召回的相似岗位候选。"
            )
        ),
    }


def _hydrate_similar_jobs(items, model_source):
    hydrated = []
    for item in items:
        row = None
        raw_name = item.get("job_name")
        if raw_name:
            row = job_repository.get_job_by_name(raw_name) or job_repository.get_job_by_name(raw_name, fuzzy=True)
        if not row:
            row = job_repository.get_job_by_rowid(item.get("job_id"))
        if not row:
            continue
        hydrated.append(_similar_job_payload(row, item.get("similarity", 0), model_source))
    return hydrated


def _hydrate_word2vec_rows(items, rows=None):
    rows = rows if rows is not None else job_repository.all_jobs()
    by_id = {row["id"]: row for row in rows}
    by_name = {}
    for row in rows:
        key = str(row.get("job_name") or "").lower()
        by_name.setdefault(key, row)
    hydrated = []
    for item in items or []:
        row = None
        raw_name = item.get("job_name")
        if raw_name:
            row = by_name.get(str(raw_name).lower())
            if not row:
                raw_lower = str(raw_name).lower()
                row = next((candidate for candidate in rows if raw_lower in str(candidate.get("job_name") or "").lower()), None)
        if not row:
            row = by_id.get(item.get("job_id"))
        if row:
            hydrated.append((row, item.get("similarity", 0)))
    return hydrated


def _is_hard_negative_direction(source, target):
    source_family = _role_family(source)
    target_family = _role_family(target)
    if source_family == "general" or target_family == "general":
        compatible = source.get("industry") == target.get("industry")
    else:
        compatible = target_family in ROLE_FAMILIES.get(source_family, {}).get("adjacent", [source_family])
    if compatible:
        return False
    target_text = _job_text(target)
    if any(word in target_text for word in HARD_NEGATIVE_BY_FAMILY.get(source_family, [])):
        return True
    return target_family.startswith("business_") and source_family.startswith("tech_")


def _career_similar_jobs(source, top_k, include_same_title=False):
    requested = max(1, top_k)
    rows = job_repository.all_jobs()
    word2vec_results = job_ml_service.word2vec_similar_jobs(source["id"], top_k=max(requested * 6, 30))
    vector_scores = {}
    fallback_reason = None
    if word2vec_results is None:
        fallback_reason = "word2vec_unavailable"
    else:
        hydrated_vectors = _hydrate_word2vec_rows(word2vec_results, rows=rows)
        if hydrated_vectors:
            vector_scores = {row["id"]: score for row, score in hydrated_vectors}
        else:
            fallback_reason = "word2vec_results_unmatched"

    model_source = "word2vec" if vector_scores else "rules"
    source_key = _normalized_role_key(source)
    candidates = []
    for row in rows:
        if row["id"] == source["id"]:
            continue
        same_title = _normalized_role_key(row) == source_key
        if same_title and not include_same_title:
            continue
        if not same_title and _is_promotion_level_role(row):
            continue
        if not same_title and _is_hard_negative_direction(source, row):
            continue
        relation_type = _relation_type_for(source, row)
        vector_score = vector_scores.get(row["id"])
        score = _career_similarity_score(source, row, relation_type, vector_score)
        candidates.append((row, score, vector_score, relation_type))

    best_by_role = {}
    for row, score, vector_score, relation_type in candidates:
        key = _normalized_role_key(row)
        current = best_by_role.get(key)
        if not current or score > current[1]:
            best_by_role[key] = (row, score, vector_score, relation_type)

    ranked = sorted(
        best_by_role.values(),
        key=lambda item: (
            1 if item[3] == "same_role_posting" else 0,
            item[1],
            _salary_midpoint(item[0].get("salary_range", "")),
        ),
        reverse=True,
    )
    return [
        _similar_job_payload(row, score, model_source, source=source, vector_score=vector_score)
        for row, score, vector_score, _ in ranked[:requested]
    ], model_source, fallback_reason


@job_bp.route("/<job_name>/full-path", methods=["GET"])
def get_full_career_path(job_name):
    normalized = job_repository.normalize_job_name(job_name)
    student = _load_student_profile(request.args.get("student_id", type=int))
    vertical_path, vertical_source = _career_path(normalized)
    lateral_paths, lateral_source = _lateral_paths(normalized, student=student)
    if student:
        source = job_repository.get_job_by_name(normalized)
        vertical_path = _personalize_vertical_path(source, vertical_path, student, vertical_source)
    model_source = "word2vec" if "word2vec" in {vertical_source, lateral_source} else "rules"
    return jsonify({
        "success": True,
        "job_name": normalized,
        "student_id": student["id"] if student else None,
        "vertical_path": vertical_path,
        "lateral_paths": lateral_paths,
        "model_source": model_source,
    })


@job_bp.route("/<job_name>/vertical", methods=["GET"])
def get_vertical_path_simple(job_name):
    student = _load_student_profile(request.args.get("student_id", type=int))
    path, _ = _career_path(job_name)
    if student:
        source = job_repository.get_job_by_name(job_repository.normalize_job_name(job_name))
        path = _personalize_vertical_path(source, path, student, "rules")
    return jsonify(path)


@job_bp.route("/<job_name>/lateral", methods=["GET"])
def get_lateral_path_simple(job_name):
    student = _load_student_profile(request.args.get("student_id", type=int))
    paths, _ = _lateral_paths(job_name, student=student)
    return jsonify([
        item if student else {"to_job": item["job_name"], "description": item["description"]}
        for item in paths
    ])


@job_bp.route("/names", methods=["GET"])
def get_all_job_names():
    return jsonify(job_repository.list_job_names())


@job_bp.route("/<int:job_id>/similar", methods=["GET"])
def get_similar_jobs(job_id):
    top_k = request.args.get("top_k", 10, type=int)
    include_same_title = request.args.get("include_same_title", "false").lower() == "true"
    source = job_repository.get_job_by_rowid(job_id)
    if not source:
        return jsonify({"success": False, "error": "岗位不存在"}), 404

    data, model_source, fallback_reason = _career_similar_jobs(
        source,
        max(1, top_k),
        include_same_title=include_same_title,
    )
    payload = {
        "success": True,
        "model_source": model_source,
        "include_same_title": include_same_title,
        "data": data,
    }
    if fallback_reason:
        payload["fallback_reason"] = fallback_reason
    return jsonify(payload)


@job_bp.route("/skills", methods=["POST"])
def predict_job_skills():
    data = request.get_json(silent=True) or {}
    text = data.get("job_description", "")
    if not text:
        return jsonify({"success": False, "error": "请提供 job_description"}), 400
    top_k = data.get("top_k", 5)
    predictions, model_source = job_ml_service.predict_skills_with_textcnn(text, top_k=top_k)
    if predictions:
        return jsonify({
            "success": True,
            "model_source": model_source,
            "data": predictions,
        })
    skills = build_ml_job_profile({"job_title": "", "job_description": text}).get("skills", [])
    return jsonify({
        "success": True,
        "model_source": "rules",
        "data": [
            {"skill": skill, "probability": round(1.0 - index * 0.05, 4)}
            for index, skill in enumerate(skills[:top_k])
        ],
    })
