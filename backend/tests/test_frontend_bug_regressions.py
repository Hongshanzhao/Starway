import io
import importlib
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class FrontendBugRegressionTests(unittest.TestCase):
    def test_login_accepts_code_generated_for_same_captcha_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmp) / "career.db")

            import config
            import db

            importlib.reload(config)
            importlib.reload(db)

            import backend.app as app_module
            importlib.reload(app_module)

            from werkzeug.security import generate_password_hash

            conn = db.get_db()
            try:
                conn.execute(
                    "INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                    ("captcha_real_user", generate_password_hash("pass123"), "user"),
                )
                conn.commit()
            finally:
                conn.close()

            captcha_id = "captcha-real-id"
            with app_module.app.test_client() as client:
                image_resp = client.get(f"/api/captcha?captcha_id={captcha_id}")
                self.assertEqual(image_resp.status_code, 200)
                self.assertEqual(image_resp.mimetype, "image/png")

                conn = db.get_db()
                try:
                    row = conn.execute(
                        "SELECT code FROM captcha_challenges WHERE id = ? AND used_at IS NULL",
                        (captcha_id,),
                    ).fetchone()
                finally:
                    conn.close()
                self.assertIsNotNone(row)

                login_resp = client.post("/api/login", json={
                    "username": "captcha_real_user",
                    "password": "pass123",
                    "captcha": row["code"].lower(),
                    "captcha_id": captcha_id,
                })

        self.assertEqual(login_resp.status_code, 200, login_resp.get_data(as_text=True))
        self.assertTrue(login_resp.get_json()["token"].startswith("mock-token-"))

    def test_assistant_stream_calls_llm_client_for_auto_provider(self):
        import backend.app as app_module
        import routes.assistant as assistant_route

        calls = []

        class FakeLLMClient:
            def __init__(self, provider=None, timeout=18):
                self.provider = "zhipu"
                self.used_fallback = False
                self.last_error = ""

            def chat_remote_only(self, messages, max_tokens=1200, **kwargs):
                calls.append({"messages": messages, "max_tokens": max_tokens})
                return "REMOTE API ANSWER for software engineering to data analysis. 30 60 90."

        with mock.patch.object(assistant_route, "LLMClient", FakeLLMClient):
            with mock.patch.object(assistant_route, "chunk_text", lambda text, size=40: [text]):
                with app_module.app.test_client() as client:
                    resp = client.post("/api/assistant/chat", json={
                        "message": "software engineering senior wants data analysis plan",
                        "provider": "auto",
                        "stream": True,
                        "context": {"skills": ["Python", "SQL"]},
                    }, buffered=True)
                    body = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200, body)
        self.assertTrue(calls)
        self.assertIn("REMOTE API ANSWER", body)
        self.assertIn('"provider": "zhipu"', body)
        self.assertIn('"fallback": false', body)
        self.assertNotIn('"provider": "instant"', body)

    def test_resume_upload_parse_failure_is_friendly(self):
        import backend.app as app_module
        import routes.profile as profile_route

        broken_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"
        with mock.patch.object(profile_route, "_read_pdf_with_pdfplumber", side_effect=IndexError("list index out of range")):
            with mock.patch.object(profile_route, "_read_pdf_with_pdfminer", side_effect=ValueError("list index out of range")):
                with app_module.app.test_client() as client:
                    resp = client.post(
                        "/api/profile/upload",
                        data={"file": (io.BytesIO(broken_pdf), "resume.pdf")},
                        content_type="multipart/form-data",
                    )

        body = resp.get_data(as_text=True)
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200, body)
        self.assertEqual(data["text"], "")
        self.assertTrue(data["parse_warning"])
        self.assertNotIn("list index out of range", body)

    def test_resume_upload_chinese_pdf_filename_never_500(self):
        import backend.app as app_module
        import routes.profile as profile_route

        broken_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"
        with mock.patch.object(profile_route, "_read_pdf_with_pdfplumber", side_effect=ValueError("empty pdf")):
            with mock.patch.object(profile_route, "_read_pdf_with_pdfminer", side_effect=ValueError("empty pdf")):
                with app_module.app.test_client() as client:
                    resp = client.post(
                        "/api/profile/upload",
                        data={"file": (io.BytesIO(broken_pdf), "陈圆圆_南华大学_测试工程师_软件工程_本科(简历).pdf")},
                        content_type="multipart/form-data",
                    )

        body = resp.get_data(as_text=True)
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200, body)
        self.assertIsInstance(data, dict)
        self.assertIn("parse_warning", data)
        self.assertNotIn("Internal Server Error", body)

    def test_resume_upload_pdf_text_layer_is_returned(self):
        import backend.app as app_module
        import routes.profile as profile_route

        resume_text = "陈圆圆\n南华大学 软件工程 本科\n技能：Python SQL 测试工程师"
        pdf_file = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"
        with mock.patch.object(profile_route, "_read_pdf_with_pypdfium2", return_value=resume_text):
            with app_module.app.test_client() as client:
                resp = client.post(
                    "/api/profile/upload",
                    data={"file": (io.BytesIO(pdf_file), "陈圆圆_简历.pdf")},
                    content_type="multipart/form-data",
                )

        body = resp.get_data(as_text=True)
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200, body)
        self.assertIn("陈圆圆", data["text"])
        self.assertEqual(data["parse_warning"], "")
        self.assertIn("Python", data["skills"])

    def test_resume_pdf_compatibility_chars_are_normalized_for_profile_fields(self):
        import backend.app as app_module
        import routes.profile as profile_route

        resume_text = "陈圆圆\n求职意向：测试⼯程师 | ⼤三\n南华⼤学 软件⼯程 本科\n技能：Python Java 单元测试"
        pdf_file = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"
        with mock.patch.object(profile_route, "_read_pdf_with_pypdfium2", return_value=resume_text):
            with app_module.app.test_client() as client:
                resp = client.post(
                    "/api/profile/upload",
                    data={"file": (io.BytesIO(pdf_file), "陈圆圆_简历.pdf")},
                    content_type="multipart/form-data",
                )

        data = resp.get_json()
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        self.assertIn("测试工程师", data["text"])
        self.assertIn("软件工程", data["text"])
        self.assertEqual(data["education_json"]["major"], "软件工程")
        self.assertEqual(data["education_json"]["grade"], "大三")
        self.assertIn("单元测试", data["skills"])


if __name__ == "__main__":
    unittest.main()
