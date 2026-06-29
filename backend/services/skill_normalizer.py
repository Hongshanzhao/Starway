import re
from typing import Dict, Iterable, List, Sequence, Set, Tuple


SKILL_ALIASES = {
    "java": ["java", "jvm"],
    "python": ["python"],
    "go": ["golang", " go "],
    "spring": ["spring", "springboot", "spring boot"],
    "spring_boot": ["spring boot", "springboot"],
    "api": ["api", "restful", "rest api", "interface development"],
    "sql": ["sql"],
    "mysql": ["mysql", "my sql"],
    "redis": ["redis", "cache"],
    "linux": ["linux"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "microservice": ["microservice", "microservices", "微服务"],
    "distributed_system": ["distributed", "distributed system", "分布式", "高并发"],
    "testing": ["testing", "test development", "automation testing", "测试", "测试开发", "接口测试"],
    "automation_testing": ["automation testing", "automated testing", "自动化测试"],
    "spark": ["spark"],
    "flink": ["flink"],
    "data_analysis": ["data analysis", "analytics", "dashboard", "数据分析", "数据建模", "数据平台"],
    "vue": ["vue"],
    "react": ["react"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "devops": ["devops", "sre"],
    "excel": ["excel"],
    "machine_learning": ["machine learning", "ml", "机器学习", "深度学习", "算法", "tensorflow", "pytorch"],
}


DISPLAY_NAMES = {
    "java": "Java",
    "python": "Python",
    "go": "Go",
    "spring": "Spring",
    "spring_boot": "Spring Boot",
    "api": "API",
    "sql": "SQL",
    "mysql": "MySQL",
    "redis": "Redis",
    "linux": "Linux",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "microservice": "Microservice",
    "distributed_system": "Distributed System",
    "testing": "Testing",
    "automation_testing": "Automation Testing",
    "spark": "Spark",
    "flink": "Flink",
    "data_analysis": "Data Analysis",
    "vue": "Vue",
    "react": "React",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "devops": "DevOps",
    "excel": "Excel",
    "machine_learning": "Machine Learning",
}


def _clean_text(text: str) -> str:
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text or "")
    text = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff+#.]+", " ", text)
    return f" {text.lower()} "


COMPILED_SKILL_ALIASES = {
    concept: [
        (alias, _clean_text(alias).strip(), bool(re.search(r"[a-zA-Z0-9]", _clean_text(alias).strip())))
        for alias in aliases
        if _clean_text(alias).strip()
    ]
    for concept, aliases in SKILL_ALIASES.items()
}


def split_skill_items(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = [str(item) for item in value]
    else:
        raw = re.split(r"[,，、;\n\r\t/|]+", str(value))
    result = []
    seen = set()
    for item in raw:
        skill = str(item).strip()
        if not skill:
            continue
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            result.append(skill)
    return result


def _contains_alias(cleaned_text: str, alias_cleaned: str, has_ascii: bool) -> bool:
    if not alias_cleaned:
        return False
    if has_ascii:
        return f" {alias_cleaned} " in cleaned_text
    return alias_cleaned in cleaned_text


def concepts_from_text(text: str) -> Set[str]:
    cleaned = _clean_text(text)
    concepts = set()
    for concept, aliases in COMPILED_SKILL_ALIASES.items():
        if any(_contains_alias(cleaned, alias_cleaned, has_ascii) for _, alias_cleaned, has_ascii in aliases):
            concepts.add(concept)
    if "spring_boot" in concepts:
        concepts.add("spring")
    if "mysql" in concepts:
        concepts.add("sql")
    if "api" in concepts:
        concepts.add("backend")
    return concepts


def concepts_from_skills(value, extra_text: str = "") -> Set[str]:
    text = " ".join(split_skill_items(value))
    if extra_text:
        text = f"{text} {extra_text}"
    concepts = concepts_from_text(text)
    for item in split_skill_items(value):
        cleaned = item.strip().lower()
        if cleaned and cleaned not in concepts:
            concepts.update(concepts_from_text(cleaned))
    return {concept for concept in concepts if concept != "backend"}


def display_for_concept(concept: str) -> str:
    return DISPLAY_NAMES.get(concept, concept.replace("_", " ").title())


def display_concepts(concepts: Iterable[str]) -> List[str]:
    return [display_for_concept(concept) for concept in sorted(set(concepts))]


def match_concepts(student_skills, required_skills, required_text: str = "") -> Tuple[Set[str], Set[str], Set[str]]:
    student_concepts = concepts_from_skills(student_skills)
    required_concepts = concepts_from_skills(required_skills, extra_text=required_text)
    matched = student_concepts & required_concepts
    missing = required_concepts - student_concepts
    return required_concepts, matched, missing
