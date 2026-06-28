import os
import sys
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("LLM_PROVIDER", "local")

from backend.app import app
from backend.db import get_db


class AssessmentEndpointTests(unittest.TestCase):
    def tearDown(self):
        conn = get_db()
        try:
            conn.execute("DELETE FROM assessment_results WHERE session_id = ?", ("unit-test",))
            conn.commit()
        finally:
            conn.close()

    def test_questions_and_submit_work_in_local_mode(self):
        with app.test_client() as client:
            questions_resp = client.get("/api/assessment/questions")
            self.assertEqual(questions_resp.status_code, 200)
            questions = questions_resp.get_json()
            self.assertIsInstance(questions, list)

            answers = [
                {"question_id": q["id"], "score": 4}
                for q in questions[:3]
            ] or [{"question_id": 1, "score": 4}]
            submit_resp = client.post("/api/assessment/submit", json={
                "answers": answers,
                "user_id": 1,
                "session_id": "unit-test",
                "test_mode": True,
            })

        self.assertEqual(submit_resp.status_code, 200)
        data = submit_resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("result_id", data)


if __name__ == "__main__":
    unittest.main()
