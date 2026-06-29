import csv
import importlib
import json
import os
import pickle
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


class StarwayRebuildTests(unittest.TestCase):
    def test_tianchi_import_creates_core_tables_and_legacy_job_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            os.environ["SQLITE_DB_PATH"] = str(tmp_path / "career.db")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)

            data_dir = tmp_path / "data"
            data_dir.mkdir()
            write_csv(data_dir / "jobs.csv", [{
                "job_id": "JOB001",
                "job_title": "Python开发工程师",
                "job_category": "技术",
                "company_name": "星途科技",
                "company_size": "20-99人",
                "company_type": "民营",
                "city": "杭州",
                "education": "本科",
                "experience": "1-3年",
                "salary_min": "10000",
                "salary_max": "18000",
                "salary_avg": "14000",
                "skills": "Python,Flask,SQL",
                "job_description": "负责后端服务开发和接口设计",
                "requirements": "熟悉 Python 和 Flask",
                "publish_date": "2026-06-01",
                "views": "10",
                "applications": "2",
            }])
            write_csv(data_dir / "candidates.csv", [{
                "candidate_id": "CAND001",
                "name": "林同学",
                "age": "22",
                "gender": "女",
                "education": "本科",
                "experience": "应届",
                "current_city": "杭州",
                "preferred_cities": "杭州,上海",
                "preferred_categories": "技术",
                "skills": "Python,SQL",
                "expected_salary_min": "9000",
                "expected_salary_max": "15000",
                "expected_salary_avg": "12000",
                "self_introduction": "计算机专业，熟悉 Python",
                "registration_date": "2026-05-01",
            }])
            write_csv(data_dir / "applications.csv", [{
                "application_id": "APP001",
                "job_id": "JOB001",
                "candidate_id": "CAND001",
                "application_date": "2026-06-10",
                "skill_match_score": "0.66",
                "salary_match_score": "1.0",
                "education_match_score": "1.0",
                "experience_match_score": "0.8",
                "total_match_score": "0.82",
                "is_matched": "1",
                "status": "面试中",
            }])

            from services.data_importer import import_tianchi_dataset

            summary = import_tianchi_dataset(str(data_dir), reset=True)
            summary = import_tianchi_dataset(str(data_dir), reset=True)

            conn = db.get_db()
            cur = conn.cursor()
            self.assertEqual(summary, {"jobs": 1, "candidates": 1, "applications": 1})
            self.assertEqual(cur.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)
            self.assertEqual(cur.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 1)
            self.assertEqual(cur.execute("SELECT COUNT(*) FROM applications").fetchone()[0], 1)

            legacy = cur.execute(
                "SELECT id, job_name, company, salary_range, location, job_description FROM job"
            ).fetchone()
            conn.close()
            self.assertEqual(dict(legacy), {
                "id": 1,
                "job_name": "Python开发工程师",
                "company": "星途科技",
                "salary_range": "10000-18000",
                "location": "杭州",
                "job_description": "负责后端服务开发和接口设计\n熟悉 Python 和 Flask",
            })

    def test_llm_client_selects_deepseek_and_zhipu_without_aliyun(self):
        import services.llm_client as llm_client

        calls = []

        def fake_post(url, headers=None, json=None, timeout=None, stream=False):
            calls.append({"url": url, "headers": headers, "json": json, "stream": stream})

            class Resp:
                status_code = 200

                def raise_for_status(self):
                    return None

                def json(self):
                    return {"choices": [{"message": {"content": "ok"}}]}

            return Resp()

        with mock.patch.object(llm_client.requests, "post", fake_post):
            os.environ["DEEPSEEK_API_KEY"] = "deepseek-key"
            os.environ["ZHIPU_API_KEY"] = "zhipu-key"
            deepseek = llm_client.LLMClient(provider="deepseek")
            zhipu = llm_client.LLMClient(provider="zhipu")

            self.assertEqual(deepseek.chat([{"role": "user", "content": "hi"}]), "ok")
            self.assertEqual(zhipu.chat([{"role": "user", "content": "hi"}]), "ok")

        self.assertIn("deepseek", calls[0]["url"].lower())
        self.assertIn("bigmodel", calls[1]["url"].lower())
        self.assertTrue(all("dashscope" not in call["url"].lower() for call in calls))

    def test_llm_auto_prefers_zhipu_to_save_deepseek_quota(self):
        import services.llm_client as llm_client

        os.environ["DEEPSEEK_API_KEY"] = "deepseek-key"
        os.environ["ZHIPU_API_KEY"] = "zhipu-key"
        os.environ["LLM_PROVIDER"] = "auto"

        self.assertEqual(llm_client.normalize_provider(), "zhipu")

    def test_ml_profile_and_recommendation_are_offline_and_explainable(self):
        from services.ml_recommender import build_job_profile, recommend_jobs_for_candidate

        job = {
            "job_id": "JOB001",
            "job_title": "Python开发工程师",
            "job_category": "技术",
            "skills": "Python,Flask,SQL",
            "job_description": "负责 Flask API 开发，优化 SQL 查询",
            "requirements": "熟悉 Python、Flask、SQL，有良好沟通能力",
            "salary_min": 10000,
            "salary_max": 18000,
        }
        candidate = {
            "candidate_id": "CAND001",
            "skills": "Python,SQL",
            "preferred_categories": "技术",
            "expected_salary_min": 9000,
            "expected_salary_max": 15000,
            "education": "本科",
        }

        profile = build_job_profile(job)
        recommendations = recommend_jobs_for_candidate(candidate, [job], top_k=1)

        self.assertEqual(profile["source"], "ml_rules")
        self.assertEqual(profile["skills"][:3], ["Python", "Flask", "SQL"])
        self.assertEqual(recommendations[0]["job_id"], "JOB001")
        self.assertGreater(recommendations[0]["score"], 0.5)
        self.assertIn("skill_overlap", recommendations[0]["explain"])

    def test_assistant_chat_endpoint_uses_stable_contract(self):
        os.environ["LLM_PROVIDER"] = "local"

        from backend.app import app

        with app.test_client() as client:
            resp = client.post("/api/assistant/chat", json={
                "message": "我想找 Python 后端岗位，应该补哪些技能？",
                "context": {"skills": ["Python", "SQL"]},
            })

        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["provider"], "local")
        self.assertTrue(data["answer"])
        self.assertTrue(data["usage"]["fallback"])

    def test_core_routes_no_longer_import_removed_llm_service(self):
        route_files = [
            BACKEND_DIR / "routes" / "assessment.py",
            BACKEND_DIR / "routes" / "job.py",
            BACKEND_DIR / "routes" / "match.py",
            BACKEND_DIR / "routes" / "profile.py",
            BACKEND_DIR / "routes" / "report.py",
            BACKEND_DIR / "routes" / "admin.py",
            BACKEND_DIR / "routes" / "llm.py",
        ]
        for path in route_files:
            source = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("from services.llm_service import", source, str(path))
            self.assertNotIn("from services import llm_service", source, str(path))
        self.assertFalse((BACKEND_DIR / "services" / "llm_service.py").exists())

    def test_auth_module_only_owns_authentication_routes(self):
        auth_source = (BACKEND_DIR / "routes" / "auth.py").read_text(encoding="utf-8", errors="ignore")
        user_source = (BACKEND_DIR / "routes" / "user.py").read_text(encoding="utf-8", errors="ignore")

        self.assertIn("auth_bp = Blueprint", auth_source)
        self.assertIn("user_bp = Blueprint", user_source)
        self.assertNotIn("@auth_bp.route('/user", auth_source)
        self.assertNotIn('@auth_bp.route("/user', auth_source)
        self.assertTrue("@user_bp.route('/user/profile'" in user_source or '@user_bp.route("/user/profile"' in user_source)
        self.assertTrue("@user_bp.route('/user/history'" in user_source or '@user_bp.route("/user/history"' in user_source)

    def test_runtime_backend_files_do_not_contain_mojibake_markers(self):
        checked_files = [
            BACKEND_DIR / "app.py",
            BACKEND_DIR / "routes" / "__init__.py",
            BACKEND_DIR / "routes" / "admin.py",
            BACKEND_DIR / "routes" / "assessment.py",
            BACKEND_DIR / "routes" / "assistant.py",
            BACKEND_DIR / "routes" / "auth.py",
            BACKEND_DIR / "routes" / "content.py",
            BACKEND_DIR / "routes" / "job.py",
            BACKEND_DIR / "routes" / "llm.py",
            BACKEND_DIR / "routes" / "match.py",
            BACKEND_DIR / "routes" / "profile.py",
            BACKEND_DIR / "routes" / "report.py",
            BACKEND_DIR / "routes" / "user.py",
            BACKEND_DIR / "services" / "career_ai_service.py",
            BACKEND_DIR / "services" / "llm_client.py",
            BACKEND_DIR / "services" / "ml_recommender.py",
        ]
        markers = ["鐢", "宀", "璇", "鎶", "鑱", "娴", "鍥", "楠", "绠", "搴"]
        for path in checked_files:
            source = path.read_text(encoding="utf-8", errors="ignore")
            for marker in markers:
                self.assertNotIn(marker, source, f"{marker} remains in {path}")

    def test_runtime_code_does_not_reintroduce_removed_legacy_concepts(self):
        checked_dirs = [BACKEND_DIR / "routes", BACKEND_DIR / "services"]
        forbidden = [
            "cluster-categories",
            "generate-all-category-profiles",
            "assign_jobs_to_categories",
            "build_category_profiles",
            "services.llm_service",
            "from services import llm_service",
            "category_id",
            "DashScope",
            "ALIYUN_API_KEY",
        ]
        for base in checked_dirs:
            for path in base.rglob("*.py"):
                source = path.read_text(encoding="utf-8", errors="ignore")
                for word in forbidden:
                    self.assertNotIn(word, source, f"{word} remains in {path}")

    def test_aliyun_dashscope_removed_from_runtime_requirements(self):
        checked_files = [
            BACKEND_DIR / "requirements.txt",
            BACKEND_DIR / "services" / "llm_client.py",
            BACKEND_DIR / "services" / "career_ai_service.py",
        ]
        forbidden = ["dashscope", "ALIYUN_API_KEY", "DashScope"]
        for path in checked_files:
            source = path.read_text(encoding="utf-8", errors="ignore")
            for word in forbidden:
                self.assertNotIn(word, source, f"{word} remains in {path}")

    def test_db_cleanup_protects_core_tables(self):
        from services.db_cleanup import CORE_TABLES, DROP_TABLES, LEGACY_UNUSED_TABLES, PURGE_DATA_TABLES

        self.assertIn("jobs", CORE_TABLES)
        self.assertIn("candidates", CORE_TABLES)
        self.assertIn("applications", CORE_TABLES)
        self.assertNotIn("verification_codes", CORE_TABLES)
        self.assertNotIn("job_categories", CORE_TABLES)
        self.assertIn("job_categories", DROP_TABLES)
        self.assertIn("verification_codes", DROP_TABLES)
        self.assertIn("job_legacy_with_category", DROP_TABLES)
        self.assertIn("assessment_results", PURGE_DATA_TABLES)
        self.assertIn("match_history", PURGE_DATA_TABLES)
        self.assertIn("report_history", PURGE_DATA_TABLES)
        self.assertIn("job_profile", PURGE_DATA_TABLES)
        self.assertTrue(CORE_TABLES.isdisjoint(LEGACY_UNUSED_TABLES))
        self.assertIn("user_plans", LEGACY_UNUSED_TABLES)

    def test_cleanup_purges_runtime_data_and_drops_job_categories_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            conn = db.get_db()
            cur = conn.cursor()
            cur.execute("CREATE TABLE assessment_results (id INTEGER PRIMARY KEY, value TEXT)")
            cur.execute("CREATE TABLE match_history (id INTEGER PRIMARY KEY, value TEXT)")
            cur.execute("CREATE TABLE report_history (id INTEGER PRIMARY KEY, value TEXT)")
            cur.execute("CREATE TABLE job_profile (id INTEGER PRIMARY KEY, job_name TEXT)")
            cur.execute("CREATE TABLE job_relations (id INTEGER PRIMARY KEY, from_job TEXT)")
            cur.execute("CREATE TABLE job_categories (id INTEGER PRIMARY KEY, name TEXT)")
            for table in ["assessment_results", "match_history", "report_history", "job_profile", "job_relations", "job_categories"]:
                cur.execute(f"INSERT INTO {table} DEFAULT VALUES")
            conn.commit()
            conn.close()

            import services.db_cleanup as db_cleanup
            importlib.reload(db_cleanup)
            result = db_cleanup.cleanup_unused_tables(apply=True, purge_data=True)

            conn = db.get_db()
            try:
                tables = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }
                self.assertNotIn("job_categories", tables)
                for table in ["assessment_results", "match_history", "report_history", "job_profile", "job_relations"]:
                    self.assertIn(table, tables)
                    self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
            finally:
                conn.close()

        self.assertIn("job_categories", result["dropped"])
        self.assertIn("assessment_results", result["purged"])

    def test_job_categories_endpoint_reads_tianchi_job_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")
            os.environ["LLM_PROVIDER"] = "local"

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            from services.data_importer import ensure_core_tables

            conn = db.get_db()
            ensure_core_tables(conn)
            conn.execute(
                """
                INSERT INTO jobs
                (job_id, job_title, job_category, company_name, city, skills, job_description, requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("JOB-CAT-1", "Python Engineer", "技术", "Starway", "杭州", "Python,SQL", "Backend", "Flask"),
            )
            conn.execute(
                """
                INSERT INTO jobs
                (job_id, job_title, job_category, company_name, city, skills, job_description, requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("JOB-CAT-2", "Product Manager", "产品", "Starway", "上海", "Axure", "Product", "Research"),
            )
            conn.commit()
            conn.close()

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get("/api/jobs/categories")

        self.assertEqual(resp.status_code, 200)
        names = {item["name"] for item in resp.get_json()}
        self.assertEqual(names, {"技术", "产品"})

    def test_admin_routes_do_not_expose_legacy_ai_category_workflows(self):
        admin_source = (BACKEND_DIR / "routes" / "admin.py").read_text(encoding="utf-8", errors="ignore")
        service_source = (BACKEND_DIR / "services" / "career_ai_service.py").read_text(encoding="utf-8", errors="ignore")

        forbidden = [
            "cluster-categories",
            "generate-all-category-profiles",
            "assign_jobs_to_categories",
            "build_category_profiles",
            "AI 自动聚类",
            "AI 生成所有大类画像",
        ]
        for word in forbidden:
            self.assertNotIn(word, admin_source)
            self.assertNotIn(word, service_source)

    def test_admin_category_summary_returns_tianchi_category_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")
            os.environ["LLM_PROVIDER"] = "local"

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()

            conn = db.get_db()
            try:
                conn.execute(
                    "INSERT INTO users (id, username, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
                    (930001, "admin_category_user", "unused", "admin"),
                )
                conn.execute(
                    """
                    INSERT INTO jobs (job_id, job_title, job_category, company_name, city, skills)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("ADMIN-CAT-1", "Backend Engineer", "技术", "Starway", "杭州", "Python"),
                )
                conn.execute(
                    """
                    INSERT INTO jobs (job_id, job_title, job_category, company_name, city, skills)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("ADMIN-CAT-2", "Data Analyst", "技术", "Starway", "杭州", "SQL"),
                )
                conn.commit()
            finally:
                conn.close()

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get(
                    "/api/admin/category-summary",
                    headers={"Authorization": "Bearer mock-token-930001"},
                )

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertEqual(data["source"], "jobs.job_category")
        self.assertEqual(data["total_categories"], 1)
        self.assertEqual(data["categories"][0]["name"], "技术")
        self.assertEqual(data["categories"][0]["job_count"], 2)

    def test_job_profile_generates_from_tianchi_fields_without_category_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")
            os.environ["LLM_PROVIDER"] = "local"

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()
            from services.data_importer import import_tianchi_dataset

            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            write_csv(data_dir / "jobs.csv", [{
                "job_id": "JOB-PROFILE-1",
                "job_title": "Python Backend Engineer",
                "job_category": "技术",
                "company_name": "Starway",
                "company_size": "20-99人",
                "company_type": "民营",
                "city": "杭州",
                "education": "本科",
                "experience": "1-3年",
                "salary_min": "10000",
                "salary_max": "18000",
                "salary_avg": "14000",
                "skills": "Python,Flask,SQL",
                "job_description": "Build Flask APIs and optimize SQL queries",
                "requirements": "Python Flask SQL communication",
                "publish_date": "2026-06-01",
                "views": "1",
                "applications": "0",
            }])
            write_csv(data_dir / "candidates.csv", [{
                "candidate_id": "CAND-PROFILE-1",
                "name": "Candidate",
                "age": "22",
                "gender": "女",
                "education": "本科",
                "experience": "应届",
                "current_city": "杭州",
                "preferred_cities": "杭州",
                "preferred_categories": "技术",
                "skills": "Python,SQL",
                "expected_salary_min": "9000",
                "expected_salary_max": "15000",
                "expected_salary_avg": "12000",
                "self_introduction": "Python candidate",
                "registration_date": "2026-06-01",
            }])
            write_csv(data_dir / "applications.csv", [{
                "application_id": "APP-PROFILE-1",
                "job_id": "JOB-PROFILE-1",
                "candidate_id": "CAND-PROFILE-1",
                "application_date": "2026-06-01",
                "skill_match_score": "1",
                "salary_match_score": "1",
                "education_match_score": "1",
                "experience_match_score": "1",
                "total_match_score": "1",
                "is_matched": "1",
                "status": "已录用",
            }])
            import_tianchi_dataset(str(data_dir), reset=True)
            conn = db.get_db()
            try:
                conn.execute("DELETE FROM job_profile")
                conn.execute("DROP TABLE IF EXISTS job_categories")
                conn.commit()
            finally:
                conn.close()

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get("/api/jobs/1/profile")

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertEqual(data["category"], "技术")
        self.assertEqual(data["source"], "ml_rules")
        self.assertIn("Python", data["skills"])

    def test_job_paths_are_planning_oriented_without_hardcoded_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")
            os.environ["LLM_PROVIDER"] = "local"

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()

            conn = db.get_db()
            try:
                conn.execute(
                    """
                    INSERT INTO job
                    (id, job_name, company, industry, salary_range, job_description, company_size, job_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (940001, "Python Backend Engineer", "Starway", "技术", "10000-18000", "Python Flask SQL", "20-99人", "PATH-1"),
                )
                conn.execute(
                    """
                    INSERT INTO job
                    (id, job_name, company, industry, salary_range, job_description, company_size, job_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (940002, "Backend Architect", "Starway", "技术", "22000-35000", "Python SQL architecture distributed systems", "20-99人", "PATH-2"),
                )
                conn.execute(
                    """
                    INSERT INTO job
                    (id, job_name, company, industry, salary_range, job_description, company_size, job_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (940003, "Product Analyst", "Starway", "产品", "12000-20000", "SQL product analytics", "20-99人", "PATH-3"),
                )
                conn.commit()
            finally:
                conn.close()

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get("/api/jobs/Python Backend Engineer/full-path")

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        vertical_text = json.dumps(data["vertical_path"], ensure_ascii=False)
        lateral_text = json.dumps(data["lateral_paths"], ensure_ascii=False)
        self.assertNotIn("高级Python Backend Engineer", vertical_text)
        self.assertNotIn("Python Backend Engineer专家", vertical_text)
        self.assertIn("Backend Architect", vertical_text)
        self.assertIn("Product Analyst", lateral_text)

    def test_similar_jobs_use_calculated_similarity_not_constant_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")
            os.environ["LLM_PROVIDER"] = "local"

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()

            conn = db.get_db()
            try:
                rows = [
                    (950001, "Python Backend Engineer", "技术", "Python Flask SQL API"),
                    (950002, "Flask API Engineer", "技术", "Python Flask API Redis"),
                    (950003, "Frontend Developer", "技术", "Vue React CSS"),
                ]
                for row in rows:
                    conn.execute(
                        "INSERT INTO job (id, job_name, industry, job_description) VALUES (?, ?, ?, ?)",
                        row,
                    )
                conn.commit()
            finally:
                conn.close()

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get("/api/jobs/950001/similar?top_k=2")

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 2)
        scores = [item["similarity"] for item in data]
        self.assertNotEqual(scores, [0.8, 0.8])
        self.assertGreater(scores[0], scores[1])

    def test_similar_jobs_prefers_word2vec_vectors_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            os.environ["SQLITE_DB_PATH"] = str(tmp_path / "career.db")
            os.environ["LLM_PROVIDER"] = "local"
            os.environ["WORD2VEC_JOB_VECTOR_PATH"] = str(tmp_path / "job_vectors_word2vec.pkl")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()

            conn = db.get_db()
            try:
                rows = [
                    (960001, "Python Backend Engineer", "技术", "10000-18000", "Python Flask SQL API"),
                    (960002, "Flask Platform Engineer", "技术", "16000-26000", "Python Flask service platform"),
                    (960003, "Visual Designer", "设计", "9000-14000", "Figma visual branding"),
                ]
                for row in rows:
                    conn.execute(
                        """
                        INSERT INTO job (id, job_name, industry, salary_range, job_description)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        row,
                    )
                conn.commit()
            finally:
                conn.close()

            with open(os.environ["WORD2VEC_JOB_VECTOR_PATH"], "wb") as f:
                pickle.dump({
                    "job_ids": [960001, 960002, 960003],
                    "vectors": [
                        [1.0, 0.0, 0.0],
                        [0.95, 0.05, 0.0],
                        [0.0, 1.0, 0.0],
                    ],
                    "raw_names": ["Python Backend Engineer", "Flask Platform Engineer", "Visual Designer"],
                }, f)

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get("/api/jobs/960001/similar?top_k=2")

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertEqual(data["model_source"], "word2vec")
        self.assertEqual(data["data"][0]["job_id"], 960002)
        self.assertGreater(data["data"][0]["similarity"], data["data"][1]["similarity"])

    def test_full_path_uses_word2vec_vectors_for_path_ranking(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            os.environ["SQLITE_DB_PATH"] = str(tmp_path / "career.db")
            os.environ["LLM_PROVIDER"] = "local"
            os.environ["WORD2VEC_JOB_VECTOR_PATH"] = str(tmp_path / "job_vectors_word2vec.pkl")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()

            conn = db.get_db()
            try:
                rows = [
                    (970001, "Data Analyst", "数据", "9000-15000", "SQL Python dashboard analytics"),
                    (970002, "Analytics Engineer", "数据", "18000-28000", "SQL Python data modeling"),
                    (970003, "Product Operations", "运营", "10000-18000", "SQL dashboard user growth"),
                ]
                for row in rows:
                    conn.execute(
                        """
                        INSERT INTO job (id, job_name, industry, salary_range, job_description)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        row,
                    )
                conn.commit()
            finally:
                conn.close()

            with open(os.environ["WORD2VEC_JOB_VECTOR_PATH"], "wb") as f:
                pickle.dump({
                    "job_ids": [970001, 970002, 970003],
                    "vectors": [
                        [1.0, 0.0, 0.0],
                        [0.91, 0.03, 0.0],
                        [0.88, 0.1, 0.0],
                    ],
                    "raw_names": ["Data Analyst", "Analytics Engineer", "Product Operations"],
                }, f)

            import backend.app as app_module
            importlib.reload(app_module)
            with app_module.app.test_client() as client:
                resp = client.get("/api/jobs/Data Analyst/full-path")

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertEqual(data["model_source"], "word2vec")
        self.assertIn("Analytics Engineer", json.dumps(data["vertical_path"], ensure_ascii=False))
        self.assertIn("Product Operations", json.dumps(data["lateral_paths"], ensure_ascii=False))

    def test_job_skills_uses_textcnn_predictor_when_available(self):
        os.environ["LLM_PROVIDER"] = "local"

        import config
        import db

        importlib.reload(config)
        importlib.reload(db)

        import backend.app as app_module
        importlib.reload(app_module)
        import services.job_ml_service as job_ml_service

        with mock.patch.object(job_ml_service, "predict_skills_with_textcnn") as predictor:
            predictor.return_value = (
                [
                    {"skill": "python", "probability": 0.93},
                    {"skill": "flask", "probability": 0.88},
                ],
                "textcnn",
            )
            with app_module.app.test_client() as client:
                resp = client.post("/api/jobs/skills", json={
                    "job_description": "Python Flask backend API",
                    "top_k": 2,
                })

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertEqual(data["model_source"], "textcnn")
        self.assertEqual(data["data"][0]["skill"], "python")

    def test_init_db_does_not_recreate_unused_legacy_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)
            db.init_db()

            conn = db.get_db()
            try:
                tables = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }
            finally:
                conn.close()

        self.assertNotIn("verification_codes", tables)
        self.assertFalse(tables & {
            "verification_codes",
            "job_legacy_with_category",
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
        })

    def test_register_uses_captcha_without_sms_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")
            os.environ["LLM_PROVIDER"] = "local"

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)

            import backend.app as app_module
            importlib.reload(app_module)

            with app_module.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess["captcha"] = "ABCD"
                resp = client.post("/api/register", json={
                    "username": "captcha_only_user",
                    "phone": "13900001234",
                    "password": "pass123",
                    "captcha": "ABCD",
                })

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()
        self.assertEqual(data["username"], "captcha_only_user")

    def test_send_code_is_disabled_when_sms_auth_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)

            import backend.app as app_module
            importlib.reload(app_module)

            with app_module.app.test_client() as client:
                resp = client.post("/api/send_code", json={"phone": "13900001234"})

        self.assertEqual(resp.status_code, 410)
        self.assertEqual(resp.get_json()["error"], "sms verification is disabled")

    def test_bind_phone_does_not_require_sms_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)

            import backend.app as app_module
            importlib.reload(app_module)

            conn = db.get_db()
            try:
                conn.execute(
                    "INSERT INTO users (id, username, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
                    (910001, "bind_phone_user", "unused", "user"),
                )
                conn.commit()
            finally:
                conn.close()

            with app_module.app.test_client() as client:
                resp = client.post(
                    "/api/user/bind-phone",
                    headers={"Authorization": "Bearer mock-token-910001"},
                    json={"phone": "13900009998"},
                )

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        self.assertEqual(resp.get_json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
